#!/usr/bin/env python3
"""
Generate summaries and plots for existing yield curve snapshots.
"""

import os
import sys
import subprocess
import datetime as dt
from pathlib import Path
import re

# Get repo root
try:
    import subprocess as sp
    ROOT = Path(sp.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
except:
    ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

def get_snapshot_dates():
    """Get all dates that have snapshots."""
    snapshot_dir = ROOT / "tools" / "ust_curve" / "llm" / "snapshots"
    snapshots = sorted(snapshot_dir.glob("curve_snapshot_*.json"))
    dates = []
    for snapshot in snapshots:
        match = re.search(r'curve_snapshot_(\d{4}-\d{2}-\d{2})\.json', snapshot.name)
        if match:
            dates.append(match.group(1))
    return sorted(dates)

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
            return True, None
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

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
            return True, None
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Generate summaries and plots for existing snapshots")
    ap.add_argument("--days", type=int, help="Limit to last N business days (default: all)")
    ap.add_argument("--skip-summaries", action="store_true", help="Skip generating summaries")
    ap.add_argument("--skip-plots", action="store_true", help="Skip generating plots")
    args = ap.parse_args()
    
    # Get all snapshot dates
    all_dates = get_snapshot_dates()
    
    # Limit to last N days if specified
    if args.days:
        end_date = dt.date.today()
        cutoff_date = (end_date - dt.timedelta(days=args.days * 2)).isoformat()  # Approximate
        dates = [d for d in all_dates if d >= cutoff_date]
    else:
        dates = all_dates
    
    print(f"\n{'='*70}")
    print(f"GENERATING SUMMARIES AND PLOTS")
    print(f"{'='*70}")
    print(f"Total snapshots found: {len(all_dates)}")
    print(f"Dates to process: {len(dates)}")
    if dates:
        print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"{'='*70}\n")
    
    summary_success = 0
    summary_fail = 0
    plot_success = 0
    plot_fail = 0
    
    for i, date_str in enumerate(dates, 1):
        print(f"[{i}/{len(dates)}] Processing {date_str}...")
        
        # Generate summary
        if not args.skip_summaries:
            success, error = run_make_summary(date_str)
            if success:
                print(f"  ✓ Summary created")
                summary_success += 1
            else:
                print(f"  ✗ Summary failed: {error[:100] if error else 'Unknown error'}")
                summary_fail += 1
        
        # Generate plots
        if not args.skip_plots:
            success, error = run_plot_snapshot(date_str)
            if success:
                print(f"  ✓ Plots created")
                plot_success += 1
            else:
                print(f"  ✗ Plots failed: {error[:100] if error else 'Unknown error'}")
                plot_fail += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    if not args.skip_summaries:
        print(f"Summaries: {summary_success} success, {summary_fail} failed")
    if not args.skip_plots:
        print(f"Plots: {plot_success} success, {plot_fail} failed")
    print(f"{'='*70}\n")
    
    # List generated files
    if not args.skip_summaries:
        summary_dir = ROOT / "tools" / "ust_curve" / "llm" / "summaries"
        summaries = list(summary_dir.glob("*.md")) + list(summary_dir.glob("*.json"))
        print(f"Total summaries: {len(summaries)}")
    
    if not args.skip_plots:
        plot_dir = ROOT / "tools" / "ust_curve" / "llm" / "plots"
        plots = list(plot_dir.glob("*.png"))
        print(f"Total plots: {len(plots)}")

if __name__ == "__main__":
    main()

