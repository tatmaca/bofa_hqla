#!/usr/bin/env python3
"""
Create training data from news buckets and yield curve snapshots.
This version works without LLM predictions - uses only news bucket features.
"""

import os
import sys
import json
import datetime as dt
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from bucket_news import get_bucket_counts
from analyze_yield_impact import load_curve_snapshot

def get_available_dates(start_date: str, end_date: str) -> List[str]:
    """Get business days between start and end dates."""
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Monday-Friday
            dates.append(current.isoformat())
        current += dt.timedelta(days=1)
    return dates

def get_actual_yield_changes(date: str) -> Optional[Dict]:
    """Get actual yield changes from snapshot."""
    snapshot = load_curve_snapshot(date)
    if not snapshot:
        return None
    
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

def collect_training_data_simple(start_date: str, end_date: str) -> List[Dict]:
    """Collect training data using only news buckets and yield curve data."""
    dates = get_available_dates(start_date, end_date)
    training_data = []
    
    print(f"[COLLECT] Collecting data for {len(dates)} dates from {start_date} to {end_date}")
    
    missing_news = []
    missing_snapshots = []
    
    for date in dates:
        # Get news buckets
        bucket_counts = get_bucket_counts(date)
        if not bucket_counts:
            missing_news.append(date)
            continue
        
        # Get actual yield changes
        actual = get_actual_yield_changes(date)
        if not actual:
            missing_snapshots.append(date)
            continue
        
        # Calculate total articles and weights
        total_articles = sum(bucket_counts.values())
        
        # Create features: bucket counts and normalized weights
        features = {}
        for bucket, count in bucket_counts.items():
            features[f"bucket_{bucket}_count"] = float(count)
            features[f"bucket_{bucket}_weight"] = float(count / total_articles) if total_articles > 0 else 0.0
        
        # Add total article count
        features["total_articles"] = float(total_articles)
        
        # Create training example (format compatible with train_xgboost.py)
        example = {
            "date": date,
            "features": features,
            "actual": {
                "delta_2y": actual["2y"],
                "delta_5y": actual["5y"],
                "delta_10y": actual["10y"],
                "delta_30y": actual["30y"],
                "delta_2s10s": actual["2s10s"],
                "delta_2s30s": actual["2s30s"],
            }
        }
        training_data.append(example)
    
    print(f"[COLLECT] Collected {len(training_data)} complete training examples")
    if missing_news:
        print(f"[COLLECT] Missing news buckets: {len(missing_news)} dates")
    if missing_snapshots:
        print(f"[COLLECT] Missing yield snapshots: {len(missing_snapshots)} dates")
    
    return training_data

def save_training_data(training_data: List[Dict], output_path: Path):
    """Save training data to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(training_data, f, indent=2)
    print(f"[SAVE] Saved {len(training_data)} examples to {output_path}")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Collect training data from news buckets and yield curves")
    ap.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    ap.add_argument("--output", help="Output file path (default: training_data_simple_<start>_<end>.json)")
    args = ap.parse_args()
    
    training_data = collect_training_data_simple(args.start_date, args.end_date)
    
    if not training_data:
        print("[ERROR] No training data collected")
        sys.exit(1)
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent / f"training_data_simple_{args.start_date}_{args.end_date}.json"
    
    save_training_data(training_data, output_path)

if __name__ == "__main__":
    main()

