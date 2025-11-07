#!/usr/bin/env python3
"""
Generate yield curve snapshots for the past N business days.
This script will create snapshots, summaries, and plots for each business day.
"""

import os
import sys
import subprocess
import datetime as dt
from pathlib import Path
from datetime import timedelta

# Get repo root - use git if available, otherwise go up 3 levels from script location
try:
    import subprocess as sp
    ROOT = Path(sp.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
except:
    # Fallback: script is in tools/ust_curve/llm/, so go up 3 levels
    ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

def is_business_day(date):
    """Check if a date is a business day (Monday-Friday)."""
    return date.weekday() < 5  # 0=Monday, 4=Friday

def get_business_days_back(start_date, num_days):
    """Get the last N business days before (and including) start_date."""
    business_days = []
    current = start_date
    days_back = 0
    
    while len(business_days) < num_days and days_back < num_days * 2:  # Safety limit
        if is_business_day(current):
            business_days.append(current)
        current = current - timedelta(days=1)
        days_back += 1
    
    return sorted(business_days)  # Return in chronological order

def check_snapshot_exists(date_str):
    """Check if snapshot already exists for a date."""
    snapshot_path = ROOT / "tools" / "ust_curve" / "llm" / "snapshots" / f"curve_snapshot_{date_str}.json"
    return snapshot_path.exists()

def run_build_snapshot(date_str, skip_existing=True):
    """Run build_snapshots.py for a specific date."""
    if skip_existing and check_snapshot_exists(date_str):
        print(f"[SKIP] Snapshot already exists for {date_str}")
        return True
    
    print(f"\n{'='*60}")
    print(f"Building snapshot for {date_str}")
    print(f"{'='*60}")
    
    # Set up environment
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = sys.executable  # Fallback to system Python
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    # Run build_snapshots.py
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "build_snapshots.py"
    try:
        result = subprocess.run(
            [str(venv_python), str(script_path), "--core-module", "tools.ust_curve.curves", date_str],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per date
        )
        
        if result.returncode == 0:
            print(f"[OK] Snapshot built for {date_str}")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"[ERROR] Failed to build snapshot for {date_str}")
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout building snapshot for {date_str}")
        return False
    except Exception as e:
        print(f"[ERROR] Exception building snapshot for {date_str}: {e}")
        return False

def run_make_summary(date_str):
    """Run make_summary.py for a specific date."""
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = sys.executable
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "make_summary.py"
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
            print(f"[OK] Summary created for {date_str}")
            return True
        else:
            print(f"[WARN] Summary creation failed for {date_str}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Exception creating summary for {date_str}: {e}")
        return False

def run_plot_snapshot(date_str):
    """Run plot_snapshot.py for a specific date."""
    venv_python = ROOT / "tools" / "ust_curve" / "venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = sys.executable
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}/tools/ust_curve:{ROOT}:{env.get('PYTHONPATH', '')}"
    
    script_path = ROOT / "tools" / "ust_curve" / "llm" / "plot_snapshot.py"
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
            print(f"[OK] Plots created for {date_str}")
            return True
        else:
            print(f"[WARN] Plot creation failed for {date_str}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[WARN] Exception creating plots for {date_str}: {e}")
        return False

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Generate yield curve snapshots for past N business days")
    ap.add_argument("--days", type=int, default=30, help="Number of business days to generate (default: 30)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--skip-existing", action="store_true", default=True, help="Skip dates that already have snapshots")
    ap.add_argument("--skip-summaries", action="store_true", help="Skip generating summaries")
    ap.add_argument("--skip-plots", action="store_true", help="Skip generating plots")
    args = ap.parse_args()
    
    # Determine end date
    if args.end_date:
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        end_date = dt.date.today()
    
    # Get business days
    business_days = get_business_days_back(end_date, args.days)
    
    print(f"\n{'='*70}")
    print(f"GENERATING YIELD CURVE SNAPSHOTS")
    print(f"{'='*70}")
    print(f"End date: {end_date}")
    print(f"Business days to process: {len(business_days)}")
    print(f"Date range: {business_days[0]} to {business_days[-1]}")
    print(f"{'='*70}\n")
    
    # Process each date
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, date in enumerate(business_days, 1):
        date_str = date.isoformat()
        print(f"\n[{i}/{len(business_days)}] Processing {date_str}...")
        
        # Build snapshot
        if run_build_snapshot(date_str, skip_existing=args.skip_existing):
            success_count += 1
            
            # Generate summary (if not skipped)
            if not args.skip_summaries:
                run_make_summary(date_str)
            
            # Generate plots (if not skipped)
            if not args.skip_plots:
                run_plot_snapshot(date_str)
        else:
            if check_snapshot_exists(date_str):
                skip_count += 1
            else:
                fail_count += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total dates processed: {len(business_days)}")
    print(f"  ✓ Success: {success_count}")
    print(f"  ⊘ Skipped (already exist): {skip_count}")
    print(f"  ✗ Failed: {fail_count}")
    print(f"{'='*70}\n")
    
    # List generated snapshots
    snapshot_dir = ROOT / "tools" / "ust_curve" / "llm" / "snapshots"
    snapshots = sorted(snapshot_dir.glob("curve_snapshot_*.json"))
    print(f"Total snapshots available: {len(snapshots)}")
    if snapshots:
        print(f"Latest: {snapshots[-1].name}")
        print(f"Oldest: {snapshots[0].name}")

if __name__ == "__main__":
    main()

