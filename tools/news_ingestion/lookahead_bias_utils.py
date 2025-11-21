#!/usr/bin/env python3
"""
Look-Ahead Bias Prevention Utilities
Ensures no future information leaks into predictions.
"""

import datetime as dt
from datetime import timezone, timedelta
from typing import Optional, Tuple
import pytz

# US Treasury market close time: 4:00 PM ET (16:00 ET)
# Convert to UTC: ET is UTC-5 (EST) or UTC-4 (EDT)
MARKET_CLOSE_ET = dt.time(16, 0)  # 4:00 PM ET
ET_TIMEZONE = pytz.timezone('America/New_York')

def get_market_close_time(date: dt.date, timezone_str: str = "America/New_York") -> dt.datetime:
    """
    Get market close time for a given date in UTC.
    
    Args:
        date: The date to get market close for
        timezone_str: Timezone string (default: America/New_York for ET)
    
    Returns:
        Market close time in UTC
    """
    tz = pytz.timezone(timezone_str)
    # Market closes at 4:00 PM ET
    local_close = dt.datetime.combine(date, MARKET_CLOSE_ET)
    local_close = tz.localize(local_close)
    utc_close = local_close.astimezone(pytz.UTC)
    return utc_close

def get_market_close_time_iso(date: str) -> str:
    """Get market close time as ISO string for a given date string."""
    date_obj = dt.datetime.strptime(date, "%Y-%m-%d").date()
    close_time = get_market_close_time(date_obj)
    return close_time.isoformat()

def is_article_before_market_close(article_published_at: str, yield_date: str) -> bool:
    """
    Check if an article was published before market close on the yield date.
    
    Args:
        article_published_at: ISO timestamp of article publication
        yield_date: Date string (YYYY-MM-DD) of yield curve snapshot
    
    Returns:
        True if article was published before market close, False otherwise
    """
    try:
        # Parse article published time
        if article_published_at:
            pub_dt = dt.datetime.fromisoformat(article_published_at.replace('Z', '+00:00'))
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        else:
            return False  # No timestamp = can't verify
        
        # Get market close time for yield date
        yield_date_obj = dt.datetime.strptime(yield_date, "%Y-%m-%d").date()
        market_close = get_market_close_time(yield_date_obj)
        
        # Article must be published before market close
        return pub_dt < market_close
    
    except (ValueError, AttributeError) as e:
        # If we can't parse, be conservative and exclude
        print(f"[WARN] Could not parse timestamp for look-ahead check: {e}")
        return False

def get_valid_news_for_date(date: str, hours_before: int = 24) -> Tuple[str, str]:
    """
    Get valid time range for news that could affect yields on a given date.
    
    Args:
        date: Date string (YYYY-MM-DD) of yield curve snapshot
        hours_before: How many hours before market close to include (default: 24)
    
    Returns:
        Tuple of (start_time_iso, end_time_iso) in UTC
    """
    yield_date_obj = dt.datetime.strptime(date, "%Y-%m-%d").date()
    market_close = get_market_close_time(yield_date_obj)
    
    # End time is market close
    end_time = market_close
    
    # Start time is hours_before before market close
    start_time = market_close - timedelta(hours=hours_before)
    
    return start_time.isoformat(), end_time.isoformat()

def validate_no_lookahead_bias(date: str, article_ids: list = None) -> Tuple[bool, list]:
    """
    Validate that no articles used for a date were published after market close.
    
    Args:
        date: Date string (YYYY-MM-DD) to validate
        article_ids: Optional list of article IDs to check (if None, checks all for date)
    
    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    from db import get_conn
    
    violations = []
    market_close = get_market_close_time(dt.datetime.strptime(date, "%Y-%m-%d").date())
    market_close_iso = market_close.isoformat()
    
    conn = get_conn()
    c = conn.cursor()
    
    if article_ids:
        placeholders = ','.join(['?'] * len(article_ids))
        query = f"""
            SELECT id, url, published_at, title
            FROM articles
            WHERE id IN ({placeholders})
            AND published_at IS NOT NULL
            AND published_at > ?
        """
        params = tuple(article_ids) + (market_close_iso,)
    else:
        query = """
            SELECT id, url, published_at, title
            FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
            AND published_at IS NOT NULL
            AND published_at > ?
        """
        params = (date, market_close_iso)
    
    rows = c.execute(query, params).fetchall()
    conn.close()
    
    for row in rows:
        violations.append({
            'article_id': row['id'],
            'url': row['url'],
            'published_at': row['published_at'],
            'title': row['title'],
            'market_close': market_close_iso
        })
    
    return len(violations) == 0, violations

