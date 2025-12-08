#!/usr/bin/env python3
"""
Collect Training Data with Time Series Lag Features
Creates training examples with news from t-n affecting yields at t.
"""

import os
import json
import datetime as dt
from datetime import timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from bucket_news import get_bucket_counts, BUCKETS
from analyze_yield_impact import load_curve_snapshot, extract_llm_features
from lookahead_bias_utils import get_market_close_time, is_article_before_market_close

ANALYSES_DIR = Path(__file__).parent / "analyses"
SNAPSHOTS_DIR = Path(__file__).parent.parent.parent / "tools" / "ust_curve" / "llm" / "snapshots"

def get_available_dates(start_date: str, end_date: str) -> List[str]:
    """Get list of business days between start and end."""
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Business day
            dates.append(current.isoformat())
        current += timedelta(days=1)
    
    return dates

def get_bucket_counts_with_lag(date: str, lag_days: int = 0) -> Dict[str, int]:
    """
    Get bucket counts for a date with optional lag.
    
    Args:
        date: Target date (date of yield change)
        lag_days: How many days before (0 = same day, 1 = t-1, etc.)
    
    Returns:
        Dict of bucket counts
    """
    if lag_days == 0:
        return get_bucket_counts(date)
    
    # Calculate news date (lag days before target date)
    target_date = dt.datetime.strptime(date, "%Y-%m-%d").date()
    news_date = target_date - timedelta(days=lag_days)
    
    # Skip if news date is not a business day or is in the future
    if news_date.weekday() >= 5 or news_date > dt.date.today():
        return {}
    
    return get_bucket_counts(news_date.isoformat())

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
            "2y": zeros.get("2y", 0.0) * 100,  # Convert to bps
            "5y": zeros.get("5y", 0.0) * 100,
            "10y": zeros.get("10y", 0.0) * 100,
            "30y": zeros.get("30y", 0.0) * 100,
            "2s10s": spreads.get("2s10s", 0.0) * 100,
            "2s30s": spreads.get("2s30s", 0.0) * 100,
        }
    except Exception as e:
        print(f"[WARN] Failed to load actual changes for {date}: {e}")
        return None

def collect_training_data_with_lags(start_date: str, end_date: str, 
                                   max_lag_days: int = 3) -> List[Dict]:
    """
    Collect training data with time series lag features.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_lag_days: Maximum lag to include (0 = same day, 1 = t-1, etc.)
    
    Returns:
        List of training examples with lag features
    """
    dates = get_available_dates(start_date, end_date)
    training_data = []
    
    print(f"[COLLECT] Collecting data with lags (max_lag={max_lag_days}) for {len(dates)} dates")
    
    missing_news = []
    missing_llm = []
    missing_snapshots = []
    
    for date in dates:
        # Get actual yield changes (ground truth)
        actual_changes = get_actual_yield_changes(date)
        if not actual_changes:
            missing_snapshots.append(date)
            continue
        
        # Get LLM prediction for this date
        llm_pred = get_llm_prediction(date)
        if not llm_pred:
            missing_llm.append(date)
        
        # Build features with lags
        features = {}
        
        # Add lag features (t-0, t-1, t-2, etc.)
        for lag in range(max_lag_days + 1):
            lag_suffix = f"_lag{lag}" if lag > 0 else ""
            
            # Get bucket counts for this lag
            bucket_counts = get_bucket_counts_with_lag(date, lag_days=lag)
            
            if not bucket_counts and lag == 0:
                # No news for same day - skip this example
                missing_news.append(date)
                break
            
            total_articles = sum(bucket_counts.values())
            
            # Add bucket features for this lag
            for bucket in BUCKETS:
                count = bucket_counts.get(bucket, 0)
                weight = count / total_articles if total_articles > 0 else 0.0
                features[f"bucket_{bucket}_count{lag_suffix}"] = count
                features[f"bucket_{bucket}_weight{lag_suffix}"] = weight
            
            features[f"total_articles{lag_suffix}"] = total_articles
        
        # If we broke due to missing news, continue to next date
        if date in missing_news:
            continue
        
        # Add LLM prediction features (from same day only)
        if llm_pred:
            llm_features = extract_llm_features(llm_pred)
            for key, value in llm_features.items():
                features[f"llm_{key}"] = value
        else:
            # Add zero features if no LLM prediction
            for target in ["2y", "5y", "10y", "30y", "2s10s", "2s30s"]:
                features[f"llm_{target}_magnitude"] = 0.0
                features[f"llm_{target}_direction_up"] = 0.0
                features[f"llm_{target}_direction_down"] = 0.0
                features[f"llm_{target}_signed"] = 0.0
        
        # Create training example
        example = {
            "date": date,
            "features": features,
            "targets": {
                "2y": actual_changes["2y"],
                "5y": actual_changes["5y"],
                "10y": actual_changes["10y"],
                "30y": actual_changes["30y"],
                "2s10s": actual_changes["2s10s"],
                "2s30s": actual_changes["2s30s"],
            }
        }
        
        training_data.append(example)
    
    print(f"[COLLECT] Collected {len(training_data)} complete training examples")
    if missing_news:
        print(f"[COLLECT] Missing news buckets: {len(missing_news)} dates")
    if missing_llm:
        print(f"[COLLECT] Missing LLM predictions: {len(missing_llm)} dates")
    if missing_snapshots:
        print(f"[COLLECT] Missing yield snapshots: {len(missing_snapshots)} dates")
    
    return training_data

def save_training_data_lagged(training_data: List[Dict], output_path: Path):
    """Save training data with lag features to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(training_data, f, indent=2)
    print(f"[SAVE] Saved {len(training_data)} examples to {output_path}")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Collect training data with time series lag features")
    ap.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    ap.add_argument("--max-lag", type=int, default=3, help="Maximum lag days (default: 3)")
    ap.add_argument("--output", type=str, help="Output JSON file path")
    args = ap.parse_args()
    
    training_data = collect_training_data_with_lags(
        args.start_date, 
        args.end_date,
        max_lag_days=args.max_lag
    )
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent / f"training_data_lagged_{args.start_date}_{args.end_date}.json"
    
    save_training_data_lagged(training_data, output_path)

if __name__ == "__main__":
    main()

