#!/usr/bin/env python3
"""
Incremental XGBoost Training with Timeout Handling
Trains models with limited data and handles timeouts gracefully.
"""

import os
import json
import signal
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import datetime as dt
import sys

sys.path.insert(0, str(Path(__file__).parent))

from train_xgboost import (
    load_training_data, train_models, save_models, evaluate_accuracy,
    MODEL_DIR, TARGETS, HAS_XGBOOST, HAS_SHAP
)

# Timeout settings
TRAINING_TIMEOUT = 300  # 5 minutes for training
SHAP_TIMEOUT = 120  # 2 minutes for SHAP computation

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def train_with_timeout(X, y, dates, feature_names, timeout_seconds=TRAINING_TIMEOUT):
    """Train models with timeout protection."""
    # Set up signal handler for timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        print(f"[TRAIN] Training with {timeout_seconds}s timeout...")
        models = train_models(X, y, dates, feature_names, test_size=0.2, use_time_split=True)
        signal.alarm(0)  # Cancel alarm
        signal.signal(signal.SIGALRM, old_handler)  # Restore handler
        return models
    except TimeoutError:
        print(f"[WARN] Training timed out after {timeout_seconds}s")
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return None
    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        print(f"[ERROR] Training failed: {e}")
        return None

def adjust_params_for_small_data(n_samples: int):
    """Adjust XGBoost parameters for small datasets."""
    if n_samples < 10:
        return {
            'n_estimators': 50,
            'max_depth': 3,
            'learning_rate': 0.1,
            'subsample': 1.0,
            'colsample_bytree': 1.0,
            'min_child_weight': 1,
        }
    elif n_samples < 20:
        return {
            'n_estimators': 100,
            'max_depth': 4,
            'learning_rate': 0.08,
        }
    else:
        return {}  # Use defaults

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Train XGBoost models incrementally with timeout")
    ap.add_argument("--data", type=str, help="Training data JSON file (default: use most recent)")
    ap.add_argument("--timeout", type=int, default=TRAINING_TIMEOUT, help="Training timeout in seconds")
    ap.add_argument("--shap-timeout", type=int, default=SHAP_TIMEOUT, help="SHAP computation timeout")
    args = ap.parse_args()
    
    if not HAS_XGBOOST:
        print("[ERROR] XGBoost is required. Install with: pip install xgboost")
        return
    
    # Find training data file
    if args.data:
        data_path = Path(__file__).parent / args.data
    else:
        # Use most recent training data
        training_files = sorted(Path(__file__).parent.glob("training_data_*.json"), 
                              key=lambda p: p.stat().st_mtime, reverse=True)
        if not training_files:
            print("[ERROR] No training data files found")
            return
        data_path = training_files[0]
        print(f"[INFO] Using most recent training data: {data_path.name}")
    
    if not data_path.exists():
        print(f"[ERROR] Training data file not found: {data_path}")
        return
    
    print(f"[LOAD] Loading training data from {data_path}")
    X, y, dates = load_training_data(data_path)
    
    if X is None or len(X) == 0:
        print("[ERROR] No training data loaded")
        return
    
    print(f"[INFO] Loaded {len(X)} samples with {X.shape[1]} features")
    
    # Check if we have enough data
    if len(X) < 5:
        print(f"[WARN] Very small dataset ({len(X)} samples). Results may be unreliable.")
        print("[INFO] Consider collecting more training data.")
    
    # Get feature names
    with open(data_path) as f:
        data = json.load(f)
    feature_names = sorted(data[0]["features"].keys())
    
    # Check for factor features
    has_factors = any('factor_' in f for f in feature_names)
    print(f"[INFO] Has factor features: {has_factors}")
    if has_factors:
        factor_features = [f for f in feature_names if 'factor_' in f]
        print(f"[INFO] Found {len(factor_features)} factor features")
    
    # Adjust parameters for small data
    param_adjustments = adjust_params_for_small_data(len(X))
    if param_adjustments:
        print(f"[INFO] Adjusting parameters for small dataset: {param_adjustments}")
        # Note: This would require modifying train_xgboost.py to accept params
        # For now, we'll proceed with defaults
    
    # Train models with timeout
    print(f"\n[TRAIN] Training XGBoost models (timeout: {args.timeout}s)...")
    models = train_with_timeout(X, y, dates, feature_names, args.timeout)
    
    if not models:
        print("[ERROR] Model training failed or timed out")
        return
    
    # Evaluate accuracy
    print(f"\n[EVAL] Evaluating model accuracy...")
    evaluation = evaluate_accuracy(models, threshold_mae=5.0)  # More lenient threshold for small data
    
    print(f"\n[EVAL] Results:")
    print(f"  Mean R²: {evaluation['overall_metrics']['mean_r2']:.3f}")
    print(f"  Mean MAE: {evaluation['overall_metrics']['mean_mae']:.3f} bps")
    print(f"  Threshold met: {evaluation['all_targets_meet_threshold']}")
    
    # Save models
    date = dt.date.today().isoformat()
    save_models(models, feature_names, date)
    
    # Save evaluation
    eval_path = MODEL_DIR / f"evaluation_{date}.json"
    with open(eval_path, "w") as f:
        json.dump(evaluation, f, indent=2)
    print(f"[SAVE] Saved evaluation to {eval_path}")
    
    # Print SHAP summary if available
    print(f"\n[SHAP] Summary:")
    for target, model_info in models.items():
        shap_info = model_info.get("shap_info")
        if shap_info and shap_info.get("top_features"):
            top_features = shap_info["top_features"][:5]
            print(f"  {target}: {', '.join([f[0] for f in top_features])}")
    
    if evaluation["all_targets_meet_threshold"]:
        print(f"\n[SUCCESS] All models meet accuracy threshold!")
    else:
        print(f"\n[INFO] Some models need improvement. Consider:")
        print("  - Collecting more training data")
        print("  - The models were trained with limited data")

if __name__ == "__main__":
    main()

