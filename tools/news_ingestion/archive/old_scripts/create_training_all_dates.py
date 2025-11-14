#!/usr/bin/env python3
"""
Create training data using all available yield curve dates.
For dates without news, uses zero/empty features (baseline model).
"""

import os
import sys
import json
import datetime as dt
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from bucket_news import get_bucket_counts, BUCKETS
from analyze_yield_impact import load_curve_snapshot

def get_all_yield_curve_dates() -> List[str]:
    """Get all dates with yield curve data."""
    conn = get_conn()
    dates = [row[0] for row in conn.execute("SELECT date FROM yield_curve_daily ORDER BY date").fetchall()]
    conn.close()
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

def create_training_data_with_all_dates() -> List[Dict]:
    """Create training data for all yield curve dates, using zero features for dates without news."""
    dates = get_all_yield_curve_dates()
    training_data = []
    
    print(f"[COLLECT] Creating training data for {len(dates)} yield curve dates")
    
    for date in dates:
        # Get news buckets (may be empty)
        bucket_counts = get_bucket_counts(date)
        
        # Get actual yield changes
        actual = get_actual_yield_changes(date)
        if not actual:
            continue
        
        # Create features: bucket counts and normalized weights
        # Initialize all buckets to zero
        features = {}
        for bucket in BUCKETS:
            features[f"bucket_{bucket}_count"] = 0.0
            features[f"bucket_{bucket}_weight"] = 0.0
        
        # Fill in actual bucket counts if available
        total_articles = sum(bucket_counts.values())
        for bucket, count in bucket_counts.items():
            features[f"bucket_{bucket}_count"] = float(count)
            features[f"bucket_{bucket}_weight"] = float(count / total_articles) if total_articles > 0 else 0.0
        
        # Add total article count
        features["total_articles"] = float(total_articles)
        
        # Create training example
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
    
    dates_with_news = sum(1 for ex in training_data if ex["features"]["total_articles"] > 0)
    print(f"[COLLECT] Created {len(training_data)} training examples")
    print(f"[COLLECT] Dates with news: {dates_with_news}, Dates without news: {len(training_data) - dates_with_news}")
    
    return training_data

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Create training data using all yield curve dates")
    ap.add_argument("--output", help="Output file path (default: training_data_all_dates.json)")
    args = ap.parse_args()
    
    training_data = create_training_data_with_all_dates()
    
    if not training_data:
        print("[ERROR] No training data created")
        sys.exit(1)
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent / "training_data_all_dates.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(training_data, f, indent=2)
    print(f"[SAVE] Saved {len(training_data)} examples to {output_path}")

if __name__ == "__main__":
    main()

