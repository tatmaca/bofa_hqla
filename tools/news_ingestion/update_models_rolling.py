#!/usr/bin/env python3
"""
Rolling 30-Day Model Training and Update System
Continuously updates models based on the most recent 30 days of data.
"""

import os
import sys
import json
import datetime as dt
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from collect_training_data import collect_training_data, save_training_data
from train_xgboost import train_models, load_training_data, evaluate_accuracy, save_models
from enhance_predictions import load_latest_xgb_models

def get_rolling_window_dates(days: int = 30) -> tuple:
    """Get start and end dates for rolling window."""
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()

def update_models_with_rolling_window(days: int = 30, threshold_mae: float = 3.0):
    """Update models using rolling window of recent data."""
    start_date, end_date = get_rolling_window_dates(days)
    
    print(f"\n{'='*70}")
    print(f"ROLLING {days}-DAY MODEL UPDATE")
    print(f"Date range: {start_date} to {end_date}")
    print(f"{'='*70}\n")
    
    # Step 1: Collect training data
    print(f"[STEP 1] Collecting training data from last {days} days...")
    try:
        training_data = collect_training_data(start_date, end_date)
    except Exception as e:
        print(f"[ERROR] Failed to collect training data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if len(training_data) < 7:
        print(f"[INFO] Insufficient training data: {len(training_data)} examples (need at least 7)")
        print(f"[INFO] Need more historical data. Run daily pipeline to generate analyses and snapshots.")
        return False
    
    # Save training data
    data_path = Path(__file__).parent / f"training_data_rolling_{days}d.json"
    save_training_data(training_data, data_path)
    
    # Step 2: Train models
    print(f"\n[STEP 2] Training XGBoost models on {len(training_data)} examples...")
    
    try:
        X, y, dates = load_training_data(data_path)
        feature_names = sorted(training_data[0]["features"].keys())
        
        # Train with time series split
        models = train_models(X, y, dates, test_size=0.2, use_time_split=True)
        
        if not models:
            print("[ERROR] Model training returned no results")
            return False
        
        # Step 3: Evaluate
        print(f"\n[STEP 3] Evaluating model accuracy...")
        evaluation = evaluate_accuracy(models, threshold_mae=threshold_mae)
        
        print(f"\n[EVAL] Results:")
        print(f"  Mean R²: {evaluation['overall_metrics']['mean_r2']:.3f}")
        print(f"  Mean MAE: {evaluation['overall_metrics']['mean_mae']:.3f} bps")
        print(f"  Threshold met: {evaluation['all_targets_meet_threshold']}")
        
        # Step 4: Save models
        print(f"\n[STEP 4] Saving updated models...")
        date = dt.date.today().isoformat()
        save_models(models, feature_names, date)
        
        # Save evaluation
        eval_path = Path(__file__).parent / "models" / f"rolling_evaluation_{date}.json"
        with open(eval_path, "w") as f:
            json.dump({
                "window_days": days,
                "start_date": start_date,
                "end_date": end_date,
                "training_examples": len(training_data),
                **evaluation
            }, f, indent=2)
        
        print(f"[SUCCESS] Models updated with {days}-day rolling window")
        print(f"  Training examples: {len(training_data)}")
        print(f"  Mean R²: {evaluation['overall_metrics']['mean_r2']:.3f}")
        print(f"  Mean MAE: {evaluation['overall_metrics']['mean_mae']:.3f} bps")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] XGBoost not available: {e}")
        print(f"[INFO] Run: python3 fix_dependencies.py")
        return False
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Update models with rolling window")
    ap.add_argument("--days", type=int, default=30, help="Rolling window size in days (default: 30)")
    ap.add_argument("--threshold-mae", type=float, default=3.0, help="MAE threshold in bps")
    args = ap.parse_args()
    
    success = update_models_with_rolling_window(days=args.days, threshold_mae=args.threshold_mae)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

