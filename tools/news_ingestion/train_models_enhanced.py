#!/usr/bin/env python3
"""
Enhanced Model Training with Multiple Algorithms
Trains XGBoost, Random Forest, and Attention-based models for yield curve prediction.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import datetime as dt

# Try to import ML libraries
try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARN] scikit-learn not available")

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[WARN] PyTorch not available for attention models")

TARGETS = ["2y", "5y", "10y", "30y", "2s10s", "2s30s"]

class AttentionModel(nn.Module):
    """Simple attention-based model for time series prediction."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_heads: int = 4):
        super().__init__()
        self.embedding = nn.Linear(input_dim, hidden_dim)
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
    
    def forward(self, x):
        # x shape: (batch, seq_len, features)
        x = self.embedding(x)
        attn_out, _ = self.attention(x, x, x)
        # Take mean over sequence
        pooled = attn_out.mean(dim=1)
        return self.fc(pooled)

def load_training_data(data_path: Path) -> Tuple[np.ndarray, Dict[str, np.ndarray], List[str]]:
    """Load training data from JSON file."""
    with open(data_path) as f:
        data = json.load(f)
    
    if not data:
        return None, {}, []
    
    # Get feature names (sorted for consistency)
    feature_names = sorted(data[0]["features"].keys())
    
    # Build feature matrix and target dict
    X = []
    y = {target: [] for target in TARGETS}
    dates = []
    
    for example in data:
        features = example["features"]
        X.append([features.get(name, 0.0) for name in feature_names])
        
        targets = example["targets"]
        for target in TARGETS:
            y[target].append(targets.get(target, 0.0))
        
        dates.append(example["date"])
    
    X = np.array(X)
    y = {target: np.array(values) for target, values in y.items()}
    
    return X, y, dates

def train_xgboost_model(X_train, y_train, X_val, y_val, target_name: str) -> Tuple[Optional[object], Dict]:
    """Train XGBoost model."""
    if not HAS_SKLEARN:
        return None, {}
    
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
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    metrics = {
        "train_mse": float(mean_squared_error(y_train, y_pred_train)),
        "val_mse": float(mean_squared_error(y_val, y_pred_val)),
        "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
        "val_mae": float(mean_absolute_error(y_val, y_pred_val)),
        "train_r2": float(r2_score(y_train, y_pred_train)),
        "val_r2": float(r2_score(y_val, y_pred_val)),
    }
    
    # Get feature importance
    feature_importance = model.feature_importances_.tolist()
    
    return model, metrics, feature_importance

def train_random_forest_model(X_train, y_train, X_val, y_val, target_name: str) -> Tuple[Optional[object], Dict]:
    """Train Random Forest model."""
    if not HAS_SKLEARN:
        return None, {}
    
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    metrics = {
        "train_mse": float(mean_squared_error(y_train, y_pred_train)),
        "val_mse": float(mean_squared_error(y_val, y_pred_val)),
        "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
        "val_mae": float(mean_absolute_error(y_val, y_pred_val)),
        "train_r2": float(r2_score(y_train, y_pred_train)),
        "val_r2": float(r2_score(y_val, y_pred_val)),
    }
    
    feature_importance = model.feature_importances_.tolist()
    
    return model, metrics, feature_importance

def train_models_ensemble(X: np.ndarray, y: Dict[str, np.ndarray], dates: List[str],
                          test_size: float = 0.2, use_time_split: bool = True) -> Dict[str, Dict]:
    """
    Train ensemble of models (XGBoost, Random Forest) and compare performance.
    """
    if not HAS_SKLEARN:
        print("[ERROR] scikit-learn required for training")
        return {}
    
    results = {}
    
    # Time series split
    if use_time_split and len(X) > 10:
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        dates_train, dates_test = dates[:split_idx], dates[split_idx:]
        
        val_split_idx = int(len(X_train) * 0.8)
        X_train_final, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
        
        # Store split indices for y arrays
        train_end_idx = val_split_idx
        val_end_idx = split_idx
    else:
        # Random split
        X_train_val, X_test, _, dates_test = train_test_split(
            X, dates, test_size=test_size, random_state=42
        )
        val_split_idx = int(len(X_train_val) * 0.8)
        X_train_final, X_val = X_train_val[:val_split_idx], X_train_val[val_split_idx:]
        
        # For random split, we need to track indices differently
        train_end_idx = val_split_idx
        val_end_idx = len(X_train_val)
        split_idx = len(X) - len(X_test)
    
    print(f"[TRAIN] Training set: {len(X_train_final)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    for target_name in TARGETS:
        y_target = y[target_name]
        
        if use_time_split and len(X) > 10:
            y_train = y_target[:train_end_idx]
            y_val = y_target[train_end_idx:val_end_idx]
            y_test = y_target[split_idx:]
        else:
            # For random split, need to split y consistently
            y_train_val, y_test = train_test_split(
                y_target, test_size=test_size, random_state=42
            )
            y_train = y_train_val[:train_end_idx]
            y_val = y_train_val[train_end_idx:]
        
        print(f"\n[TRAIN] Training models for {target_name}...")
        
        target_results = {}
        
        # Train XGBoost
        try:
            xgb_model, xgb_metrics, xgb_importance = train_xgboost_model(
                X_train_final, y_train, X_val, y_val, target_name
            )
            if xgb_model:
                target_results["xgboost"] = {
                    "model": xgb_model,
                    "metrics": xgb_metrics,
                    "feature_importance": xgb_importance
                }
                print(f"  XGBoost - Val MAE: {xgb_metrics['val_mae']:.2f} bps, R²: {xgb_metrics['val_r2']:.3f}")
        except Exception as e:
            print(f"  XGBoost failed: {e}")
        
        # Train Random Forest
        try:
            rf_model, rf_metrics, rf_importance = train_random_forest_model(
                X_train_final, y_train, X_val, y_val, target_name
            )
            if rf_model:
                target_results["random_forest"] = {
                    "model": rf_model,
                    "metrics": rf_metrics,
                    "feature_importance": rf_importance
                }
                print(f"  Random Forest - Val MAE: {rf_metrics['val_mae']:.2f} bps, R²: {rf_metrics['val_r2']:.3f}")
        except Exception as e:
            print(f"  Random Forest failed: {e}")
        
        # Select best model based on validation MAE
        if target_results:
            best_model_name = min(
                target_results.keys(),
                key=lambda k: target_results[k]["metrics"]["val_mae"]
            )
            target_results["best_model"] = best_model_name
            print(f"  Best model: {best_model_name} (MAE: {target_results[best_model_name]['metrics']['val_mae']:.2f} bps)")
        
        results[target_name] = target_results
    
    return results

def save_models_enhanced(models: Dict[str, Dict], feature_names: List[str], date: str):
    """Save enhanced models with metadata."""
    import pickle
    
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    metadata = {
        "date": date,
        "model_type": "ensemble",
        "targets": TARGETS,
        "feature_names": feature_names,
        "model_info": {}
    }
    
    for target_name, target_models in models.items():
        metadata["model_info"][target_name] = {}
        
        for model_name, model_data in target_models.items():
            if model_name == "best_model":
                continue
            
            # Save model
            model_path = models_dir / f"{model_name}_{target_name}_{date}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model_data["model"], f)
            
            metadata["model_info"][target_name][model_name] = {
                "metrics": model_data["metrics"],
                "feature_importance": model_data["feature_importance"][:10],  # Top 10
                "model_path": str(model_path)
            }
        
        if "best_model" in target_models:
            metadata["model_info"][target_name]["best_model"] = target_models["best_model"]
    
    # Save metadata
    metadata_path = models_dir / f"ensemble_metadata_{date}.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n[SAVE] Models saved to {models_dir}")
    print(f"[SAVE] Metadata saved to {metadata_path}")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Train enhanced ensemble models")
    ap.add_argument("--data", type=str, required=True, help="Training data JSON file")
    ap.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    args = ap.parse_args()
    
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
    
    print(f"[TRAIN] Training ensemble models on {len(X)} examples with {len(feature_names)} features...")
    models = train_models_ensemble(X, y, dates, test_size=args.test_size, use_time_split=True)
    
    if not models:
        print("[ERROR] Model training failed")
        return
    
    # Save models
    date = dt.date.today().isoformat()
    save_models_enhanced(models, feature_names, date)
    
    print("\n[TRAIN] Training complete!")

if __name__ == "__main__":
    main()

