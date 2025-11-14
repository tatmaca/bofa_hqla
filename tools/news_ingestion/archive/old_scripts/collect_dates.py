#!/usr/bin/env python3
"""
Collect News for Specific Dates
Collects and processes news for specified dates (Nov 8, 9, 10).
"""

import os
import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import get_conn, init_db
from bucket_news import bucket_articles, get_bucket_counts
from analyze_yield_impact import get_bucketed_news, analyze_yield_impact, load_curve_snapshot, save_analysis
from daily_pipeline import sync_yield_curve_data

def collect_and_process_dates(dates):
    """Collect and process news for specific dates."""
    print(f"\n{'='*70}")
    print(f"COLLECTING NEWS FOR SPECIFIED DATES")
    print(f"{'='*70}")
    print(f"Dates: {', '.join(dates)}\n")
    
    # Initialize database
    init_db()
    
    # Step 1: Run news ingestion (will collect recent articles)
    print("[1/4] Running news ingestion...")
    try:
        from run_ingest import run
        run()
        print("[OK] News ingestion completed")
    except Exception as e:
        print(f"[WARN] Ingestion had issues: {e}")
        print("[INFO] Continuing with existing articles...")
    
    # Step 2: Check what articles we have for these dates
    print("\n[2/4] Checking articles for target dates...")
    conn = get_conn()
    c = conn.cursor()
    
    date_articles = {}
    for date in dates:
        # Check articles published on this date
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
        """, (date,)).fetchone()[0]
        date_articles[date] = count
        print(f"  {date}: {count} articles")
    
    # Also check for articles published recently that might discuss these dates
    print("\n[INFO] Checking for recent articles that might discuss these dates...")
    for date in dates:
        # Look for articles published within 1 day of the target date
        next_day = (dt.datetime.strptime(date, "%Y-%m-%d").date() + dt.timedelta(days=1)).isoformat()
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE (DATE(published_at) = ? OR DATE(published_at) = ?)
              AND (title LIKE ? OR text LIKE ? OR summary LIKE ?)
        """, (date, next_day, f"%{date}%", f"%{date}%", f"%{date}%")).fetchone()[0]
        if count > 0:
            print(f"  Found {count} articles mentioning {date} (published on {date} or {next_day})")
    
    conn.close()
    
    # Step 3: Bucket articles
    print("\n[3/4] Bucketing articles...")
    try:
        # Bucket articles from last 72 hours to catch weekend news
        bucket_articles(hours=72, batch_size=200)
        print("[OK] Bucketing completed")
    except Exception as e:
        print(f"[ERROR] Bucketing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Generate analyses for dates with news
    print("\n[4/4] Generating analyses...")
    analyses_generated = 0
    
    for date in dates:
        print(f"\n  Processing {date}...")
        
        # Check if we have bucketed news for this date
        bucketed_news = get_bucketed_news(date)
        if not bucketed_news:
            print(f"    [SKIP] No bucketed news for {date}")
            continue
        
        print(f"    [INFO] Found news in {len(bucketed_news)} buckets")
        
        # Load yield curve snapshot
        current_curve = load_curve_snapshot(date)
        if not current_curve:
            # Try to load most recent snapshot
            repo_root = Path(__file__).resolve().parents[2]
            snapshots_dir = repo_root / "tools" / "ust_curve" / "llm" / "snapshots"
            if snapshots_dir.exists():
                snapshot_files = sorted(list(snapshots_dir.glob("curve_snapshot_*.json")))
                if snapshot_files:
                    latest_snapshot = snapshot_files[-1]
                    import json
                    with open(latest_snapshot) as f:
                        current_curve = json.load(f)
                    print(f"    [INFO] Using most recent snapshot: {latest_snapshot.stem}")
        
        # Generate analysis
        try:
            analysis = analyze_yield_impact(bucketed_news, current_curve)
            save_analysis(date, analysis, bucketed_news)
            print(f"    [OK] Analysis generated for {date}")
            analyses_generated += 1
        except Exception as e:
            print(f"    [ERROR] Analysis failed for {date}: {e}")
    
    print(f"\n[OK] Generated {analyses_generated} analyses")
    return True

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Collect and process news for specific dates")
    ap.add_argument("--dates", nargs="+", required=True,
                    help="Dates to process (YYYY-MM-DD)")
    args = ap.parse_args()
    
    dates = args.dates
    
    print(f"\n{'='*70}")
    print(f"COLLECTING NEWS FOR SPECIFIED DATES")
    print(f"{'='*70}")
    print(f"Dates: {', '.join(dates)}")
    print(f"{'='*70}\n")
    
    # Collect and process
    success = collect_and_process_dates(dates)
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    
    conn = get_conn()
    c = conn.cursor()
    
    for date in dates:
        # Count articles
        article_count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
        """, (date,)).fetchone()[0]
        
        # Count bucketed articles
        bucketed_count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
              AND bucket IS NOT NULL AND bucket != ''
        """, (date,)).fetchone()[0]
        
        # Get bucket breakdown
        bucket_counts = get_bucket_counts(date)
        
        # Check if analysis exists
        analyses_dir = Path(__file__).parent / "analyses"
        analysis_exists = (analyses_dir / f"yield_impact_{date}.json").exists()
        
        print(f"\n{date}:")
        print(f"  Articles: {article_count}")
        print(f"  Bucketed: {bucketed_count}")
        if bucket_counts:
            print(f"  Buckets: {', '.join([f'{k}: {v}' for k, v in bucket_counts.items()])}")
        print(f"  Analysis: {'[OK]' if analysis_exists else '[FAIL]'}")
    
    conn.close()
    
    print(f"\n{'='*70}\n")
    
    if success:
        print("[OK] Collection and processing completed!")
        return 0
    else:
        print("[WARN] Some steps had issues. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

