#!/usr/bin/env python3
"""
Retroactive Factor Extraction
Extracts factors from all historical articles in the database.
Can be run incrementally with resume capability.
"""

import os
import sys
import datetime as dt
from datetime import timedelta
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from extract_factors import extract_factors_for_date, get_openai_api_key

def get_dates_with_articles(start_date: str = None, end_date: str = None) -> list:
    """Get list of dates that have articles."""
    conn = get_conn()
    c = conn.cursor()
    
    query = """
        SELECT DISTINCT DATE(COALESCE(published_at, fetched_at)) as date
        FROM articles
        WHERE title IS NOT NULL AND title != ''
    """
    params = []
    
    if start_date:
        query += " AND DATE(COALESCE(published_at, fetched_at)) >= DATE(?)"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(COALESCE(published_at, fetched_at)) <= DATE(?)"
        params.append(end_date)
    
    query += " ORDER BY date"
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    return [row["date"] for row in rows]

def get_dates_already_extracted() -> set:
    """Get set of dates that already have factor extraction."""
    conn = get_conn()
    c = conn.cursor()
    
    rows = c.execute("""
        SELECT DISTINCT date
        FROM article_factors
    """).fetchall()
    
    conn.close()
    
    return {row["date"] for row in rows}

def main():
    ap = argparse.ArgumentParser(description="Extract factors from historical articles")
    ap.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    ap.add_argument("--resume", action="store_true", help="Skip dates that already have factors extracted")
    ap.add_argument("--batch-size", type=int, default=10, help="Number of dates to process before progress update")
    args = ap.parse_args()
    
    api_key = get_openai_api_key()
    if not api_key:
        print("[ERROR] No OpenAI API key found. Set OPENAI_API_KEY or add to news_config.yaml")
        return
    
    # Get dates to process
    dates = get_dates_with_articles(args.start_date, args.end_date)
    
    if not dates:
        print("[INFO] No articles found in date range")
        return
    
    print(f"[HIST] Found {len(dates)} dates with articles")
    
    # Filter out already extracted dates if resume
    if args.resume:
        extracted_dates = get_dates_already_extracted()
        dates = [d for d in dates if d not in extracted_dates]
        print(f"[HIST] After filtering, {len(dates)} dates need factor extraction")
    
    if not dates:
        print("[INFO] All dates already have factors extracted")
        return
    
    # Process dates
    total_processed = 0
    total_factors = 0
    
    for i, date in enumerate(dates, 1):
        print(f"\n{'='*70}")
        print(f"Processing {date} ({i}/{len(dates)})")
        print(f"{'='*70}")
        
        try:
            factors_count = extract_factors_for_date(date, api_key)
            total_factors += factors_count
            total_processed += 1
            
            if i % args.batch_size == 0:
                print(f"\n[PROGRESS] Processed {i}/{len(dates)} dates, {total_factors} total factors extracted")
        
        except Exception as e:
            print(f"[ERROR] Failed to process {date}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*70}")
    print(f"COMPLETE")
    print(f"{'='*70}")
    print(f"Processed: {total_processed}/{len(dates)} dates")
    print(f"Total factors extracted: {total_factors}")

if __name__ == "__main__":
    main()

