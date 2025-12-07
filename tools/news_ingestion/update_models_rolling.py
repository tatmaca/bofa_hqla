#!/usr/bin/env python3
"""
Rolling 30-Day Model Training and Update System
Continuously updates models based on the most recent 30 days of data.
"""

import os
import sys
import json
import signal
import datetime as dt
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from collect_training_data import collect_training_data, save_training_data

# Import XGBoost functions only if available
try:
    from train_xgboost import train_models, load_training_data, evaluate_accuracy, save_models
    HAS_XGBOOST_TRAIN = True
except (ImportError, AttributeError) as e:
    HAS_XGBOOST_TRAIN = False
    print(f"[WARN] XGBoost training not available: {e}")

# Timeout settings
TRAINING_TIMEOUT = 600  # 10 minutes for training (6 models × ~1-2 min each)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def get_rolling_window_dates(days: int = 30) -> tuple:
    """Get start and end dates for rolling window."""
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()

def update_models_with_rolling_window(days: int = 30, threshold_mae: float = 3.0, filter_significance: bool = False):
    """Update models using rolling window of recent data."""
    start_date, end_date = get_rolling_window_dates(days)
    
    print(f"\n{'='*70}")
    print(f"ROLLING {days}-DAY MODEL UPDATE")
    print(f"Date range: {start_date} to {end_date}")
    print(f"{'='*70}\n")
    
    # Step 1: Collect training data
    print(f"[STEP 1] Collecting training data from last {days} days...")
    print(f"[INFO] Significance filtering: {'ON' if filter_significance else 'OFF'}")
    
    try:
        # Try with significance filtering first if enabled
        training_data = collect_training_data(start_date, end_date, filter_significance=filter_significance)
        
        # If not enough data and significance filtering was on, try without it
        if len(training_data) < 7 and filter_significance:
            print(f"[INFO] Only {len(training_data)} examples with significance filter, trying without...")
            training_data = collect_training_data(start_date, end_date, filter_significance=False)
    except Exception as e:
        print(f"[ERROR] Failed to collect training data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Lower minimum requirement for small datasets (but warn)
    min_examples = 5  # Reduced from 7 to allow training with less data
    if len(training_data) < min_examples:
        print(f"[WARN] Insufficient training data: {len(training_data)} examples (need at least {min_examples})")
        print(f"[WARN] Need more historical data with valid LLM predictions.")
        print(f"[WARN] Make sure OpenAI API key is set and daily pipeline is generating real LLM analyses.")
        print(f"[WARN] Current data: {len(training_data)} examples (need {min_examples}+)")
        return False
    elif len(training_data) < 15:
        print(f"[WARN] Small training dataset: {len(training_data)} examples (recommended: 15+)")
        print(f"[WARN] Models will use conservative parameters to prevent overfitting")
    
    # Save training data
    data_path = Path(__file__).parent / f"training_data_rolling_{days}d.json"
    save_training_data(training_data, data_path)
    
    # Step 2: Train models
    print(f"\n[STEP 2] Training XGBoost models on {len(training_data)} examples...")
    print(f"[INFO] Training timeout: {TRAINING_TIMEOUT}s")
    
    if not HAS_XGBOOST_TRAIN:
        print("[ERROR] XGBoost training not available")
        print("[INFO] Install OpenMP: brew install libomp")
        print("[INFO] Or use conda: conda install -c conda-forge xgboost")
        return False
    
    try:
        X, y, dates = load_training_data(data_path)
        feature_names = sorted(training_data[0]["features"].keys())
        
        # Train with timeout protection
        print(f"[TRAIN] Starting training with {TRAINING_TIMEOUT}s timeout...")
        
        # Set up timeout handler (Unix only - Windows will skip timeout)
        old_handler = None
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TRAINING_TIMEOUT)
        
        try:
            # Train with time series split
            models = train_models(X, y, dates, feature_names, test_size=0.2, use_time_split=True)
            
            # Cancel alarm if training completed
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)
        except TimeoutError:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)
            print(f"[ERROR] Training timed out after {TRAINING_TIMEOUT}s")
            print("[INFO] Consider reducing training data size or increasing timeout")
            return False
        except Exception as e:
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)
            raise
        
        if not models:
            print("[ERROR] Model training returned no results")
            return False
        
        # Step 3: Evaluate
        print(f"\n[STEP 3] Evaluating model accuracy...")
        evaluation = evaluate_accuracy(models, threshold_mae=threshold_mae)
        
        print(f"\n[EVAL] Results:")
        mean_r2 = evaluation['overall_metrics']['mean_r2']
        mean_mae = evaluation['overall_metrics']['mean_mae']
        print(f"  Mean R²: {mean_r2:.3f}")
        print(f"  Mean MAE: {mean_mae:.3f} bps")
        print(f"  Threshold met: {evaluation['all_targets_meet_threshold']}")
        
        # Warn about negative R² (indicates overfitting or small test set)
        if mean_r2 < 0:
            print(f"\n[WARN] Negative R² ({mean_r2:.3f}) indicates model performs worse than baseline")
            print(f"[WARN] This is common with small datasets (< 20 examples)")
            print(f"[WARN] Consider collecting more training data for better performance")
        elif mean_r2 < 0.3:
            print(f"\n[INFO] Low R² ({mean_r2:.3f}) - model has limited predictive power")
            print(f"[INFO] More training data may improve performance")
        
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

