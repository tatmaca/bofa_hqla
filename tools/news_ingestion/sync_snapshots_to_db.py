#!/usr/bin/env python3
"""
Sync all yield curve snapshots to the database for training.
"""

import os
import sys
import json
from pathlib import Path
import re

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn, init_db
from daily_pipeline import sync_yield_curve_data

def get_snapshot_dates():
    """Get all dates that have snapshots."""
    repo_root = Path(__file__).resolve().parents[2]
    snapshot_dir = repo_root / "tools" / "ust_curve" / "llm" / "snapshots"
    snapshots = sorted(snapshot_dir.glob("curve_snapshot_*.json"))
    dates = []
    for snapshot in snapshots:
        match = re.search(r'curve_snapshot_(\d{4}-\d{2}-\d{2})\.json', snapshot.name)
        if match:
            dates.append(match.group(1))
    return sorted(dates)

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Sync yield curve snapshots to database")
    ap.add_argument("--days", type=int, help="Limit to last N business days")
    args = ap.parse_args()
    
    # Initialize database
    init_db()
    
    # Get snapshot dates
    all_dates = get_snapshot_dates()
    
    # Limit if requested
    if args.days:
        dates = all_dates[-args.days:]
    else:
        dates = all_dates
    
    print(f"\n{'='*70}")
    print(f"SYNCING YIELD CURVE SNAPSHOTS TO DATABASE")
    print(f"{'='*70}")
    print(f"Total snapshots found: {len(all_dates)}")
    print(f"Dates to sync: {len(dates)}")
    if dates:
        print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"{'='*70}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, date_str in enumerate(dates, 1):
        print(f"[{i}/{len(dates)}] Syncing {date_str}...", end=" ")
        if sync_yield_curve_data(date_str):
            success_count += 1
            print("✓")
        else:
            fail_count += 1
            print("✗")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Synced: {success_count}")
    print(f"Failed: {fail_count}")
    
    # Check database
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM yield_curve_daily").fetchone()[0]
    conn.close()
    print(f"Total dates in database: {count}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

