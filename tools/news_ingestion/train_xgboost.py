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
except (ImportError, AttributeError) as e:
    HAS_XGBOOST = False
    xgb = None  # Set to None to avoid NameError
    print(f"[WARN] XGBoost not available: {e}")
    print("[WARN] Install with: pip install 'numpy<2.0' xgboost")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    shap = None
    print("[WARN] SHAP not available. Install with: pip install shap")

# All available tenors (lowercase for consistency with database)
TENORS = ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "20y", "30y"]
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

def compute_shap_values(model, X_sample: np.ndarray, feature_names: List[str], 
                        max_samples: int = 100, timeout_seconds: Optional[int] = None) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
    """
    Compute SHAP values for model interpretability.
    
    Args:
        model: Trained XGBoost model
        X_sample: Sample of features to explain (subset of training/validation data)
        feature_names: List of feature names
        max_samples: Maximum number of samples to use for SHAP (for performance)
        timeout_seconds: Optional timeout in seconds for SHAP computation
    
    Returns:
        (shap_values, importance_ranking)
        - shap_values: Array of SHAP values (n_samples, n_features)
        - importance_ranking: List of (feature_name, mean_abs_shap_value) sorted by importance
    """
    if not HAS_SHAP or shap is None:
        return None, None
    
    # Limit sample size for performance (especially for small datasets)
    if len(X_sample) > max_samples:
        indices = np.random.choice(len(X_sample), max_samples, replace=False)
        X_sample = X_sample[indices]
    elif len(X_sample) == 0:
        return None, None
    
    try:
        # For very small datasets, use even fewer samples
        if len(X_sample) > 5:
            X_sample = X_sample[:min(10, len(X_sample))]
        
        # Use TreeExplainer for XGBoost (fast and exact)
        explainer = shap.TreeExplainer(model)
        
        # Apply timeout if specified
        if timeout_seconds:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("SHAP computation timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        try:
            shap_values = explainer.shap_values(X_sample)
            
            if timeout_seconds:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            # Compute mean absolute SHAP value per feature
            mean_abs_shap = np.abs(shap_values).mean(0)
            
            # Create ranking
            importance_ranking = sorted(
                zip(feature_names, mean_abs_shap),
                key=lambda x: x[1],
                reverse=True
            )
            
            return shap_values, dict(importance_ranking)
        except TimeoutError:
            if timeout_seconds:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            print(f"[WARN] SHAP computation timed out after {timeout_seconds}s")
            return None, None
    except Exception as e:
        print(f"[WARN] SHAP computation failed: {e}")
        return None, None

def train_xgboost_model(X_train: np.ndarray, y_train: np.ndarray,
                       X_val: np.ndarray, y_val: np.ndarray,
                       target_name: str, feature_names: Optional[List[str]] = None) -> Tuple[Optional[object], Dict, Optional[Dict]]:
    """
    Train XGBoost model for a single target.
    
    Returns:
        (model, metrics, shap_info)
        - model: Trained XGBoost model
        - metrics: Performance metrics
        - shap_info: Dict with SHAP values and importance ranking (if available)
    """
    if not HAS_XGBOOST or xgb is None:
        raise ImportError("XGBoost not available")
    
    # XGBoost parameters - tuned for financial time series
    # Adjust for small datasets to prevent overfitting
    n_samples = len(X_train)
    
    if n_samples < 15:
        # Very small dataset - use conservative parameters to prevent overfitting
        params = {
            'objective': 'reg:squarederror',
            'n_estimators': 50,
            'max_depth': 3,
            'learning_rate': 0.1,
            'subsample': 1.0,
            'colsample_bytree': 1.0,
            'min_child_weight': 1,
            'gamma': 0.0,
            'reg_alpha': 0.5,
            'reg_lambda': 1.5,
            'random_state': 42,
            'n_jobs': -1
        }
        print(f"  [PARAMS] Using conservative parameters for small dataset ({n_samples} samples)")
    elif n_samples < 30:
        # Small dataset - moderate regularization
        params = {
            'objective': 'reg:squarederror',
            'n_estimators': 100,
            'max_depth': 4,
            'learning_rate': 0.08,
            'subsample': 0.9,
            'colsample_bytree': 0.9,
            'min_child_weight': 2,
            'gamma': 0.05,
            'reg_alpha': 0.2,
            'reg_lambda': 1.2,
            'random_state': 42,
            'n_jobs': -1
        }
        print(f"  [PARAMS] Using moderate regularization for small dataset ({n_samples} samples)")
    else:
        # Normal dataset - standard parameters
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
    # Note: early_stopping_rounds moved to constructor in newer XGBoost versions
    try:
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
    except TypeError:
        # Fallback for older XGBoost versions
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
    
    # Compute SHAP values if available (with timeout for small datasets)
    shap_info = None
    if HAS_SHAP and feature_names is not None:
        # Use validation set for SHAP (smaller and representative)
        # Use shorter timeout for small datasets
        timeout = 60 if len(X_val) < 10 else 120
        shap_values, importance_ranking = compute_shap_values(
            model, X_val, feature_names, max_samples=min(20, len(X_val)), timeout_seconds=timeout
        )
        if shap_values is not None:
            shap_info = {
                "shap_values": shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
                "importance_ranking": importance_ranking,
                "top_features": list(importance_ranking.items())[:10] if importance_ranking else []
            }
    
    return model, metrics, shap_info

def train_models(X: np.ndarray, y: Dict[str, np.ndarray], dates: List[str],
                feature_names: List[str],
                test_size: float = 0.2, use_time_split: bool = True) -> Dict[str, Dict]:
    """Train XGBoost models for all targets."""
    if not HAS_XGBOOST:
        print("[ERROR] XGBoost required for training")
        return {}
    
    results = {}
    
    # Adjust splits for small datasets
    if len(X) < 10:
        # Very small dataset - use minimal test set
        test_size = 0.1
        val_size = 0.3
    elif len(X) < 20:
        # Small dataset - use smaller test set
        test_size = 0.15
        val_size = 0.25
    else:
        # Normal dataset - use standard splits
        val_size = 0.2
    
    # Use time series split to respect temporal order
    if use_time_split and len(X) > 5:
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        dates_train, dates_test = dates[:split_idx], dates[split_idx:]
        
        # Further split training set for validation
        val_split_idx = int(len(X_train) * (1 - val_size))
        X_train_final, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
        
        # Store split indices for y arrays
        train_end_idx = val_split_idx
        val_end_idx = split_idx
    else:
        # For very small datasets, use all data
        if len(X) >= 8:
            X_train_val, X_test = train_test_split(
                X, test_size=test_size, random_state=42
            )
            val_split_idx = int(len(X_train_val) * (1 - val_size))
            X_train_final, X_val = X_train_val[:val_split_idx], X_train_val[val_split_idx:]
            train_end_idx = val_split_idx
            val_end_idx = len(X_train_val)
            split_idx = len(X) - len(X_test)
        else:
            # Too small - use all for training/validation
            X_train_final = X
            X_val = X[:max(1, len(X)//3)]
            X_test = X
            train_end_idx = len(X_train_final)
            val_end_idx = len(X_val)
            split_idx = 0
    
    print(f"[TRAIN] Training set: {len(X_train_final)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    if len(X) < 15:
        print(f"[WARN] Small dataset detected ({len(X)} samples) - using conservative model parameters")
    
    for target_name in TARGETS:
        print(f"\n[TRAIN] Training XGBoost model for {target_name}")
        
        y_target = y[target_name]
        if use_time_split and len(X) > 5:
            y_train = y_target[:train_end_idx]
            y_val = y_target[train_end_idx:val_end_idx]
            if split_idx > 0:
                y_test = y_target[split_idx:]
            else:
                y_test = y_target  # Use all as test for very small datasets
        else:
            # For random split or very small datasets, need to split y consistently
            if len(X) >= 8:
                y_train_val, y_test = train_test_split(
                    y_target, test_size=test_size, random_state=42
                )
                y_train = y_train_val[:train_end_idx]
                y_val = y_train_val[train_end_idx:]
            else:
                # Very small - use all
                y_train = y_target[:train_end_idx]
                y_val = y_target[train_end_idx:val_end_idx]
                y_test = y_target
        
        # Train model
        model, metrics, shap_info = train_xgboost_model(
            X_train_final, y_train, X_val, y_val, target_name, feature_names
        )
        
        # Test set evaluation
        y_pred_test = model.predict(X_test)
        test_mse = mean_squared_error(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        metrics["test_mse"] = float(test_mse)
        metrics["test_mae"] = float(test_mae)
        metrics["test_r2"] = float(test_r2)
        
        # Feature importance (built-in XGBoost)
        feature_importance = model.feature_importances_.tolist()
        
        results[target_name] = {
            "model": model,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "shap_info": shap_info
        }
        
        # Print SHAP top features if available
        if shap_info and shap_info.get("top_features"):
            print(f"  Top SHAP features: {', '.join([f[0] for f in shap_info['top_features'][:5]])}")
        
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
        
        # Save SHAP values if available (for later analysis)
        if model_info.get("shap_info") and model_info["shap_info"]:
            shap_path = MODEL_DIR / f"xgb_{target_name}_{date}_shap.json"
            # Convert numpy types to native Python types for JSON serialization
            shap_values = model_info["shap_info"].get("shap_values")
            if shap_values is not None:
                if isinstance(shap_values, list):
                    shap_values = [[float(x) for x in row] for row in shap_values]
                elif hasattr(shap_values, 'tolist'):
                    shap_values = shap_values.tolist()
            
            importance_ranking = model_info["shap_info"].get("importance_ranking")
            if importance_ranking:
                importance_ranking = {k: float(v) for k, v in importance_ranking.items()}
            
            shap_data = {
                "shap_values": shap_values,
                "importance_ranking": importance_ranking,
                "feature_names": feature_names
            }
            with open(shap_path, "w") as f:
                json.dump(shap_data, f, indent=2)
            print(f"[SAVE] Saved SHAP data for {target_name} to {shap_path}")
    
    # Save metadata
    metadata = {
        "date": date,
        "model_type": "xgboost",
        "targets": list(models.keys()),
        "feature_names": feature_names,
        "model_info": {
            target: {
                "metrics": info["metrics"],
                "top_features_xgb": [
                    feature_names[i] 
                    for i in np.argsort(info["feature_importance"])[-10:][::-1]
                ],
                "top_features_shap": (
                    list(info.get("shap_info", {}).get("importance_ranking", {}).keys())[:10]
                    if info.get("shap_info") and info["shap_info"].get("importance_ranking")
                    else []
                )
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
    models = train_models(X, y, dates, feature_names, test_size=args.test_size, 
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

