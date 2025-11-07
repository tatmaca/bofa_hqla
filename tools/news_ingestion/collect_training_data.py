#!/usr/bin/env python3
"""
Historical Data Collection for Model Training
Collects LLM predictions and actual yield curve movements for training.
"""

import os
import json
import sqlite3
import datetime as dt
from datetime import timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import get_conn
from bucket_news import get_bucket_counts, BUCKETS
from analyze_yield_impact import load_curve_snapshot, extract_llm_features

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
ANALYSES_DIR = Path(__file__).parent / "analyses"
SNAPSHOTS_DIR = Path(__file__).parent.parent.parent / "tools" / "ust_curve" / "llm" / "snapshots"

def get_available_dates(start_date: str, end_date: str) -> List[str]:
    """Get list of dates between start and end (business days only)."""
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    dates = []
    current = start
    while current <= end:
        # Skip weekends (basic - could enhance with holiday calendar)
        if current.weekday() < 5:  # Monday=0, Friday=4
            dates.append(current.isoformat())
        current += timedelta(days=1)
    
    return dates

def get_llm_prediction(date: str) -> Optional[Dict]:
    """Load LLM prediction from analysis file."""
    analysis_path = ANALYSES_DIR / f"yield_impact_{date}.json"
    if not analysis_path.exists():
        return None
    
    try:
        with open(analysis_path) as f:
            data = json.load(f)
        return data.get("analysis", {})
    except Exception as e:
        print(f"[WARN] Failed to load LLM prediction for {date}: {e}")
        return None

def get_actual_yield_changes(date: str) -> Optional[Dict]:
    """Get actual yield curve changes from snapshot."""
    snapshot_path = SNAPSHOTS_DIR / f"curve_snapshot_{date}.json"
    if not snapshot_path.exists():
        return None
    
    try:
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        
        delta = snapshot.get("delta", {})
        zeros = delta.get("zeros_pct", {})
        spreads = delta.get("spreads_pct", {})
        
        return {
            "2y": zeros.get("2y", 0.0),
            "5y": zeros.get("5y", 0.0),
            "10y": zeros.get("10y", 0.0),
            "30y": zeros.get("30y", 0.0),
            "2s10s": spreads.get("2s10s", 0.0),
            "2s30s": spreads.get("2s30s", 0.0),
        }
    except Exception as e:
        print(f"[WARN] Failed to load actual changes for {date}: {e}")
        return None

def extract_llm_features(prediction: Dict) -> Dict[str, float]:
    """Extract features from LLM prediction."""
    features = {}
    predictions = prediction.get("predictions", {})
    spreads = prediction.get("spreads", {})
    
    # Extract magnitude and direction for each tenor/spread
    for tenor in ["2y", "5y", "10y", "30y"]:
        pred = predictions.get(tenor, {})
        magnitude = pred.get("magnitude_bps", 0.0)
        direction = pred.get("direction", "flat")
        
        # Convert direction to numeric: up=1, down=-1, flat=0
        dir_val = 1.0 if direction == "up" else (-1.0 if direction == "down" else 0.0)
        
        features[f"{tenor}_pred_magnitude"] = float(magnitude)
        features[f"{tenor}_pred_direction"] = dir_val
        features[f"{tenor}_pred_signed"] = float(magnitude) * dir_val  # Signed magnitude
    
    for spread in ["2s10s", "2s30s"]:
        spred = spreads.get(spread, {})
        magnitude = spred.get("magnitude_bps", 0.0)
        direction = spred.get("direction", "flat")
        
        dir_val = 1.0 if direction == "steepen" else (-1.0 if direction == "flatten" else 0.0)
        
        features[f"{spread}_pred_magnitude"] = float(magnitude)
        features[f"{spread}_pred_direction"] = dir_val
        features[f"{spread}_pred_signed"] = float(magnitude) * dir_val
    
    return features

def collect_training_data(start_date: str, end_date: str) -> List[Dict]:
    """Collect training data for date range."""
    dates = get_available_dates(start_date, end_date)
    training_data = []
    
    print(f"[COLLECT] Collecting data for {len(dates)} dates from {start_date} to {end_date}")
    
    for date in dates:
        # Get news buckets
        bucket_counts = get_bucket_counts(date)
        if not bucket_counts:
            continue
        
        # Get LLM prediction
        llm_pred = get_llm_prediction(date)
        if not llm_pred:
            continue
        
        # Get actual yield changes
        actual = get_actual_yield_changes(date)
        if not actual:
            continue
        
        # Extract features
        llm_features = extract_llm_features(llm_pred)
        
        # Build feature vector: bucket counts + LLM predictions
        features = {}
        
        # News bucket features
        total_articles = sum(bucket_counts.values())
        for bucket in BUCKETS:
            count = bucket_counts.get(bucket, 0)
            weight = count / total_articles if total_articles > 0 else 0.0
            features[f"{bucket}_count"] = count
            features[f"{bucket}_weight"] = weight
        
        # Add LLM prediction features
        features.update(llm_features)
        
        # Store training example
        training_data.append({
            "date": date,
            "features": features,
            "actual": actual,
            "llm_prediction": llm_pred
        })
    
    print(f"[COLLECT] Collected {len(training_data)} complete training examples")
    return training_data

def save_training_data(training_data: List[Dict], output_path: Path):
    """Save training data to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(training_data, f, indent=2)
    print(f"[SAVE] Saved {len(training_data)} examples to {output_path}")

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Collect historical training data")
    ap.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--output", type=str, help="Output file path", 
                   default="training_data_historical.json")
    args = ap.parse_args()
    
    end_date = args.end_date or dt.date.today().isoformat()
    
    training_data = collect_training_data(args.start_date, end_date)
    
    if not training_data:
        print("[ERROR] No training data collected")
        return
    
    output_path = Path(__file__).parent / args.output
    save_training_data(training_data, output_path)
    
    print(f"\n[COLLECT] Summary:")
    print(f"  Dates: {args.start_date} to {end_date}")
    print(f"  Examples: {len(training_data)}")
    print(f"  Features per example: {len(training_data[0]['features'])}")
    print(f"  Output: {output_path}")

if __name__ == "__main__":
    main()

