#!/usr/bin/env python3
"""
XGBoost Model Training for Yield Curve Prediction
Trains XGBoost models to learn from LLM predictions and improve accuracy.
"""

import os
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle
import datetime as dt

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[WARN] XGBoost not installed. Install with: pip install xgboost")

TENORS = ["2y", "5y", "10y", "30y"]
SPREADS = ["2s10s", "2s30s"]
TARGETS = TENORS + SPREADS

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

def load_training_data(data_path: Path) -> Tuple[np.ndarray, Dict[str, np.ndarray], List[str]]:
    """Load training data and convert to feature/target arrays."""
    with open(data_path) as f:
        data = json.load(f)
    
    if not data:
        return None, {}, []
    
    # Get feature names from first example
    feature_names = sorted(data[0]["features"].keys())
    
    # Build feature matrix and target dict
    X = []
    y = {target: [] for target in TARGETS}
    dates = []
    
    for example in data:
        features = example["features"]
        actual = example["actual"]
        
        # Build feature vector in consistent order
        feature_vec = [features.get(name, 0.0) for name in feature_names]
        X.append(feature_vec)
        
        # Extract targets
        for target in TARGETS:
            y[target].append(actual.get(target, 0.0))
        
        dates.append(example["date"])
    
    X = np.array(X)
    y = {k: np.array(v) for k, v in y.items()}
    
    print(f"[LOAD] Loaded {len(X)} examples with {len(feature_names)} features")
    return X, y, dates

def train_xgboost_model(X_train: np.ndarray, y_train: np.ndarray,
                       X_val: np.ndarray, y_val: np.ndarray,
                       target_name: str) -> Tuple[xgb.XGBRegressor, Dict]:
    """Train XGBoost model for a single target."""
    
    # XGBoost parameters - tuned for financial time series
    params = {
        'objective': 'reg:squarederror',
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 3,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
        'n_jobs': -1
    }
    
    model = xgb.XGBRegressor(**params)
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=20,
        verbose=False
    )
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    train_mse = mean_squared_error(y_train, y_pred_train)
    val_mse = mean_squared_error(y_val, y_pred_val)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    val_mae = mean_absolute_error(y_val, y_pred_val)
    train_r2 = r2_score(y_train, y_pred_train)
    val_r2 = r2_score(y_val, y_pred_val)
    
    metrics = {
        "train_mse": float(train_mse),
        "val_mse": float(val_mse),
        "train_mae": float(train_mae),
        "val_mae": float(val_mae),
        "train_r2": float(train_r2),
        "val_r2": float(val_r2),
        "best_iteration": model.best_iteration if hasattr(model, 'best_iteration') else params['n_estimators']
    }
    
    return model, metrics

def train_models(X: np.ndarray, y: Dict[str, np.ndarray], dates: List[str],
                test_size: float = 0.2, use_time_split: bool = True) -> Dict[str, Dict]:
    """Train XGBoost models for all targets."""
    if not HAS_XGBOOST:
        print("[ERROR] XGBoost required for training")
        return {}
    
    results = {}
    
    # Use time series split to respect temporal order
    if use_time_split and len(X) > 10:
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        dates_train, dates_test = dates[:split_idx], dates[split_idx:]
        
        # Further split training set for validation
        val_split_idx = int(len(X_train) * 0.8)
        X_train_final, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
    else:
        # Standard random split
        X_train_final, X_test = train_test_split(X, test_size=test_size, random_state=42)
        val_split_idx = int(len(X_train_final) * 0.8)
        X_train_final, X_val = X_train_final[:val_split_idx], X_train_final[val_split_idx:]
    
    print(f"[TRAIN] Training set: {len(X_train_final)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    for target_name in TARGETS:
        print(f"\n[TRAIN] Training XGBoost model for {target_name}")
        
        y_target = y[target_name]
        if use_time_split:
            y_train = y_target[:split_idx][:val_split_idx]
            y_val = y_target[:split_idx][val_split_idx:]
            y_test = y_target[split_idx:]
        else:
            y_train, y_test = train_test_split(y_target, test_size=test_size, random_state=42)
            val_split_idx = int(len(y_train) * 0.8)
            y_train, y_val = y_train[:val_split_idx], y_train[val_split_idx:]
        
        # Train model
        model, metrics = train_xgboost_model(X_train_final, y_train, X_val, y_val, target_name)
        
        # Test set evaluation
        y_pred_test = model.predict(X_test)
        test_mse = mean_squared_error(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        metrics["test_mse"] = float(test_mse)
        metrics["test_mae"] = float(test_mae)
        metrics["test_r2"] = float(test_r2)
        
        # Feature importance
        feature_importance = model.feature_importances_.tolist()
        
        results[target_name] = {
            "model": model,
            "metrics": metrics,
            "feature_importance": feature_importance
        }
        
        print(f"  Train R²: {metrics['train_r2']:.3f}, Val R²: {metrics['val_r2']:.3f}, Test R²: {metrics['test_r2']:.3f}")
        print(f"  Test MAE: {metrics['test_mae']:.4f} bps, Test RMSE: {np.sqrt(metrics['test_mse']):.4f} bps")
    
    return results

def save_models(models: Dict[str, Dict], feature_names: List[str], date: str):
    """Save trained models and metadata."""
    for target_name, model_info in models.items():
        model_path = MODEL_DIR / f"xgb_{target_name}_{date}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model_info["model"], f)
        print(f"[SAVE] Saved {target_name} model to {model_path}")
    
    # Save metadata
    metadata = {
        "date": date,
        "model_type": "xgboost",
        "targets": list(models.keys()),
        "feature_names": feature_names,
        "model_info": {
            target: {
                "metrics": info["metrics"],
                "top_features": [
                    feature_names[i] 
                    for i in np.argsort(info["feature_importance"])[-10:][::-1]
                ]
            }
            for target, info in models.items()
        }
    }
    
    metadata_path = MODEL_DIR / f"xgb_metadata_{date}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[SAVE] Saved metadata to {metadata_path}")
    return metadata_path

def evaluate_accuracy(models: Dict[str, Dict], threshold_mae: float = 3.0) -> Dict:
    """Evaluate model accuracy and check if threshold is met."""
    evaluation = {
        "all_targets_meet_threshold": True,
        "target_results": {},
        "overall_metrics": {}
    }
    
    all_test_r2 = []
    all_test_mae = []
    
    for target_name, model_info in models.items():
        metrics = model_info["metrics"]
        test_mae = metrics["test_mae"]
        test_r2 = metrics["test_r2"]
        
        meets_threshold = test_mae <= threshold_mae
        
        evaluation["target_results"][target_name] = {
            "test_mae": test_mae,
            "test_r2": test_r2,
            "meets_threshold": meets_threshold
        }
        
        if not meets_threshold:
            evaluation["all_targets_meet_threshold"] = False
        
        all_test_r2.append(test_r2)
        all_test_mae.append(test_mae)
    
    evaluation["overall_metrics"] = {
        "mean_r2": float(np.mean(all_test_r2)),
        "mean_mae": float(np.mean(all_test_mae)),
        "threshold_mae": threshold_mae
    }
    
    return evaluation

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Train XGBoost models for yield curve prediction")
    ap.add_argument("--data", type=str, required=True, help="Training data JSON file")
    ap.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    ap.add_argument("--threshold-mae", type=float, default=3.0, help="MAE threshold in bps")
    ap.add_argument("--no-time-split", action="store_true", help="Use random split instead of time series split")
    args = ap.parse_args()
    
    if not HAS_XGBOOST:
        print("[ERROR] XGBoost is required. Install with: pip install xgboost")
        return
    
    data_path = Path(__file__).parent / args.data
    if not data_path.exists():
        print(f"[ERROR] Training data file not found: {data_path}")
        return
    
    print(f"[LOAD] Loading training data from {data_path}")
    X, y, dates = load_training_data(data_path)
    
    if X is None or len(X) == 0:
        print("[ERROR] No training data loaded")
        return
    
    # Get feature names
    with open(data_path) as f:
        data = json.load(f)
    feature_names = sorted(data[0]["features"].keys())
    
    print(f"[TRAIN] Training XGBoost models...")
    models = train_models(X, y, dates, test_size=args.test_size, 
                         use_time_split=not args.no_time_split)
    
    if not models:
        print("[ERROR] Model training failed")
        return
    
    # Evaluate accuracy
    print(f"\n[EVAL] Evaluating model accuracy (threshold: {args.threshold_mae} bps MAE)...")
    evaluation = evaluate_accuracy(models, threshold_mae=args.threshold_mae)
    
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
    
    if evaluation["all_targets_meet_threshold"]:
        print(f"\n[SUCCESS] All models meet accuracy threshold!")
    else:
        print(f"\n[INFO] Some models need improvement. Consider:")
        print("  - Collecting more training data")
        print("  - Adjusting model hyperparameters")
        print("  - Adding more features")

if __name__ == "__main__":
    main()

