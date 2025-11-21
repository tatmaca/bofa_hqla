#!/usr/bin/env python3
"""
Comprehensive Look-Ahead Bias Validation Script
Validates that no future information is used in predictions.
"""

import datetime as dt
from datetime import timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from lookahead_bias_utils import (
    get_market_close_time,
    validate_no_lookahead_bias,
    is_article_before_market_close
)

def validate_all_dates(start_date: str = None, end_date: str = None):
    """Validate look-ahead bias for all dates in range."""
    if start_date is None:
        start_date = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    if end_date is None:
        end_date = dt.date.today().isoformat()
    
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    dates = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Business days only
            dates.append(current.isoformat())
        current += dt.timedelta(days=1)
    
    print("=" * 70)
    print("LOOK-AHEAD BIAS VALIDATION")
    print("=" * 70)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Checking {len(dates)} business days\n")
    
    total_violations = 0
    dates_with_violations = []
    
    for date in dates:
        is_valid, violations = validate_no_lookahead_bias(date)
        
        if violations:
            total_violations += len(violations)
            dates_with_violations.append((date, violations))
            print(f"❌ {date}: {len(violations)} violations")
            for v in violations[:3]:  # Show first 3
                print(f"   - Article {v['article_id']}: {v['title'][:50]}...")
                print(f"     Published: {v['published_at']}")
                print(f"     Market close: {v['market_close']}")
            if len(violations) > 3:
                print(f"   ... and {len(violations) - 3} more")
        else:
            print(f"✅ {date}: No violations")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total dates checked: {len(dates)}")
    print(f"Dates with violations: {len(dates_with_violations)}")
    print(f"Total violations: {total_violations}")
    
    if total_violations == 0:
        print("\n✅ All dates passed look-ahead bias validation!")
    else:
        print(f"\n⚠️  Found {total_violations} look-ahead bias violations")
        print("   These articles should be excluded from training/analysis")
    
    return dates_with_violations

def check_article_timestamps():
    """Check for articles with missing or invalid timestamps."""
    conn = get_conn()
    c = conn.cursor()
    
    # Articles without published_at
    no_timestamp = c.execute("""
        SELECT COUNT(*) FROM articles
        WHERE published_at IS NULL
    """).fetchone()[0]
    
    # Articles with published_at but no date match
    invalid_timestamp = c.execute("""
        SELECT COUNT(*) FROM articles
        WHERE published_at IS NOT NULL
        AND DATE(published_at) != DATE(COALESCE(published_at, fetched_at))
    """).fetchone()[0]
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("TIMESTAMP VALIDATION")
    print("=" * 70)
    print(f"Articles without published_at: {no_timestamp}")
    print(f"Articles with timestamp mismatches: {invalid_timestamp}")
    
    if no_timestamp > 0:
        print(f"\n⚠️  {no_timestamp} articles missing published_at timestamps")
        print("   These cannot be validated for look-ahead bias")
        print("   Recommendation: Exclude from training or use fetched_at as fallback")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Validate look-ahead bias prevention")
    ap.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    ap.add_argument("--days-back", type=int, help="Number of past business days to check (alternative to date range)")
    ap.add_argument("--check-timestamps", action="store_true", help="Check timestamp quality")
    args = ap.parse_args()
    
    if args.check_timestamps:
        check_article_timestamps()
    
    # Handle --days-back option
    if args.days_back:
        end_date = dt.date.today()
        # Calculate start date by going back enough days to get N business days
        start_date = end_date
        business_days = 0
        while business_days < args.days_back:
            if start_date.weekday() < 5:
                business_days += 1
            if business_days < args.days_back:
                start_date -= dt.timedelta(days=1)
        validate_all_dates(start_date.isoformat(), end_date.isoformat())
    else:
        validate_all_dates(args.start_date, args.end_date)

if __name__ == "__main__":
    main()

