#!/usr/bin/env python3
"""
Model Comparison Utility
Compares linear online learning model vs XGBoost model predictions.
"""

import os
import sys
import json
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from train_linear_online import predict_yield_changes, initialize_coefficients, get_daily_factor_scores, get_intercepts

def get_linear_predictions(date: str) -> Optional[Dict[str, float]]:
    """Get linear model predictions for a date."""
    try:
        coefficients = initialize_coefficients(date)
        factor_scores = get_daily_factor_scores(date)
        intercepts = get_intercepts(date)
        
        if not factor_scores:
            return None
        
        predictions = predict_yield_changes(date, coefficients, factor_scores, intercepts)
        return predictions
    except Exception as e:
        print(f"[WARN] Failed to get linear predictions: {e}")
        return None

def get_xgboost_predictions(date: str) -> Optional[Dict[str, float]]:
    """Get XGBoost model predictions for a date (if available)."""
    # XGBoost predictions are stored in LLM analysis or can be computed from models
    # For now, return None if not available
    # This can be enhanced to load XGBoost models and make predictions
    return None

def get_actual_changes(date: str) -> Optional[Dict[str, float]]:
    """Get actual yield changes from database."""
    conn = get_conn()
    c = conn.cursor()
    
    row = c.execute("""
        SELECT delta_zeros_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (date,)).fetchone()
    
    conn.close()
    
    if not row:
        return None
    
    try:
        delta_zeros = json.loads(row["delta_zeros_pct"])
        # Convert to our format (handle both "3M" and "3m", "2y" and "2Y", etc.)
        actuals = {}
        for key, value in delta_zeros.items():
            key_upper = key.upper()
            if key_upper == "3M":
                actuals["3M"] = float(value) * 100  # Convert to bps
            elif key_upper in ["2Y", "5Y", "10Y", "30Y"]:
                actuals[key_upper] = float(value) * 100
            elif key_upper.replace("Y", "Y") in ["2Y", "5Y", "10Y", "30Y"]:
                actuals[key_upper.replace("Y", "Y")] = float(value) * 100
        
        return actuals
    except:
        return None

def compare_models_for_date(date: str) -> Dict:
    """Compare linear and XGBoost models for a single date."""
    linear_preds = get_linear_predictions(date)
    xgb_preds = get_xgboost_predictions(date)
    actuals = get_actual_changes(date)
    
    if not actuals:
        return None
    
    comparison = {
        "date": date,
        "actuals": actuals,
        "linear": {},
        "xgboost": {},
        "metrics": {}
    }
    
    if linear_preds:
        comparison["linear"] = linear_preds
        # Compute errors
        linear_errors = {}
        linear_mae = 0.0
        linear_count = 0
        for tenor in ["3M", "2Y", "5Y", "10Y", "30Y"]:
            if tenor in actuals and tenor in linear_preds:
                error = actuals[tenor] - linear_preds[tenor]
                linear_errors[tenor] = error
                linear_mae += abs(error)
                linear_count += 1
        comparison["linear"]["errors"] = linear_errors
        if linear_count > 0:
            comparison["metrics"]["linear_mae"] = linear_mae / linear_count
    
    if xgb_preds:
        comparison["xgboost"] = xgb_preds
    
    return comparison

def compare_models_date_range(start_date: str, end_date: str) -> List[Dict]:
    """Compare models across a date range."""
    comparisons = []
    
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    current = start
    while current <= end:
        if current.weekday() < 5:  # Business days only
            date_str = current.isoformat()
            comparison = compare_models_for_date(date_str)
            if comparison:
                comparisons.append(comparison)
        current += dt.timedelta(days=1)
    
    return comparisons

def print_comparison(comparison: Dict):
    """Print a formatted comparison."""
    print(f"\n{'='*70}")
    print(f"Model Comparison - {comparison['date']}")
    print(f"{'='*70}")
    
    print(f"\nActual Changes (bps):")
    for tenor in ["3M", "2Y", "5Y", "10Y", "30Y"]:
        if tenor in comparison["actuals"]:
            print(f"  {tenor}: {comparison['actuals'][tenor]:+.2f}")
    
    if comparison["linear"]:
        print(f"\nLinear Model Predictions (bps):")
        for tenor in ["3M", "2Y", "5Y", "10Y", "30Y"]:
            if tenor in comparison["linear"]:
                pred = comparison["linear"][tenor]
                actual = comparison["actuals"].get(tenor, 0.0)
                error = actual - pred
                print(f"  {tenor}: {pred:+.2f} (error: {error:+.2f})")
        
        if "metrics" in comparison and "linear_mae" in comparison["metrics"]:
            print(f"\nLinear Model MAE: {comparison['metrics']['linear_mae']:.2f} bps")
    
    if comparison["xgboost"]:
        print(f"\nXGBoost Predictions (bps):")
        for tenor in comparison["xgboost"]:
            print(f"  {tenor}: {comparison['xgboost'][tenor]:+.2f}")

def main():
    ap = argparse.ArgumentParser(description="Compare linear and XGBoost model predictions")
    ap.add_argument("--date", type=str, help="Single date (YYYY-MM-DD) to compare")
    ap.add_argument("--start-date", type=str, help="Start date for range comparison")
    ap.add_argument("--end-date", type=str, help="End date for range comparison")
    ap.add_argument("--output", type=str, help="Output JSON file for comparison results")
    args = ap.parse_args()
    
    if args.date:
        comparison = compare_models_for_date(args.date)
        if comparison:
            print_comparison(comparison)
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(comparison, f, indent=2)
        else:
            print(f"[WARN] No comparison data available for {args.date}")
    
    elif args.start_date and args.end_date:
        comparisons = compare_models_date_range(args.start_date, args.end_date)
        
        if comparisons:
            # Print summary
            print(f"\n{'='*70}")
            print(f"Model Comparison Summary")
            print(f"{'='*70}")
            print(f"Date range: {args.start_date} to {args.end_date}")
            print(f"Dates compared: {len(comparisons)}")
            
            # Aggregate metrics
            linear_maes = [c["metrics"].get("linear_mae", 0.0) for c in comparisons if "linear_mae" in c.get("metrics", {})]
            if linear_maes:
                avg_mae = sum(linear_maes) / len(linear_maes)
                print(f"Average Linear Model MAE: {avg_mae:.2f} bps")
            
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(comparisons, f, indent=2)
                print(f"\n[OK] Comparison results saved to {args.output}")
        else:
            print(f"[WARN] No comparison data available for date range")
    
    else:
        # Default: compare today
        today = dt.date.today().isoformat()
        comparison = compare_models_for_date(today)
        if comparison:
            print_comparison(comparison)
        else:
            print(f"[WARN] No comparison data available for {today}")

if __name__ == "__main__":
    main()

