#!/usr/bin/env python3
"""
Catch-Up Script for Missing Data
Checks for missing news/yield curve data (up to 7 days back) and fills them in.
"""

import os
import sys
import json
import datetime as dt
from datetime import timedelta
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import get_conn, init_db
from analyze_yield_impact import (
    get_bucketed_news, analyze_yield_impact, load_curve_snapshot, 
    save_analysis, load_curve_snapshot as load_snapshot
)
from daily_pipeline import sync_yield_curve_data

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS_DIR = REPO_ROOT / "tools" / "ust_curve" / "llm" / "snapshots"
ANALYSES_DIR = Path(__file__).parent / "analyses"
AUTO_SNAPSHOT_SCRIPT = REPO_ROOT / "tools" / "ust_curve" / "llm" / "auto_snapshot.py"
BUILD_SNAPSHOT_SCRIPT = REPO_ROOT / "tools" / "ust_curve" / "llm" / "build_snapshots.py"

def is_business_day(date):
    """Check if a date is a business day (Monday-Friday)."""
    return date.weekday() < 5

def get_date_range(days_back=7):
    """Get list of business days going back N days from today."""
    today = dt.date.today()
    dates = []
    current = today
    
    # Go back up to days_back days, but only include business days
    for _ in range(days_back * 2):  # Check more days to account for weekends
        if is_business_day(current):
            dates.append(current.isoformat())
        if len(dates) >= days_back:
            break
        current -= timedelta(days=1)
    
    return sorted(dates)

def check_missing_snapshots(dates):
    """Check which yield curve snapshots are missing."""
    missing = []
    for date in dates:
        snapshot_path = SNAPSHOTS_DIR / f"curve_snapshot_{date}.json"
        if not snapshot_path.exists():
            missing.append(date)
    return missing

def check_missing_analyses(dates):
    """Check which news analyses are missing."""
    missing = []
    for date in dates:
        analysis_path = ANALYSES_DIR / f"yield_impact_{date}.json"
        if not analysis_path.exists():
            missing.append(date)
    return missing

def generate_snapshot(date_str):
    """Generate yield curve snapshot for a date."""
    print(f"\n[GENERATE] Creating snapshot for {date_str}...")
    
    # Try auto_snapshot first (handles data availability checks)
    if AUTO_SNAPSHOT_SCRIPT.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(AUTO_SNAPSHOT_SCRIPT), 
                 "--target-date", date_str, "--skip-plot", "--skip-summary", "--skip-sync"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print(f"[OK] Snapshot generated via auto_snapshot for {date_str}")
                return True
            else:
                # If auto_snapshot fails, try direct build_snapshots
                print(f"[INFO] Auto-snapshot failed, trying direct build...")
        except Exception as e:
            print(f"[WARN] Auto-snapshot error: {e}, trying direct build...")
    
    # Fallback: direct build_snapshots call
    if BUILD_SNAPSHOT_SCRIPT.exists():
        try:
            venv_python = REPO_ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = sys.executable
            
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{REPO_ROOT}/tools/ust_curve:{REPO_ROOT}:{env.get('PYTHONPATH', '')}"
            
            result = subprocess.run(
                [str(venv_python), str(BUILD_SNAPSHOT_SCRIPT), 
                 "--core-module", "tools.ust_curve.curves", date_str],
                cwd=str(REPO_ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"[OK] Snapshot generated for {date_str}")
                return True
            else:
                print(f"[ERROR] Failed to generate snapshot: {result.stderr[:200]}")
                return False
        except subprocess.TimeoutExpired:
            print(f"[ERROR] Timeout generating snapshot for {date_str}")
            return False
        except Exception as e:
            print(f"[ERROR] Exception generating snapshot: {e}")
            return False
    
    print(f"[ERROR] Snapshot generation scripts not found")
    return False

def generate_analysis(date_str):
    """Generate news analysis for a date."""
    print(f"\n[GENERATE] Creating analysis for {date_str}...")
    
    try:
        # Get bucketed news
        bucketed_news = get_bucketed_news(date_str)
        if not bucketed_news:
            print(f"[SKIP] No bucketed news found for {date_str}")
            return False
        
        # Load current curve snapshot
        current_curve = load_snapshot(date_str)
        if not current_curve:
            print(f"[WARN] No yield curve snapshot for {date_str}, analysis may be limited")
        
        # Generate analysis
        analysis = analyze_yield_impact(bucketed_news, current_curve)
        
        # Save analysis
        save_analysis(date_str, analysis, bucketed_news)
        print(f"[OK] Analysis generated for {date_str}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to generate analysis for {date_str}: {e}")
        import traceback
        traceback.print_exc()
        return False

def sync_snapshot_to_db(date_str):
    """Sync snapshot to database."""
    try:
        sync_yield_curve_data(date_str)
        return True
    except Exception as e:
        print(f"[WARN] Failed to sync {date_str} to database: {e}")
        return False

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Catch up on missing news/yield curve data (up to 7 days back)"
    )
    ap.add_argument("--days-back", type=int, default=7, 
                    help="Number of days to look back (default: 7)")
    ap.add_argument("--skip-snapshots", action="store_true",
                    help="Skip generating missing snapshots")
    ap.add_argument("--skip-analyses", action="store_true",
                    help="Skip generating missing analyses")
    ap.add_argument("--skip-sync", action="store_true",
                    help="Skip syncing to database")
    args = ap.parse_args()
    
    print(f"\n{'='*70}")
    print(f"CATCH-UP: Missing Data Check")
    print(f"{'='*70}")
    print(f"Looking back: {args.days_back} days")
    print(f"{'='*70}\n")
    
    # Ensure directories exist
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize database if needed
    try:
        init_db()
        print("[OK] Database initialized/verified")
    except Exception as e:
        print(f"[WARN] Database initialization issue: {e}")
    
    # Get date range
    dates = get_date_range(args.days_back)
    print(f"[INFO] Checking {len(dates)} business days: {dates[0]} to {dates[-1]}\n")
    
    # Check for missing snapshots
    missing_snapshots = []
    if not args.skip_snapshots:
        missing_snapshots = check_missing_snapshots(dates)
        if missing_snapshots:
            print(f"[FOUND] {len(missing_snapshots)} missing yield curve snapshots:")
            for date in missing_snapshots:
                print(f"  - {date}")
        else:
            print("[OK] All yield curve snapshots exist")
    else:
        print("[SKIP] Snapshot check skipped")
    
    # Check for missing analyses
    missing_analyses = []
    if not args.skip_analyses:
        missing_analyses = check_missing_analyses(dates)
        if missing_analyses:
            print(f"\n[FOUND] {len(missing_analyses)} missing news analyses:")
            for date in missing_analyses:
                print(f"  - {date}")
        else:
            print("\n[OK] All news analyses exist")
    else:
        print("\n[SKIP] Analysis check skipped")
    
    # Generate missing snapshots
    snapshot_results = {"success": 0, "failed": 0}
    if missing_snapshots and not args.skip_snapshots:
        print(f"\n{'='*70}")
        print(f"GENERATING MISSING SNAPSHOTS ({len(missing_snapshots)} dates)")
        print(f"{'='*70}")
        
        for date in missing_snapshots:
            if generate_snapshot(date):
                snapshot_results["success"] += 1
                # Sync to database
                if not args.skip_sync:
                    sync_snapshot_to_db(date)
            else:
                snapshot_results["failed"] += 1
    
    # Generate missing analyses
    analysis_results = {"success": 0, "failed": 0, "skipped": 0}
    if missing_analyses and not args.skip_analyses:
        print(f"\n{'='*70}")
        print(f"GENERATING MISSING ANALYSES ({len(missing_analyses)} dates)")
        print(f"{'='*70}")
        
        for date in missing_analyses:
            # Check if snapshot exists (analysis needs it)
            snapshot_path = SNAPSHOTS_DIR / f"curve_snapshot_{date}.json"
            if not snapshot_path.exists():
                print(f"[SKIP] Analysis for {date} skipped - no snapshot available")
                analysis_results["skipped"] += 1
                continue
            
            if generate_analysis(date):
                analysis_results["success"] += 1
            else:
                analysis_results["failed"] += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    
    if not args.skip_snapshots:
        print(f"Snapshots:")
        print(f"  - Missing found: {len(missing_snapshots)}")
        print(f"  - Generated: {snapshot_results['success']}")
        print(f"  - Failed: {snapshot_results['failed']}")
    
    if not args.skip_analyses:
        print(f"\nAnalyses:")
        print(f"  - Missing found: {len(missing_analyses)}")
        print(f"  - Generated: {analysis_results['success']}")
        print(f"  - Failed: {analysis_results['failed']}")
        print(f"  - Skipped (no snapshot): {analysis_results['skipped']}")
    
    print(f"{'='*70}\n")
    
    # Return appropriate exit code
    total_failed = snapshot_results.get("failed", 0) + analysis_results.get("failed", 0)
    if total_failed > 0:
        print(f"[WARN] Some operations failed. Check logs above.")
        return 1
    else:
        print(f"[OK] Catch-up completed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())

