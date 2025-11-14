#!/usr/bin/env python3
"""
Automated Yield Curve Snapshot Generator
Checks for new Treasury data and generates snapshots, summaries, and plots automatically.
Designed to be run daily (e.g., after market close or in the morning).
"""

import os
import sys
import json
import argparse
import datetime as dt
from pathlib import Path
import subprocess

# Get repo root
try:
    import subprocess as sp
    ROOT = Path(sp.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
except:
    ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "ust_curve"))

from tools.ust_curve import run_curve as rc

SNAPSHOTS_DIR = ROOT / "tools" / "ust_curve" / "llm" / "snapshots"
SUMMARIES_DIR = ROOT / "tools" / "ust_curve" / "llm" / "summaries"
PLOTS_DIR = ROOT / "tools" / "ust_curve" / "llm" / "plots"

def get_latest_snapshot_date():
    """Get the date of the most recent snapshot file."""
    if not SNAPSHOTS_DIR.exists():
        return None
    
    snapshot_files = sorted(list(SNAPSHOTS_DIR.glob("curve_snapshot_*.json")))
    if not snapshot_files:
        return None
    
    latest_file = snapshot_files[-1]
    date_str = latest_file.stem.replace("curve_snapshot_", "")
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

def check_new_data_available(target_date=None, lookback_days=5):
    """Check if new Treasury data is available for the target date."""
    if target_date is None:
        target_date = dt.date.today()
    
    # Try to fetch data for target date
    eff_date, par = rc.fetch_with_lookback(target_date, lookback_days=lookback_days)
    
    if not par:
        return None, None
    
    return eff_date, par

def snapshot_exists(date):
    """Check if snapshot already exists for a given date."""
    snapshot_path = SNAPSHOTS_DIR / f"curve_snapshot_{date.isoformat()}.json"
    return snapshot_path.exists()

def generate_snapshot(date_str):
    """Generate snapshot for a specific date."""
    print(f"[SNAPSHOT] Generating snapshot for {date_str}...")
    
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "build_snapshots.py"
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    
    # Use venv python if available, otherwise system python
    if not venv_python.exists():
        venv_python = sys.executable
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    try:
        result = subprocess.run(
            [str(venv_python), str(script_path), "--core-module", "tools.ust_curve.curves", date_str],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"[OK] Snapshot generated for {date_str}")
            return True
        else:
            print(f"[ERROR] Failed to generate snapshot: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout generating snapshot for {date_str}")
        return False
    except Exception as e:
        print(f"[ERROR] Exception generating snapshot: {e}")
        return False

def generate_summary(date_str):
    """Generate summary for a specific date."""
    print(f"[SUMMARY] Generating summary for {date_str}...")
    
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "make_summary.py"
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        venv_python = sys.executable
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    try:
        result = subprocess.run(
            [str(venv_python), str(script_path), "--date", date_str],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"[OK] Summary generated for {date_str}")
            return True
        else:
            print(f"[WARN] Summary generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Exception generating summary: {e}")
        return False

def generate_plot(date_str):
    """Generate plots for a specific date."""
    print(f"[PLOT] Generating plots for {date_str}...")
    
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "plot_snapshot.py"
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        venv_python = sys.executable
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    try:
        result = subprocess.run(
            [str(venv_python), str(script_path), date_str],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"[OK] Plots generated for {date_str}")
            return True
        else:
            print(f"[WARN] Plot generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Exception generating plots: {e}")
        return False

def sync_to_database(date_str):
    """Sync yield curve data to the news ingestion database."""
    print(f"[SYNC] Syncing {date_str} to database...")
    
    try:
        # Change to news_ingestion directory for database access
        news_ingestion_dir = ROOT / "tools" / "news_ingestion"
        original_cwd = os.getcwd()
        
        try:
            os.chdir(str(news_ingestion_dir))
            sys.path.insert(0, str(news_ingestion_dir))
            
            # Initialize database if needed
            try:
                from db import init_db
                init_db()
            except:
                pass
            
            from daily_pipeline import sync_yield_curve_data
            
            if sync_yield_curve_data(date_str):
                print(f"[OK] Synced {date_str} to database")
                return True
            else:
                print(f"[WARN] Failed to sync {date_str} to database")
                return False
        finally:
            os.chdir(original_cwd)
    except Exception as e:
        print(f"[WARN] Exception syncing to database: {e}")
        import traceback
        traceback.print_exc()
        return False

def is_business_day(date):
    """Check if a date is a business day (Monday-Friday)."""
    return date.weekday() < 5

def main():
    ap = argparse.ArgumentParser(description="Automatically check for new Treasury data and generate snapshots.")
    ap.add_argument("--target-date", type=str, help="Target date (YYYY-MM-DD). Defaults to today.")
    ap.add_argument("--lookback", type=int, default=5, help="Days to look back for data (default: 5).")
    ap.add_argument("--force", action="store_true", help="Force regeneration even if snapshot exists.")
    ap.add_argument("--skip-plot", action="store_true", help="Skip plot generation.")
    ap.add_argument("--skip-summary", action="store_true", help="Skip summary generation.")
    ap.add_argument("--skip-sync", action="store_true", help="Skip database sync.")
    args = ap.parse_args()
    
    # Determine target date
    if args.target_date:
        target_date = dt.datetime.strptime(args.target_date, "%Y-%m-%d").date()
    else:
        target_date = dt.date.today()
    
    print(f"\n{'='*70}")
    print(f"AUTOMATED YIELD CURVE SNAPSHOT GENERATOR")
    print(f"{'='*70}")
    print(f"Target date: {target_date}")
    print(f"Lookback days: {args.lookback}")
    print(f"{'='*70}\n")
    
    # Check what we already have
    latest_snapshot_date = get_latest_snapshot_date()
    if latest_snapshot_date:
        print(f"[INFO] Latest snapshot in database: {latest_snapshot_date}")
    else:
        print(f"[INFO] No existing snapshots found")
    
    # Check for new data
    print(f"[CHECK] Checking for new Treasury data...")
    eff_date, par = check_new_data_available(target_date, args.lookback)
    
    if not eff_date or not par:
        print(f"[WARN] No Treasury data available for {target_date} (looked back {args.lookback} days)")
        print(f"[INFO] Treasury data is typically published after market close")
        return 0
    
    print(f"[OK] Found Treasury data for: {eff_date}")
    
    # Check if we already have this snapshot
    if snapshot_exists(eff_date) and not args.force:
        print(f"[SKIP] Snapshot already exists for {eff_date}")
        print(f"[INFO] Use --force to regenerate")
        
        # Still sync to database if needed
        if not args.skip_sync:
            sync_to_database(eff_date.isoformat())
        
        return 0
    
    # Generate snapshot
    date_str = eff_date.isoformat()
    if not generate_snapshot(date_str):
        print(f"[ERROR] Failed to generate snapshot")
        return 1
    
    # Generate summary
    if not args.skip_summary:
        generate_summary(date_str)
    
    # Generate plots
    if not args.skip_plot:
        generate_plot(date_str)
    
    # Sync to database
    if not args.skip_sync:
        sync_to_database(date_str)
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"[OK] Snapshot: {date_str}")
    if not args.skip_summary:
        print(f"[OK] Summary: {date_str}")
    if not args.skip_plot:
        print(f"[OK] Plots: {date_str}")
    if not args.skip_sync:
        print(f"[OK] Database sync: {date_str}")
    print(f"{'='*70}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

