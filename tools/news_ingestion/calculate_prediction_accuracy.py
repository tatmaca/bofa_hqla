#!/usr/bin/env python3
"""
Prediction Accuracy Calculation Module
Calculates accuracy metrics (MAE, RMSE, R², directional accuracy, correlation)
for baseline and scenario predictions.
"""

import json
import numpy as np
import datetime as dt
from datetime import timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from train_linear_online import get_actual_yield_changes, TENORS


def calculate_accuracy_metrics(predictions: Dict[str, float], 
                              actuals: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate comprehensive accuracy metrics.
    
    Args:
        predictions: {tenor: predicted_delta_bps}
        actuals: {tenor: actual_delta_bps}
    
    Returns:
        Dictionary with metrics:
        - mae_bps: Mean Absolute Error
        - rmse_bps: Root Mean Squared Error
        - r2: R-squared (coefficient of determination)
        - directional_accuracy: Percentage of correct directions
        - correlation: Pearson correlation coefficient
        - total_tenors: Number of tenors with data
    """
    # Get common tenors
    common_tenors = [t for t in TENORS if t in predictions and t in actuals]
    
    if len(common_tenors) == 0:
        return {
            "mae_bps": None,
            "rmse_bps": None,
            "r2": None,
            "directional_accuracy": None,
            "correlation": None,
            "total_tenors": 0
        }
    
    # Extract arrays
    pred_array = np.array([predictions[t] for t in common_tenors])
    actual_array = np.array([actuals[t] for t in common_tenors])
    
    # Calculate errors
    errors = actual_array - pred_array
    
    # MAE (Mean Absolute Error)
    mae_bps = float(np.mean(np.abs(errors)))
    
    # RMSE (Root Mean Squared Error)
    rmse_bps = float(np.sqrt(np.mean(errors ** 2)))
    
    # R² (Coefficient of Determination)
    ss_res = np.sum(errors ** 2)  # Sum of squared residuals
    ss_tot = np.sum((actual_array - np.mean(actual_array)) ** 2)  # Total sum of squares
    if ss_tot > 0:
        r2 = float(1 - (ss_res / ss_tot))
    else:
        r2 = None  # All actuals are the same (no variance)
    
    # Directional Accuracy
    pred_signs = np.sign(pred_array)
    actual_signs = np.sign(actual_array)
    correct_directions = np.sum(pred_signs == actual_signs)
    directional_accuracy = float(correct_directions / len(common_tenors) * 100.0)
    
    # Correlation
    if len(common_tenors) > 1 and np.std(pred_array) > 0 and np.std(actual_array) > 0:
        correlation = float(np.corrcoef(pred_array, actual_array)[0, 1])
    else:
        correlation = None
    
    return {
        "mae_bps": mae_bps,
        "rmse_bps": rmse_bps,
        "r2": r2,
        "directional_accuracy": directional_accuracy,
        "correlation": correlation,
        "total_tenors": len(common_tenors)
    }


def calculate_tenor_accuracy(predictions: Dict[str, float], 
                           actuals: Dict[str, float], 
                           tenor: str) -> Dict[str, float]:
    """
    Calculate accuracy metrics for a single tenor.
    
    Args:
        predictions: {tenor: predicted_delta_bps}
        actuals: {tenor: actual_delta_bps}
        tenor: Tenor to calculate for
    
    Returns:
        Dictionary with:
        - error_bps: actual - predicted
        - abs_error_bps: |actual - predicted|
        - squared_error_bps: (actual - predicted)²
        - directional_correct: 1 if direction matches, 0 otherwise
    """
    if tenor not in predictions or tenor not in actuals:
        return {
            "error_bps": None,
            "abs_error_bps": None,
            "squared_error_bps": None,
            "directional_correct": None
        }
    
    pred = predictions[tenor]
    actual = actuals[tenor]
    error = actual - pred
    
    # Directional accuracy
    pred_sign = 1 if pred > 0 else (-1 if pred < 0 else 0)
    actual_sign = 1 if actual > 0 else (-1 if actual < 0 else 0)
    directional_correct = 1.0 if pred_sign == actual_sign else 0.0
    
    return {
        "error_bps": float(error),
        "abs_error_bps": float(abs(error)),
        "squared_error_bps": float(error ** 2),
        "directional_correct": directional_correct
    }


def save_scenario_accuracy(date: str, 
                           actual_date: str,
                           scenario_name: str, 
                           predictions: Dict[str, float], 
                           actuals: Dict[str, float]) -> bool:
    """
    Save scenario prediction accuracy to database.
    
    Args:
        date: Prediction date (base_date, when prediction was made)
        actual_date: Actual yield change date (prediction_date, typically date+1)
        scenario_name: 'baseline' or scenario name
        predictions: {tenor: predicted_delta_bps}
        actuals: {tenor: actual_delta_bps}
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_conn()
    c = conn.cursor()
    
    try:
        # Save per-tenor accuracy
        for tenor in TENORS:
            if tenor in predictions and tenor in actuals:
                pred = predictions[tenor]
                actual = actuals[tenor]
                error = actual - pred
                
                c.execute("""
                    INSERT OR REPLACE INTO scenario_prediction_accuracy
                    (date, actual_date, scenario_name, tenor, predicted_delta_bps, 
                     actual_delta_bps, error_bps, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date,
                    actual_date,
                    scenario_name,
                    tenor,
                    pred,
                    actual,
                    error,
                    dt.datetime.now(timezone.utc).isoformat()
                ))
        
        # Calculate and save summary metrics
        metrics = calculate_accuracy_metrics(predictions, actuals)
        
        c.execute("""
            INSERT OR REPLACE INTO daily_accuracy_summary
            (date, actual_date, scenario_name, mae_bps, rmse_bps, r2, 
             directional_accuracy, correlation, total_tenors, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            actual_date,
            scenario_name,
            metrics["mae_bps"],
            metrics["rmse_bps"],
            metrics["r2"],
            metrics["directional_accuracy"],
            metrics["correlation"],
            metrics["total_tenors"],
            dt.datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save accuracy for {scenario_name} on {date}: {e}")
        conn.close()
        return False


def load_accuracy_history(start_date: str, 
                         end_date: str, 
                         scenario_name: Optional[str] = None) -> List[Dict]:
    """
    Load historical accuracy data from database.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenario_name: Optional scenario name filter (if None, loads all scenarios)
    
    Returns:
        List of accuracy records, each with:
        - date, actual_date, scenario_name, mae_bps, rmse_bps, r2,
          directional_accuracy, correlation, total_tenors
    """
    conn = get_conn()
    c = conn.cursor()
    
    if scenario_name:
        rows = c.execute("""
            SELECT date, actual_date, scenario_name, mae_bps, rmse_bps, r2,
                   directional_accuracy, correlation, total_tenors
            FROM daily_accuracy_summary
            WHERE date >= ? AND date <= ?
              AND scenario_name = ?
            ORDER BY date, scenario_name
        """, (start_date, end_date, scenario_name)).fetchall()
    else:
        rows = c.execute("""
            SELECT date, actual_date, scenario_name, mae_bps, rmse_bps, r2,
                   directional_accuracy, correlation, total_tenors
            FROM daily_accuracy_summary
            WHERE date >= ? AND date <= ?
            ORDER BY date, scenario_name
        """, (start_date, end_date)).fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def load_tenor_accuracy_history(start_date: str,
                                end_date: str,
                                scenario_name: Optional[str] = None,
                                tenor: Optional[str] = None) -> List[Dict]:
    """
    Load per-tenor accuracy history.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenario_name: Optional scenario name filter
        tenor: Optional tenor filter
    
    Returns:
        List of per-tenor accuracy records
    """
    conn = get_conn()
    c = conn.cursor()
    
    query = """
        SELECT date, actual_date, scenario_name, tenor, predicted_delta_bps,
               actual_delta_bps, error_bps
        FROM scenario_prediction_accuracy
        WHERE date >= ? AND date <= ?
    """
    params = [start_date, end_date]
    
    if scenario_name:
        query += " AND scenario_name = ?"
        params.append(scenario_name)
    
    if tenor:
        query += " AND tenor = ?"
        params.append(tenor)
    
    query += " ORDER BY date, scenario_name, tenor"
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def calculate_accuracy_for_scenario_curves(date: str) -> Dict[str, Dict]:
    """
    Calculate accuracy for all scenarios in a scenario curves file.
    
    Args:
        date: Date string (YYYY-MM-DD) - the base_date from scenario curves
    
    Returns:
        Dictionary mapping scenario_name to accuracy metrics
    """
    from pathlib import Path
    
    # Load scenario curves
    scenario_file = Path(__file__).parent / "scenario_predictions" / f"scenario_curves_{date}.json"
    if not scenario_file.exists():
        print(f"[WARN] Scenario curves file not found: {scenario_file}")
        return {}
    
    with open(scenario_file) as f:
        curves = json.load(f)
    
    # Get prediction date (actual_date)
    actual_date = curves.get("prediction_date")
    if not actual_date:
        print(f"[WARN] No prediction_date in scenario curves for {date}")
        return {}
    
    # Get actual yield changes
    actuals = get_actual_yield_changes(actual_date)
    if not actuals:
        print(f"[WARN] No actual yield changes available for {actual_date}")
        return {}
    
    results = {}
    
    # Calculate accuracy for baseline
    baseline = curves.get("baseline", {})
    baseline_preds = baseline.get("predictions", {})
    if baseline_preds:
        metrics = calculate_accuracy_metrics(baseline_preds, actuals)
        results["baseline"] = metrics
        save_scenario_accuracy(date, actual_date, "baseline", baseline_preds, actuals)
    
    # Calculate accuracy for each scenario
    for key, value in curves.items():
        if key not in ["date", "base_date", "prediction_date", "baseline"]:
            scenario_name = value.get("scenario_name", key)
            scenario_preds = value.get("predictions", {})
            if scenario_preds:
                metrics = calculate_accuracy_metrics(scenario_preds, actuals)
                results[scenario_name] = metrics
                save_scenario_accuracy(date, actual_date, scenario_name, scenario_preds, actuals)
    
    return results


if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="Calculate prediction accuracy for scenario curves")
    ap.add_argument("--date", type=str, required=True, help="Date (YYYY-MM-DD) to calculate accuracy for")
    args = ap.parse_args()
    
    results = calculate_accuracy_for_scenario_curves(args.date)
    
    if results:
        print(f"\nAccuracy Metrics for {args.date}:")
        print("=" * 80)
        for scenario_name, metrics in results.items():
            print(f"\n{scenario_name}:")
            print(f"  MAE: {metrics['mae_bps']:.2f} bps")
            print(f"  RMSE: {metrics['rmse_bps']:.2f} bps")
            if metrics['r2'] is not None:
                print(f"  R²: {metrics['r2']:.3f}")
            print(f"  Directional Accuracy: {metrics['directional_accuracy']:.1f}%")
            if metrics['correlation'] is not None:
                print(f"  Correlation: {metrics['correlation']:.3f}")
            print(f"  Tenors: {metrics['total_tenors']}")
    else:
        print(f"[WARN] No accuracy calculated for {args.date}")

