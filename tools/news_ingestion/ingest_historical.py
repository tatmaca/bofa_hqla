#!/usr/bin/env python3
"""
Historical News Ingestion Script
Runs news ingestion for past dates with strict timestamp controls to prevent look-back bias.

Key features:
- Only collects articles published on or before the target date
- Sets fetched_at to target date (simulates historical fetch)
- Ensures no future information leaks into past predictions
"""

import os
import sys
import subprocess
import datetime as dt
from datetime import timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, start_ingestion_run, complete_ingestion_run, get_conn

def get_business_days_back(start_date: dt.date, num_days: int) -> list:
    """Get the last N business days before (and including) start_date."""
    business_days = []
    current = start_date
    days_back = 0
    
    while len(business_days) < num_days and days_back < num_days * 2:
        if current.weekday() < 5:  # Monday-Friday
            business_days.append(current)
        current = current - timedelta(days=1)
        days_back += 1
    
    return sorted(business_days)

def run_ingestion_for_date(target_date: dt.date, dry_run: bool = False):
    """Run news ingestion for a specific historical date."""
    date_str = target_date.isoformat()
    
    print(f"\n{'='*70}")
    print(f"INGESTING NEWS FOR {date_str}")
    print(f"{'='*70}")
    
    if dry_run:
        print("[DRY RUN] Would run ingestion...")
        return True
    
    # Initialize database
    init_db()
    
    # Start ingestion run with target date
    run_date = start_ingestion_run(date_str)
    print(f">> Starting ingestion run for {run_date}")
    
    # Set environment variable for historical mode
    env = os.environ.copy()
    env["TARGET_DATE"] = date_str
    
    try:
        # Import and run RSS ingestion with target date
        from ingest_rss import run as run_rss
        run_rss(target_date=target_date)
        
        # Note: crawl_web.py would need similar modifications
        # For now, we'll skip web crawl for historical dates to avoid complexity
        print(">> Web crawl skipped for historical dates (RSS only)")
        
        # Complete ingestion run
        conn = get_conn()
        cursor = conn.cursor()
        
        # Count articles fetched in this run
        new_count = cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE DATE(fetched_at) = ?
        """, (date_str,)).fetchone()[0]
        
        # Verify no look-back bias: check that all articles have published_at <= target_date
        future_articles = cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE DATE(fetched_at) = ? 
            AND published_at IS NOT NULL
            AND DATE(published_at) > ?
        """, (date_str, date_str)).fetchone()[0]
        
        conn.close()
        
        complete_ingestion_run(
            run_date, 
            rss_processed=new_count, 
            rss_skipped=0,
            crawl_processed=0, 
            crawl_skipped=0,
            status="completed"
        )
        
        print(f">> Done. New articles: {new_count}")
        
        if future_articles > 0:
            print(f"[WARNING] Found {future_articles} articles with published_at > {date_str}")
            print("[WARNING] This indicates potential look-back bias!")
            return False
        
        print(f"[VERIFY] [OK] No look-back bias detected (all articles published <= {date_str})")
        return True
        
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        complete_ingestion_run(run_date, status="failed", error_message=str(e))
        return False

def main():
    import argparse
    
    ap = argparse.ArgumentParser(
        description="Run news ingestion for historical dates with strict timestamp controls"
    )
    ap.add_argument("--days", type=int, default=30, help="Number of business days to process (default: 30)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--date", type=str, help="Single date to process (YYYY-MM-DD)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be done without running")
    args = ap.parse_args()
    
    if args.date:
        # Single date
        target_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
        dates = [target_date]
    elif args.start_date:
        # Date range
        start = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else dt.date.today()
        dates = [d for d in get_business_days_back(end, args.days) if d >= start]
    else:
        # Last N business days
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else dt.date.today()
        dates = get_business_days_back(end_date, args.days)
    
    print(f"\n{'='*70}")
    print(f"HISTORICAL NEWS INGESTION")
    print(f"{'='*70}")
    print(f"Dates to process: {len(dates)}")
    if dates:
        print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"{'='*70}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, date in enumerate(dates, 1):
        print(f"\n[{i}/{len(dates)}] Processing {date.isoformat()}...")
        if run_ingestion_for_date(date, dry_run=args.dry_run):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
