#!/usr/bin/env python3
"""
Daily Pipeline: Complete workflow for news ingestion, bucketing, analysis, and model training
"""

import os
import sys
import json
import yaml
import datetime as dt
from datetime import timezone
from typing import Optional
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn, start_ingestion_run, complete_ingestion_run
from bucket_news import get_bucket_counts
from analyze_yield_impact import get_bucketed_news, analyze_yield_impact, load_curve_snapshot, save_analysis
from train_models import prepare_daily_features, prepare_training_data, train_models, save_models

def get_openai_api_key() -> Optional[str]:
    """Load OpenAI API key from environment or config file."""
    # First try environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Then try config file
    config_path = Path(__file__).parent / "news_config.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
                api_key = cfg.get("openai_api_key")
                if api_key:
                    return api_key
        except Exception as e:
            print(f"[WARN] Failed to load config: {e}")
    
    return None

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
    
    # Step 3: Check for New Yield Curve Data and Generate Snapshot
    print("\n[3/6] Checking for New Yield Curve Data...")
    snapshot_generated = False
    try:
        # Try to generate snapshot for today (or most recent available date)
        repo_root = Path(__file__).resolve().parents[2]
        auto_snapshot_script = repo_root / "tools" / "ust_curve" / "llm" / "auto_snapshot.py"
        
        if auto_snapshot_script.exists():
            result = subprocess.run(
                [sys.executable, str(auto_snapshot_script), "--target-date", date, "--skip-plot", "--skip-summary"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=600,
                check=False
            )
            if result.returncode == 0:
                print(result.stdout)
                snapshot_generated = True
            else:
                print(f"[WARN] Auto-snapshot check failed: {result.stderr}")
        else:
            print("[WARN] Auto-snapshot script not found, skipping automatic snapshot generation")
    except Exception as e:
        print(f"[WARN] Auto-snapshot check failed: {e}")
    
    # Sync Yield Curve Data (for the date we have)
    print("\n[3/6] Syncing Yield Curve Data...")
    # Try to sync for today, but also check for most recent available date
    synced = sync_yield_curve_data(date)
    
    # Also try to sync the most recent available snapshot if today's doesn't exist
    if not synced:
        repo_root = Path(__file__).resolve().parents[2]
        snapshots_dir = repo_root / "tools" / "ust_curve" / "llm" / "snapshots"
        if snapshots_dir.exists():
            snapshot_files = sorted(list(snapshots_dir.glob("curve_snapshot_*.json")))
            if snapshot_files:
                latest_snapshot = snapshot_files[-1]
                latest_date = latest_snapshot.stem.replace("curve_snapshot_", "")
                if latest_date != date:
                    print(f"[INFO] Also syncing most recent snapshot: {latest_date}")
                    sync_yield_curve_data(latest_date)
    
    if snapshot_generated or synced:
        print("[OK] Yield curve data updated successfully")
    else:
        print("[WARN] No yield curve data available for today - may need to wait for market close")
    
    # Step 4: LLM Yield Impact Analysis
    print("\n[4/6] LLM Yield Impact Analysis...")
    try:
        # Load API key
        api_key = get_openai_api_key()
        if not api_key:
            print("[WARN] No OpenAI API key found. Set OPENAI_API_KEY environment variable or add 'openai_api_key' to news_config.yaml")
            print("[WARN] Analysis will use fallback predictions (not suitable for training)")
        
        bucketed_news = get_bucketed_news(date)
        if bucketed_news:
            current_curve = load_curve_snapshot(date)
            # Pass API key explicitly
            analysis = analyze_yield_impact(bucketed_news, current_curve, api_key=api_key)
            
            # Check if analysis used fallback
            predictions = analysis.get("predictions", {})
            if predictions and any("Fallback" in pred.get("reasoning", "") for pred in predictions.values()):
                print("[WARN] Analysis used fallback predictions - API key may be missing or invalid")
            else:
                print("[OK] LLM analysis completed successfully")
            
            save_analysis(date, analysis, bucketed_news)
        else:
            print("[WARN] No bucketed news for analysis")
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
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
    
    # Step 6: Train/Retrain Models (rolling 30-day window)
    print("\n[6/6] Training Models (Rolling 30-Day Window)...")
    try:
        # Use rolling 30-day window for model updates
        from update_models_rolling import update_models_with_rolling_window
        
        # Try with 30 days first, then fall back to smaller windows if needed
        success = False
        for window_days in [30, 14, 7]:
            print(f"[TRAIN] Attempting model training with {window_days}-day window...")
            success = update_models_with_rolling_window(days=window_days, threshold_mae=3.0)
            if success:
                print(f"[SUCCESS] Models trained successfully with {window_days}-day window")
                break
            elif window_days == 7:
                # Last attempt - provide detailed feedback
                print(f"[INFO] Model training requires at least 7 days of complete training data")
                print(f"[INFO] Complete data means: news buckets + valid LLM predictions + yield curve snapshots")
                print(f"[INFO] Continue running daily pipeline to accumulate more training data")
        
        if not success:
            print("[INFO] Model update skipped - insufficient data or dependencies")
    except ImportError as e:
        print(f"[INFO] Model training skipped - dependencies not available: {e}")
        print(f"[INFO] Install XGBoost: pip install 'numpy<2.0' xgboost scikit-learn")
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE - {date}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Run daily news-to-yield-curve pipeline")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    args = ap.parse_args()
    
    run_daily_pipeline(args.date)

