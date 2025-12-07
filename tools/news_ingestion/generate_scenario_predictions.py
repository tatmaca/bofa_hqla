#!/usr/bin/env python3
"""
Scenario Prediction Generation
Generates yield curve predictions for baseline (news-based) and scenarios.
"""

import datetime as dt
from typing import Dict, Optional, List
from pathlib import Path

from train_linear_online import (
    predict_yield_changes,
    get_daily_factor_scores,
    initialize_coefficients,
    get_intercepts,
    compute_factor_attribution,
    TENORS
)


def generate_baseline_prediction(date: str) -> Dict:
    """
    Generate baseline prediction from day's news.
    
    Args:
        date: Date string (YYYY-MM-DD) - the day whose news is used
    
    Returns:
        Dictionary with predictions, factor_scores, and attribution
    """
    # Get coefficients and intercepts
    coefficients = initialize_coefficients(date)
    intercepts = get_intercepts(date)
    
    # Get factor scores from day's news
    factor_scores = get_daily_factor_scores(date)
    
    if not factor_scores:
        print(f"[WARN] No factor scores for {date} - baseline prediction may be inaccurate")
        factor_scores = {}
    
    # Generate predictions
    predictions = predict_yield_changes(date, coefficients, factor_scores, intercepts)
    
    # Compute attribution
    attribution = compute_factor_attribution(date, coefficients, factor_scores)
    
    return {
        "scenario_name": "baseline",
        "scenario_description": f"Prediction from {date}'s news",
        "predictions": predictions,
        "factor_scores": factor_scores,
        "attribution": {tenor: dict(factors) for tenor, factors in attribution.items()}
    }


def generate_scenario_prediction(date: str, 
                                 scenario: Dict,
                                 scenario_factors: Dict[str, float],
                                 combine_with_news: bool = False) -> Dict:
    """
    Generate prediction for a scenario.
    
    Args:
        date: Date string (YYYY-MM-DD) - used for coefficients/intercepts
        scenario: Scenario dictionary
        scenario_factors: Factor scores extracted from scenario
        combine_with_news: If True, add scenario factors to day's news factors.
                         If False, use only scenario factors (default)
    
    Returns:
        Dictionary with predictions, factor_scores, and attribution
    """
    scenario_name = scenario.get("Scenario", "Unknown Scenario")
    scenario_description = scenario.get("Description", "")
    
    # Get coefficients and intercepts (use same as baseline)
    coefficients = initialize_coefficients(date)
    intercepts = get_intercepts(date)
    
    # Determine factor scores to use
    if combine_with_news:
        # Add scenario factors to day's news factors
        base_factors = get_daily_factor_scores(date)
        factor_scores = base_factors.copy()
        
        # Add scenario factors (scenario factors take precedence if conflict)
        for factor, score in scenario_factors.items():
            if factor in factor_scores:
                # Combine: use maximum absolute value (scenario dominates)
                if abs(score) > abs(factor_scores[factor]):
                    factor_scores[factor] = score
            else:
                factor_scores[factor] = score
    else:
        # Use only scenario factors (treat scenario as major news event)
        factor_scores = scenario_factors.copy()
    
    if not factor_scores:
        print(f"[WARN] No factor scores for scenario '{scenario_name}'")
        # Return zero predictions
        predictions = {tenor: 0.0 for tenor in TENORS}
        attribution = {tenor: {} for tenor in TENORS}
    else:
        # Generate predictions using scenario factors
        predictions = predict_yield_changes(date, coefficients, factor_scores, intercepts)
        
        # Compute attribution
        attribution = compute_factor_attribution(date, coefficients, factor_scores)
    
    return {
        "scenario_name": scenario_name,
        "scenario_description": scenario_description,
        "predictions": predictions,
        "factor_scores": factor_scores,
        "attribution": {tenor: dict(factors) for tenor, factors in attribution.items()}
    }


def generate_all_scenario_curves(date: str, 
                                 scenarios_path: Optional[str] = None,
                                 combine_with_news: bool = False) -> Optional[Dict]:
    """
    Generate all 10 curves: 1 baseline + 9 scenarios.
    
    Args:
        date: Date string (YYYY-MM-DD) - the day whose news is used for baseline
        scenarios_path: Path to scenarios JSONL file (if None, uses default)
        combine_with_news: Whether to combine scenario factors with news factors
    
    Returns:
        Dictionary with all curves, or None if generation fails
    """
    from load_scenarios import load_scenarios_from_jsonl, get_default_scenarios_path
    from extract_scenario_factors import extract_factors_for_scenarios
    
    # Load scenarios
    if not scenarios_path:
        default_path = get_default_scenarios_path()
        if not default_path:
            print("[ERROR] No scenarios path provided and default not found")
            return None
        scenarios_path = str(default_path)
    
    try:
        scenarios = load_scenarios_from_jsonl(scenarios_path)
    except Exception as e:
        print(f"[ERROR] Failed to load scenarios: {e}")
        return None
    
    if len(scenarios) != 9:
        print(f"[WARN] Expected 9 scenarios, found {len(scenarios)}")
    
    # Extract factors for all scenarios
    print(f"[SCENARIO] Extracting factors for {len(scenarios)} scenarios...")
    scenario_factors_dict = extract_factors_for_scenarios(scenarios, use_cache=True)
    
    # Calculate prediction date (t+1)
    try:
        base_date = dt.datetime.strptime(date, "%Y-%m-%d").date()
        prediction_date = (base_date + dt.timedelta(days=1)).isoformat()
    except ValueError:
        print(f"[ERROR] Invalid date format: {date}")
        return None
    
    # Generate baseline prediction
    print(f"[SCENARIO] Generating baseline prediction from {date}'s news...")
    try:
        baseline = generate_baseline_prediction(date)
    except Exception as e:
        print(f"[ERROR] Failed to generate baseline prediction: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Generate scenario predictions
    curves = {
        "date": date,
        "base_date": date,
        "prediction_date": prediction_date,
        "baseline": baseline
    }
    
    for scenario in scenarios:
        scenario_name = scenario.get("Scenario", "Unknown")
        scenario_factors = scenario_factors_dict.get(scenario_name, {})
        
        print(f"[SCENARIO] Generating prediction for scenario: {scenario_name}")
        try:
            scenario_pred = generate_scenario_prediction(
                date, scenario, scenario_factors, combine_with_news=combine_with_news
            )
            curves[scenario_name] = scenario_pred
        except Exception as e:
            print(f"[WARN] Failed to generate prediction for scenario '{scenario_name}': {e}")
            # Include scenario with empty predictions
            curves[scenario_name] = {
                "scenario_name": scenario_name,
                "scenario_description": scenario.get("Description", ""),
                "predictions": {tenor: 0.0 for tenor in TENORS},
                "factor_scores": {},
                "attribution": {tenor: {} for tenor in TENORS},
                "error": str(e)
            }
    
    print(f"[SCENARIO] Generated {len(curves) - 3} scenario curves (1 baseline + {len(curves) - 4} scenarios)")
    return curves


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Generate scenario-based yield curve predictions")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--scenarios-path", type=str, help="Path to scenarios JSONL file")
    ap.add_argument("--output-path", type=str, help="Output JSON file path")
    ap.add_argument("--combine-with-news", action="store_true", 
                   help="Combine scenario factors with day's news factors")
    args = ap.parse_args()
    
    target_date = args.date if args.date else dt.date.today().isoformat()
    
    curves = generate_all_scenario_curves(
        target_date, 
        args.scenarios_path,
        combine_with_news=args.combine_with_news
    )
    
    if curves:
        if args.output_path:
            output_path = Path(args.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(output_path, 'w') as f:
                json.dump(curves, f, indent=2)
            print(f"[SAVE] Saved scenario curves to {output_path}")
        else:
            import json
            print("\n" + "="*80)
            print("SCENARIO CURVES OUTPUT")
            print("="*80)
            print(json.dumps(curves, indent=2))
    else:
        print("[ERROR] Failed to generate scenario curves")
        exit(1)

