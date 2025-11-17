#!/usr/bin/env python3
"""
ML Model Framework for News-to-Yield-Curve Prediction
Trains models to map news bucket features to yield curve changes.
"""

import os
import json
import sqlite3
import datetime as dt
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARN] scikit-learn not installed. Install with: pip install scikit-learn")

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

TENORS = ["2y", "5y", "10y", "30y"]
SPREADS = ["2s10s", "2s30s"]
BUCKETS = [
    "monetary_policy",
    "economic_data",
    "geopolitical_events",
    "market_sentiment",
    "fiscal_policy",
    "credit_events",
    "commodity_prices",
    "other_general"
]

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def prepare_training_data(min_days: int = 7) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Prepare training data from database.
    Returns (X_features, y_targets_dict)
    """
    with get_conn() as c:
        # Get yield curve data
        curve_rows = c.execute("""
            SELECT date, delta_zeros_pct, delta_spreads_pct
            FROM yield_curve_daily
            WHERE delta_zeros_pct IS NOT NULL
            ORDER BY date
        """).fetchall()
        
        # Get news bucket data
        news_rows = c.execute("""
            SELECT date, bucket, bucket_count, bucket_weight
            FROM news_yield_training
            ORDER BY date
        """).fetchall()
    
    # Build date-indexed dictionaries
    curve_data = {}
    for row in curve_rows:
        date = row["date"]
        try:
            delta_zeros = json.loads(row["delta_zeros_pct"])
            delta_spreads = json.loads(row["delta_spreads_pct"])
            curve_data[date] = {
                "zeros": delta_zeros,
                "spreads": delta_spreads
            }
        except:
            continue
    
    news_data = {}
    for row in news_rows:
        date = row["date"]
        if date not in news_data:
            news_data[date] = {}
        news_data[date][row["bucket"]] = {
            "count": row["bucket_count"],
            "weight": row["bucket_weight"]
        }
    
    # Align dates and build feature/target arrays
    common_dates = sorted(set(curve_data.keys()) & set(news_data.keys()))
    
    if len(common_dates) < min_days:
        print(f"[WARN] Only {len(common_dates)} days of aligned data (need {min_days})")
        return None, {}
    
    # Build features: bucket counts and weights for each date
    X = []
    y = {tenor: [] for tenor in TENORS + SPREADS}
    dates_used = []
    
    for date in common_dates:
        # Features: bucket counts and weights
        features = []
        bucket_counts = news_data[date]
        for bucket in BUCKETS:
            if bucket in bucket_counts:
                features.append(bucket_counts[bucket]["count"])
                features.append(bucket_counts[bucket]["weight"])
            else:
                features.extend([0, 0.0])
        
        # Targets: yield changes
        zeros = curve_data[date]["zeros"]
        spreads = curve_data[date]["spreads"]
        
        # Extract targets
        targets = {}
        for tenor in TENORS:
            targets[tenor] = zeros.get(tenor, 0.0)
        for spread in SPREADS:
            targets[spread] = spreads.get(spread, 0.0)
        
        X.append(features)
        for key in TENORS + SPREADS:
            y[key].append(targets[key])
        dates_used.append(date)
    
    X = np.array(X)
    y = {k: np.array(v) for k, v in y.items()}
    
    print(f"[TRAIN] Prepared {len(X)} samples from {len(common_dates)} days")
    return X, y

def train_models(X: np.ndarray, y: Dict[str, np.ndarray], 
                test_size: float = 0.2) -> Dict[str, Dict]:
    """
    Train models for each target (tenor/spread).
    Returns dict of {target: {model, scaler, metrics}}
    """
    if not HAS_SKLEARN:
        print("[ERROR] scikit-learn required for training")
        return {}
    
    results = {}
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    for target_name, target_values in y.items():
        print(f"\n[TRAIN] Training model for {target_name}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, target_values, test_size=test_size, random_state=42
        )
        
        # Try multiple models
        models = {
            "ridge": Ridge(alpha=1.0),
            "lasso": Lasso(alpha=0.1),
            "rf": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            "gb": GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        }
        
        best_model = None
        best_score = float('-inf')
        best_name = None
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)  # R² score
            
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            print(f"  {name}: R²={score:.3f}, MSE={mse:.4f}, MAE={mae:.4f}")
            
            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
        
        # Cross-validation on full dataset
        cv_scores = cross_val_score(best_model, X_scaled, target_values, cv=5, scoring='r2')
        
        results[target_name] = {
            "model": best_model,
            "scaler": scaler,
            "model_name": best_name,
            "r2_score": best_score,
            "cv_r2_mean": cv_scores.mean(),
            "cv_r2_std": cv_scores.std(),
            "feature_names": [f"{b}_count" for b in BUCKETS] + [f"{b}_weight" for b in BUCKETS]
        }
        
        print(f"  Best: {best_name} (R²={best_score:.3f}, CV R²={cv_scores.mean():.3f}±{cv_scores.std():.3f})")
    
    return results

def save_models(models: Dict[str, Dict], date: str):
    """Save trained models to disk."""
    for target_name, model_info in models.items():
        model_path = MODEL_DIR / f"model_{target_name}_{date}.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model_info, f)
        print(f"[SAVE] Saved {target_name} model to {model_path}")
    
    # Save metadata
    metadata = {
        "date": date,
        "targets": list(models.keys()),
        "model_info": {
            target: {
                "model_name": info["model_name"],
                "r2_score": float(info["r2_score"]),
                "cv_r2_mean": float(info["cv_r2_mean"]),
                "cv_r2_std": float(info["cv_r2_std"])
            }
            for target, info in models.items()
        }
    }
    
    metadata_path = MODEL_DIR / f"metadata_{date}.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_path

def load_latest_models() -> Optional[Dict[str, Dict]]:
    """Load the most recent trained models."""
    metadata_files = sorted(MODEL_DIR.glob("metadata_*.json"), reverse=True)
    if not metadata_files:
        return None
    
    latest_metadata_path = metadata_files[0]
    with open(latest_metadata_path) as f:
        metadata = json.load(f)
    
    date = metadata["date"]
    models = {}
    
    for target in metadata["targets"]:
        model_path = MODEL_DIR / f"model_{target}_{date}.pkl"
        if model_path.exists():
            with open(model_path, "rb") as f:
                models[target] = pickle.load(f)
    
    return models

def predict_yield_changes(bucket_features: np.ndarray, models: Dict[str, Dict]) -> Dict[str, float]:
    """Predict yield changes from bucket features."""
    if not models:
        return {}
    
    # Use scaler from first model (they should all use the same scaler)
    scaler = list(models.values())[0]["scaler"]
    X_scaled = scaler.transform(bucket_features.reshape(1, -1))
    
    predictions = {}
    for target_name, model_info in models.items():
        model = model_info["model"]
        pred = model.predict(X_scaled)[0]
        predictions[target_name] = float(pred)
    
    return predictions

def prepare_daily_features(date: str) -> Optional[np.ndarray]:
    """Prepare feature vector for a given date from news buckets."""
    with get_conn() as c:
        rows = c.execute("""
            SELECT bucket, COUNT(*) as count
            FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
              AND bucket IS NOT NULL
            GROUP BY bucket
        """, (date,)).fetchall()
    
    bucket_counts = {row["bucket"]: row["count"] for row in rows}
    total = sum(bucket_counts.values())
    
    if total == 0:
        return None
    
    # Build feature vector: counts and normalized weights
    features = []
    for bucket in BUCKETS:
        count = bucket_counts.get(bucket, 0)
        weight = count / total if total > 0 else 0.0
        features.extend([count, weight])
    
    return np.array(features)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Train ML models for yield curve prediction")
    ap.add_argument("--min-days", type=int, default=7, help="Minimum days of data required")
    ap.add_argument("--test-size", type=float, default=0.2, help="Test set size")
    args = ap.parse_args()
    
    if not HAS_SKLEARN:
        print("[ERROR] scikit-learn is required. Install with: pip install scikit-learn")
        return
    
    print("[TRAIN] Preparing training data...")
    X, y = prepare_training_data(min_days=args.min_days)
    
    if X is None or len(X) == 0:
        print("[ERROR] Insufficient training data")
        return
    
    print(f"[TRAIN] Training models on {len(X)} samples...")
    models = train_models(X, y, test_size=args.test_size)
    
    if not models:
        print("[ERROR] Model training failed")
        return
    
    date = dt.date.today().isoformat()
    save_models(models, date)
    print(f"\n[TRAIN] Training complete. Models saved for {date}")

if __name__ == "__main__":
    main()

