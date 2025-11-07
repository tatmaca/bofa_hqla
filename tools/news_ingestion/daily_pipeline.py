#!/usr/bin/env python3
"""
Daily Pipeline: Complete workflow for news ingestion, bucketing, analysis, and model training
"""

import os
import sys
import json
import datetime as dt
from datetime import timezone
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn, start_ingestion_run, complete_ingestion_run
from bucket_news import get_bucket_counts
from analyze_yield_impact import get_bucketed_news, analyze_yield_impact, load_curve_snapshot, save_analysis
from train_models import prepare_daily_features, prepare_training_data, train_models, save_models

def sync_yield_curve_data(date: str):
    """Sync yield curve snapshot data to database."""
    repo_root = Path(__file__).resolve().parents[2]
    snapshot_path = repo_root / "tools" / "ust_curve" / "llm" / "snapshots" / f"curve_snapshot_{date}.json"
    
    if not snapshot_path.exists():
        print(f"[WARN] No yield curve snapshot found for {date}")
        return False
    
    with open(snapshot_path) as f:
        snapshot = json.load(f)
    
    conn = get_conn()
    c = conn.cursor()
    
    # Extract data
    delta_zeros = json.dumps(snapshot.get("delta", {}).get("zeros_pct", {}))
    delta_spreads = json.dumps(snapshot.get("delta", {}).get("spreads_pct", {}))
    zeros = json.dumps(snapshot.get("today", {}).get("zeros_pct", {}))
    spreads = json.dumps(snapshot.get("today", {}).get("spreads_pct", {}))
    
    c.execute("""
        INSERT OR REPLACE INTO yield_curve_daily 
        (date, zeros_pct, spreads_pct, delta_zeros_pct, delta_spreads_pct, snapshot_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, zeros, spreads, delta_zeros, delta_spreads, str(snapshot_path)))
    
    conn.commit()
    conn.close()
    print(f"[SYNC] Synced yield curve data for {date}")
    return True

def prepare_training_record(date: str):
    """Prepare training data record from news buckets and yield curve."""
    bucket_counts = get_bucket_counts(date)
    features = prepare_daily_features(date)
    
    if features is None:
        print(f"[WARN] No news features for {date}")
        return None
    
    # Get yield curve changes
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("""
        SELECT delta_zeros_pct, delta_spreads_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (date,)).fetchone()
    conn.close()
    
    if not row:
        print(f"[WARN] No yield curve data for {date}")
        return None
    
    try:
        delta_zeros = json.loads(row["delta_zeros_pct"])
        delta_spreads = json.loads(row["delta_spreads_pct"])
    except:
        return None
    
    # Calculate total articles and weights
    total_articles = sum(bucket_counts.values())
    
    # Insert training records per bucket
    records = []
    for bucket, count in bucket_counts.items():
        weight = count / total_articles if total_articles > 0 else 0.0
        
        record = {
            "date": date,
            "bucket": bucket,
            "bucket_count": count,
            "bucket_weight": weight,
            "delta_2y": delta_zeros.get("2y", 0.0),
            "delta_5y": delta_zeros.get("5y", 0.0),
            "delta_10y": delta_zeros.get("10y", 0.0),
            "delta_30y": delta_zeros.get("30y", 0.0),
            "delta_2s10s": delta_spreads.get("2s10s", 0.0),
            "delta_2s30s": delta_spreads.get("2s30s", 0.0),
            "created_at": dt.datetime.now(timezone.utc).isoformat()
        }
        records.append(record)
    
    return records

def save_training_records(records: list):
    """Save training records to database."""
    if not records:
        return
    
    conn = get_conn()
    c = conn.cursor()
    
    for record in records:
        c.execute("""
            INSERT OR REPLACE INTO news_yield_training
            (date, bucket, bucket_count, bucket_weight, delta_2y, delta_5y, delta_10y, delta_30y, delta_2s10s, delta_2s30s, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["date"], record["bucket"], record["bucket_count"], record["bucket_weight"],
            record["delta_2y"], record["delta_5y"], record["delta_10y"], record["delta_30y"],
            record["delta_2s10s"], record["delta_2s30s"], record["created_at"]
        ))
    
    conn.commit()
    conn.close()
    print(f"[TRAIN] Saved {len(records)} training records")

def run_daily_pipeline(date: str = None):
    """Run the complete daily pipeline."""
    if date is None:
        date = dt.date.today().isoformat()
    
    print(f"\n{'='*60}")
    print(f"DAILY PIPELINE - {date}")
    print(f"{'='*60}\n")
    
    # Step 1: News Ingestion
    print("[1/6] News Ingestion...")
    run_date = start_ingestion_run(date)
    try:
        result = subprocess.run(
            [sys.executable, "run_ingest.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            # Filter out expected warnings about missing optional dependencies
            stderr_lines = [line for line in result.stderr.split('\n') 
                          if line and 'ModuleNotFoundError' not in line]
            if stderr_lines:
                print('\n'.join(stderr_lines), file=sys.stderr)
        
        # Check if ingestion actually succeeded (look for "Done" in output)
        if result.returncode == 0 or "Done" in result.stdout:
            complete_ingestion_run(run_date, status="completed")
        else:
            complete_ingestion_run(run_date, status="failed", 
                                 error_message=f"Subprocess returned {result.returncode}")
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}", file=sys.stderr)
        complete_ingestion_run(run_date, status="failed", error_message=str(e))
        # Don't return - continue with other steps
    
    # Step 2: News Bucketing
    print("\n[2/6] News Bucketing...")
    try:
        result = subprocess.run(
            [sys.executable, "bucket_news.py", "--hours", "24", "--batch-size", "100"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            # Filter out expected warnings
            stderr_lines = [line for line in result.stderr.split('\n') 
                          if line and 'ModuleNotFoundError' not in line and 'DeprecationWarning' not in line]
            if stderr_lines:
                print('\n'.join(stderr_lines), file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Bucketing failed: {e}", file=sys.stderr)
    
    # Step 3: Sync Yield Curve Data
    print("\n[3/6] Syncing Yield Curve Data...")
    sync_yield_curve_data(date)
    
    # Step 4: LLM Yield Impact Analysis
    print("\n[4/6] LLM Yield Impact Analysis...")
    try:
        bucketed_news = get_bucketed_news(date)
        if bucketed_news:
            current_curve = load_curve_snapshot(date)
            analysis = analyze_yield_impact(bucketed_news, current_curve)
            save_analysis(date, analysis, bucketed_news)
        else:
            print("[WARN] No bucketed news for analysis")
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}", file=sys.stderr)
    
    # Step 5: Prepare Training Data
    print("\n[5/6] Preparing Training Data...")
    try:
        training_records = prepare_training_record(date)
        if training_records:
            save_training_records(training_records)
        else:
            print("[WARN] Could not prepare training records")
    except Exception as e:
        print(f"[ERROR] Training data prep failed: {e}", file=sys.stderr)
    
    # Step 6: Train/Retrain Models (if enough data)
    print("\n[6/6] Training Models...")
    try:
        X, y = prepare_training_data(min_days=7)
        if X is not None and len(X) >= 7:
            models = train_models(X, y, test_size=0.2)
            if models:
                save_models(models, date)
                print("[OK] Models trained successfully")
            else:
                print("[WARN] Model training returned no results")
        else:
            print(f"[INFO] Insufficient data for training ({len(X) if X is not None else 0} samples)")
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}", file=sys.stderr)
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE - {date}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Run daily news-to-yield-curve pipeline")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    args = ap.parse_args()
    
    run_daily_pipeline(args.date)

