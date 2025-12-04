#!/usr/bin/env python3
"""
Collect and Process Weekend News
Collects news published over the weekend and processes them (bucketing, analysis).
"""

import os
import sys
import datetime as dt
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import get_conn, init_db
from bucket_news import bucket_articles, get_bucket_counts
from analyze_yield_impact import get_bucketed_news, analyze_yield_impact, load_curve_snapshot, save_analysis
from daily_pipeline import sync_yield_curve_data

def get_weekend_dates(days_back=7):
    """Get weekend dates (Saturday/Sunday) from the last N days."""
    today = dt.date.today()
    weekend_dates = []
    
    # Go back up to days_back days
    for i in range(days_back * 2):
        check_date = today - timedelta(days=i)
        # Saturday = 5, Sunday = 6
        if check_date.weekday() >= 5:
            weekend_dates.append(check_date.isoformat())
    
    return sorted(weekend_dates)

def collect_weekend_news(weekend_dates):
    """Collect news published on weekend dates."""
    print(f"\n{'='*70}")
    print(f"COLLECTING WEEKEND NEWS")
    print(f"{'='*70}")
    print(f"Weekend dates: {', '.join(weekend_dates)}\n")
    
    # Initialize database
    init_db()
    
    # Run regular ingestion - it will collect recent news
    # Note: RSS feeds typically only show last 24-48 hours, so weekend articles
    # may not be available anymore. We'll collect what we can.
    print("[1/3] Running news ingestion...")
    try:
        from run_ingest import run
        run()
        print("[OK] News ingestion completed")
    except Exception as e:
        print(f"[WARN] Ingestion had issues: {e}")
        print("[INFO] Continuing with existing articles...")
    
    # Check what articles we have for weekend dates
    conn = get_conn()
    c = conn.cursor()
    
    weekend_articles = {}
    for date in weekend_dates:
        # Check articles published on this date
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
        """, (date,)).fetchone()[0]
        weekend_articles[date] = count
        print(f"  {date}: {count} articles")
    
    # Also check for articles that mention weekend dates in content
    # (some news might be published Monday but discuss weekend events)
    print("\n[INFO] Checking for articles discussing weekend events...")
    for date in weekend_dates:
        # Look for articles that mention the date or were published shortly after
        # (within 1 day of weekend)
        next_day = (dt.datetime.strptime(date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE (DATE(published_at) = ? OR DATE(published_at) = ?)
              AND (title LIKE ? OR text LIKE ? OR summary LIKE ?)
        """, (date, next_day, f"%{date}%", f"%{date}%", f"%{date}%")).fetchone()[0]
        if count > 0:
            print(f"  Found {count} articles mentioning {date} (published on {date} or {next_day})")
    
    conn.close()
    
    return weekend_articles

def process_weekend_news(weekend_dates):
    """Process weekend news (bucketing and analysis)."""
    print(f"\n{'='*70}")
    print(f"PROCESSING WEEKEND NEWS")
    print(f"{'='*70}\n")
    
    # Step 1: Bucket articles
    print("[2/3] Bucketing weekend articles...")
    try:
        # Bucket articles from last 72 hours (to catch weekend news)
        bucket_articles(hours=72, batch_size=200)
        print("[OK] Bucketing completed")
    except Exception as e:
        print(f"[ERROR] Bucketing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Generate analyses for weekend dates
    print("\n[3/3] Generating analyses for weekend dates...")
    analyses_generated = 0
    
    for date in weekend_dates:
        print(f"\n  Processing {date}...")
        
        # Check if we have bucketed news for this date
        bucketed_news = get_bucketed_news(date)
        if not bucketed_news:
            print(f"    [SKIP] No bucketed news for {date}")
            continue
        
        print(f"    [INFO] Found news in {len(bucketed_news)} buckets")
        
        # Load yield curve snapshot (use most recent available)
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
    ap = argparse.ArgumentParser(description="Collect and process weekend news")
    ap.add_argument("--days-back", type=int, default=7, 
                    help="Days to look back for weekend dates (default: 7)")
    ap.add_argument("--skip-ingestion", action="store_true",
                    help="Skip news ingestion (use existing articles)")
    ap.add_argument("--skip-analysis", action="store_true",
                    help="Skip analysis generation (only bucket)")
    args = ap.parse_args()
    
    # Get weekend dates
    weekend_dates = get_weekend_dates(args.days_back)
    
    if not weekend_dates:
        print("[INFO] No weekend dates found in the specified range")
        return 0
    
    print(f"\n{'='*70}")
    print(f"WEEKEND NEWS COLLECTION & PROCESSING")
    print(f"{'='*70}")
    print(f"Weekend dates to process: {', '.join(weekend_dates)}")
    print(f"{'='*70}\n")
    
    # Step 1: Collect news
    if not args.skip_ingestion:
        weekend_articles = collect_weekend_news(weekend_dates)
        total_articles = sum(weekend_articles.values())
        print(f"\n[SUMMARY] Collected {total_articles} articles across {len(weekend_dates)} weekend dates")
    else:
        print("[SKIP] News ingestion skipped")
    
    # Step 2: Process news
    if not args.skip_analysis:
        success = process_weekend_news(weekend_dates)
        if not success:
            print("\n[WARN] Some processing steps failed")
            return 1
    else:
        print("[SKIP] Analysis generation skipped")
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    
    conn = get_conn()
    c = conn.cursor()
    
    for date in weekend_dates:
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
        
        # Check if analysis exists
        analyses_dir = Path(__file__).parent / "analyses"
        analysis_exists = (analyses_dir / f"yield_impact_{date}.json").exists()
        
        print(f"\n{date}:")
        print(f"  Articles: {article_count}")
        print(f"  Bucketed: {bucketed_count}")
        print(f"  Analysis: {'[OK]' if analysis_exists else '[FAIL]'}")
    
    conn.close()
    
    print(f"\n{'='*70}\n")
    print("[OK] Weekend news collection and processing completed!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

