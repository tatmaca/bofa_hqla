#!/usr/bin/env python3
"""
Batch Factor Extraction
Extracts factors for multiple dates in batch, identifying dates that need extraction.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from db import get_conn
from extract_factors import extract_factors_for_date, get_openai_api_key

def get_dates_with_news(start_date: str, end_date: str) -> List[str]:
    """
    Get all dates with news articles in the specified range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        List of date strings in chronological order
    """
    conn = get_conn()
    c = conn.cursor()
    
    rows = c.execute("""
        SELECT DISTINCT DATE(COALESCE(published_at, fetched_at)) as date
        FROM articles
        WHERE title IS NOT NULL AND title != ''
          AND DATE(COALESCE(published_at, fetched_at)) >= ?
          AND DATE(COALESCE(published_at, fetched_at)) <= ?
        ORDER BY date
    """, (start_date, end_date)).fetchall()
    
    conn.close()
    
    return [row["date"] for row in rows]


def get_dates_with_factors(start_date: str, end_date: str) -> set:
    """
    Get all dates that already have factor scores extracted.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Set of date strings
    """
    conn = get_conn()
    c = conn.cursor()
    
    rows = c.execute("""
        SELECT DISTINCT date
        FROM daily_factor_scores
        WHERE date >= ? AND date <= ?
    """, (start_date, end_date)).fetchall()
    
    conn.close()
    
    return {row["date"] for row in rows}


def identify_dates_needing_extraction(start_date: str, end_date: str) -> List[str]:
    """
    Identify dates that have news articles but no factor scores.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        List of date strings needing factor extraction
    """
    dates_with_news = get_dates_with_news(start_date, end_date)
    dates_with_factors = get_dates_with_factors(start_date, end_date)
    
    dates_needing_extraction = [date for date in dates_with_news if date not in dates_with_factors]
    
    return sorted(dates_needing_extraction)


def extract_factors_for_date_range(start_date: str, 
                                   end_date: str,
                                   api_key: Optional[str] = None,
                                   dry_run: bool = False) -> Dict[str, Dict]:
    """
    Extract factors for all dates in range that need extraction.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        api_key: OpenAI API key (if None, loads from config)
        dry_run: If True, only report what would be done without actually extracting
    
    Returns:
        Dictionary with extraction results:
        {
            "total_dates": int,
            "dates_needing_extraction": List[str],
            "successful": List[str],
            "failed": Dict[str, str],  # {date: error_message}
            "skipped": List[str]  # dates that already have factors
        }
    """
    if not api_key:
        api_key = get_openai_api_key()
        if not api_key:
            print("[ERROR] No OpenAI API key found")
            return {
                "total_dates": 0,
                "dates_needing_extraction": [],
                "successful": [],
                "failed": {},
                "skipped": []
            }
    
    # Identify dates needing extraction
    dates_with_news = get_dates_with_news(start_date, end_date)
    dates_with_factors = get_dates_with_factors(start_date, end_date)
    dates_needing_extraction = [date for date in dates_with_news if date not in dates_with_factors]
    dates_already_done = [date for date in dates_with_news if date in dates_with_factors]
    
    print(f"\n{'='*60}")
    print(f"BATCH FACTOR EXTRACTION")
    print(f"{'='*60}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total dates with news: {len(dates_with_news)}")
    print(f"Dates with factors already: {len(dates_already_done)}")
    print(f"Dates needing extraction: {len(dates_needing_extraction)}")
    print(f"{'='*60}\n")
    
    if dry_run:
        print("[DRY RUN] Would extract factors for:")
        for date in dates_needing_extraction:
            print(f"  - {date}")
        print()
        return {
            "total_dates": len(dates_with_news),
            "dates_needing_extraction": dates_needing_extraction,
            "successful": [],
            "failed": {},
            "skipped": dates_already_done
        }
    
    if not dates_needing_extraction:
        print("[INFO] All dates already have factors extracted")
        return {
            "total_dates": len(dates_with_news),
            "dates_needing_extraction": [],
            "successful": [],
            "failed": {},
            "skipped": dates_already_done
        }
    
    # Extract factors for each date
    successful = []
    failed = {}
    
    for i, date in enumerate(dates_needing_extraction, 1):
        print(f"[{i}/{len(dates_needing_extraction)}] Extracting factors for {date}...")
        try:
            factor_count = extract_factors_for_date(date, api_key)
            if factor_count > 0:
                print(f"[OK] Extracted {factor_count} factors for {date}")
                successful.append(date)
            else:
                print(f"[WARN] No factors extracted for {date} (may need more articles)")
                successful.append(date)  # Still count as successful (no error)
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Failed to extract factors for {date}: {error_msg}")
            failed[date] = error_msg
    
    # Summary
    print(f"\n{'='*60}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total dates processed: {len(dates_needing_extraction)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Already had factors: {len(dates_already_done)}")
    print(f"{'='*60}\n")
    
    if failed:
        print("Failed dates:")
        for date, error in failed.items():
            print(f"  {date}: {error}")
        print()
    
    return {
        "total_dates": len(dates_with_news),
        "dates_needing_extraction": dates_needing_extraction,
        "successful": successful,
        "failed": failed,
        "skipped": dates_already_done
    }


def main():
    """Main entry point for batch factor extraction."""
    ap = argparse.ArgumentParser(
        description="Batch extract factors for historical dates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract factors for all dates in range
  python3 batch_extract_factors.py --start-date 2025-11-06 --end-date 2025-12-04

  # Dry run to see what would be extracted
  python3 batch_extract_factors.py --start-date 2025-11-06 --end-date 2025-12-04 --dry-run

  # Extract for specific date range
  python3 batch_extract_factors.py --start-date 2025-11-10 --end-date 2025-11-20
        """
    )
    
    ap.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    
    ap.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be extracted without actually extracting"
    )
    
    args = ap.parse_args()
    
    # Validate dates
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"[ERROR] Invalid date format: {e}")
        print("Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    if args.start_date > args.end_date:
        print("[ERROR] Start date must be before or equal to end date")
        sys.exit(1)
    
    # Run extraction
    results = extract_factors_for_date_range(
        args.start_date,
        args.end_date,
        dry_run=args.dry_run
    )
    
    # Exit with error code if any failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

