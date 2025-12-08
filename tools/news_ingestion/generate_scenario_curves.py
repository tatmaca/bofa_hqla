#!/usr/bin/env python3
"""
Main Script: Generate Scenario-Based Yield Curve Predictions
Generates 10 yield curve predictions: 1 baseline from news + 9 scenario-based.
"""

import argparse
import json
import datetime as dt
from pathlib import Path
from typing import Optional

from generate_scenario_predictions import generate_all_scenario_curves
from load_scenarios import get_default_scenarios_path


def main():
    """Main entry point for scenario curve generation."""
    ap = argparse.ArgumentParser(
        description="Generate scenario-based yield curve predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for today
  python3 generate_scenario_curves.py

  # Generate for specific date
  python3 generate_scenario_curves.py --date 2025-12-01

  # Specify custom scenarios file
  python3 generate_scenario_curves.py --date 2025-12-01 --scenarios-path /path/to/scenarios.jsonl

  # Combine scenario factors with news factors
  python3 generate_scenario_curves.py --date 2025-12-01 --combine-with-news
        """
    )
    
    ap.add_argument(
        "--date",
        type=str,
        help="Date (YYYY-MM-DD) whose news is used for baseline prediction. Defaults to today."
    )
    
    ap.add_argument(
        "--scenarios-path",
        type=str,
        help="Path to scenarios JSONL file. If not provided, uses default location."
    )
    
    ap.add_argument(
        "--output-path",
        type=str,
        help="Output JSON file path. If not provided, saves to scenario_predictions/scenario_curves_{date}.json"
    )
    
    ap.add_argument(
        "--combine-with-news",
        action="store_true",
        help="Combine scenario factors with day's news factors (default: use only scenario factors)"
    )
    
    ap.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached scenario factors (re-extract from LLM)"
    )
    
    args = ap.parse_args()
    
    # Determine target date
    target_date = args.date if args.date else dt.date.today().isoformat()
    
    # Determine scenarios path
    scenarios_path = args.scenarios_path
    if not scenarios_path:
        default_path = get_default_scenarios_path()
        if default_path:
            scenarios_path = str(default_path)
        else:
            print("[ERROR] No scenarios path provided and default not found")
            print("[ERROR] Default location: backend/mad_debate/data/scenarios/out.jsonl")
            exit(1)
    
    # Check if scenarios file exists
    if not Path(scenarios_path).exists():
        print(f"[ERROR] Scenarios file not found: {scenarios_path}")
        exit(1)
    
    print("="*80)
    print(f"GENERATING SCENARIO-BASED YIELD CURVE PREDICTIONS")
    print("="*80)
    print(f"Date: {target_date}")
    print(f"Scenarios: {scenarios_path}")
    print(f"Combine with news: {args.combine_with_news}")
    print("="*80)
    print()
    
    # Generate all curves
    curves = generate_all_scenario_curves(
        target_date,
        scenarios_path,
        combine_with_news=args.combine_with_news
    )
    
    if not curves:
        print("[ERROR] Failed to generate scenario curves")
        exit(1)
    
    # Determine output path
    if args.output_path:
        output_path = Path(args.output_path)
    else:
        output_dir = Path(__file__).parent / "scenario_predictions"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"scenario_curves_{target_date}.json"
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(curves, f, indent=2)
    
    print()
    print("="*80)
    print("SUCCESS")
    print("="*80)
    print(f"Generated {len(curves) - 3} curves:")
    print(f"  - 1 baseline (from {target_date}'s news)")
    print(f"  - {len(curves) - 4} scenarios")
    print(f"Output saved to: {output_path}")
    print()
    
    # Print summary
    print("Summary:")
    print(f"  Baseline prediction date: {curves['base_date']}")
    print(f"  Prediction target date: {curves['prediction_date']}")
    print()
    
    # Show baseline predictions
    baseline = curves.get("baseline", {})
    baseline_preds = baseline.get("predictions", {})
    if baseline_preds:
        print("Baseline Predictions (from news):")
        from train_linear_online import TENORS
        for tenor in TENORS:
            if tenor in baseline_preds:
                print(f"  {tenor}: {baseline_preds[tenor]:+.2f} bps")
        print()
    
    # Show scenario predictions summary
    print("Scenario Predictions:")
    for key, value in curves.items():
        if key not in ["date", "base_date", "prediction_date", "baseline"]:
            scenario_name = value.get("scenario_name", key)
            preds = value.get("predictions", {})
            if preds:
                # Show average absolute change
                avg_change = sum(abs(p) for p in preds.values()) / len(preds) if preds else 0.0
                print(f"  {scenario_name}: avg |change| = {avg_change:.2f} bps")


if __name__ == "__main__":
    main()

