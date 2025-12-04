#!/usr/bin/env python3
"""
Model-Based Prediction Enhancement
Uses trained XGBoost models to improve LLM predictions.
"""

import os
import json
import numpy as np
from typing import Dict, Optional
from pathlib import Path
import pickle
import datetime as dt

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except (ImportError, AttributeError) as e:
    HAS_XGBOOST = False
    xgb = None
    print(f"[WARN] XGBoost not available: {e}")

from bucket_news import get_bucket_counts, BUCKETS
from analyze_yield_impact import analyze_yield_impact, get_bucketed_news, load_curve_snapshot, extract_llm_features

MODEL_DIR = Path(__file__).parent / "models"
TENORS = ["2y", "5y", "10y", "30y"]
SPREADS = ["2s10s", "2s30s"]
TARGETS = TENORS + SPREADS

def load_latest_xgb_models() -> Optional[Dict]:
    """Load the most recent XGBoost models."""
    metadata_files = sorted(MODEL_DIR.glob("xgb_metadata_*.json"), reverse=True)
    if not metadata_files:
        return None
    
    latest_metadata_path = metadata_files[0]
    with open(latest_metadata_path) as f:
        metadata = json.load(f)
    
    date = metadata["date"]
    feature_names = metadata["feature_names"]
    models = {}
    
    for target in metadata["targets"]:
        model_path = MODEL_DIR / f"xgb_{target}_{date}.pkl"
        if model_path.exists():
            with open(model_path, "rb") as f:
                models[target] = pickle.load(f)
    
    return {
        "models": models,
        "feature_names": feature_names,
        "date": date
    }

def prepare_features(date: str, llm_prediction: Dict) -> Optional[np.ndarray]:
    """Prepare feature vector for model prediction."""
    # Get news buckets
    bucket_counts = get_bucket_counts(date)
    if not bucket_counts:
        return None
    
    # Extract LLM features
    llm_features = extract_llm_features(llm_prediction)
    
    # Build feature vector
    total_articles = sum(bucket_counts.values())
    features = {}
    
    # News bucket features
    for bucket in BUCKETS:
        count = bucket_counts.get(bucket, 0)
        weight = count / total_articles if total_articles > 0 else 0.0
        features[f"{bucket}_count"] = count
        features[f"{bucket}_weight"] = weight
    
    # Add LLM prediction features
    features.update(llm_features)
    
    # Load model metadata to get feature order
    model_data = load_latest_xgb_models()
    if not model_data:
        return None
    
    feature_names = model_data["feature_names"]
    
    # Build feature vector in correct order
    feature_vec = np.array([features.get(name, 0.0) for name in feature_names])
    
    return feature_vec

def enhance_prediction(llm_prediction: Dict, date: str) -> Dict:
    """Enhance LLM prediction using trained XGBoost models."""
    if not HAS_XGBOOST:
        return llm_prediction
    
    model_data = load_latest_xgb_models()
    if not model_data:
        print("[WARN] No XGBoost models found. Using LLM prediction as-is.")
        return llm_prediction
    
    # Prepare features
    features = prepare_features(date, llm_prediction)
    if features is None:
        return llm_prediction
    
    # Get model predictions
    models = model_data["models"]
    enhanced_predictions = {}
    enhanced_spreads = {}
    
    for target in TARGETS:
        if target not in models:
            continue
        
        model = models[target]
        pred = model.predict(features.reshape(1, -1))[0]
        
        if target in TENORS:
            enhanced_predictions[target] = {
                "direction": "up" if pred > 0.5 else ("down" if pred < -0.5 else "flat"),
                "magnitude_bps": float(pred),
                "reasoning": f"XGBoost-enhanced prediction based on historical patterns"
            }
        else:
            enhanced_spreads[target] = {
                "direction": "steepen" if pred > 0.5 else ("flatten" if pred < -0.5 else "flat"),
                "magnitude_bps": float(pred),
                "reasoning": f"XGBoost-enhanced prediction based on historical patterns"
            }
    
    # Merge with LLM predictions (XGBoost takes precedence)
    result = llm_prediction.copy()
    if enhanced_predictions:
        result["predictions"] = {**result.get("predictions", {}), **enhanced_predictions}
    if enhanced_spreads:
        result["spreads"] = {**result.get("spreads", {}), **enhanced_spreads}
    
    result["enhancement_method"] = "xgboost"
    result["model_date"] = model_data["date"]
    
    return result

def predict_with_enhancement(date: str, use_llm: bool = True) -> Dict:
    """Get enhanced prediction for a date."""
    # Get LLM prediction
    if use_llm:
        bucketed_news = get_bucketed_news(date)
        current_curve = load_curve_snapshot(date)
        llm_pred = analyze_yield_impact(bucketed_news, current_curve)
    else:
        # Load from saved analysis
        analysis_path = Path(__file__).parent / "analyses" / f"yield_impact_{date}.json"
        if analysis_path.exists():
            with open(analysis_path) as f:
                data = json.load(f)
            llm_pred = data.get("analysis", {})
        else:
            return {"error": "No LLM prediction found"}
    
    # Enhance with XGBoost
    enhanced = enhance_prediction(llm_pred, date)
    
    return {
        "date": date,
        "llm_prediction": llm_pred,
        "enhanced_prediction": enhanced,
        "enhancement_applied": HAS_XGBOOST and load_latest_xgb_models() is not None
    }

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Get enhanced yield curve prediction")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--no-llm", action="store_true", help="Don't call LLM, use saved prediction")
    args = ap.parse_args()
    
    date = args.date or dt.date.today().isoformat()
    
    result = predict_with_enhancement(date, use_llm=not args.no_llm)
    
    if "error" in result:
        print(f"[ERROR] {result['error']}")
        return
    
    print(f"\n=== ENHANCED PREDICTION FOR {date} ===\n")
    
    if result["enhancement_applied"]:
        print("Using XGBoost-enhanced predictions:\n")
        enhanced = result["enhanced_prediction"]
        
        print("Tenor Predictions:")
        for tenor, pred in enhanced.get("predictions", {}).items():
            print(f"  {tenor}: {pred['direction']} {pred['magnitude_bps']:.2f}bps")
        
        print("\nSpread Predictions:")
        for spread, pred in enhanced.get("spreads", {}).items():
            print(f"  {spread}: {pred['direction']} {pred['magnitude_bps']:.2f}bps")
    else:
        print("Using LLM predictions (no XGBoost enhancement available):\n")
        llm = result["llm_prediction"]
        
        print("Tenor Predictions:")
        for tenor, pred in llm.get("predictions", {}).items():
            print(f"  {tenor}: {pred['direction']} {pred['magnitude_bps']:.2f}bps")
    
    # Save enhanced prediction
    output_path = Path(__file__).parent / "analyses" / f"enhanced_yield_impact_{date}.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[SAVE] Saved to {output_path}")

if __name__ == "__main__":
    main()

