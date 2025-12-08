#!/usr/bin/env python3
"""
Yield Movement Threshold Detection
Implements statistical thresholds to identify significant yield curve movements.
Filters out noise/mean-reverting movements and focuses on significant moves (>2 std dev).
"""

import os
import sys
import json
import numpy as np
import requests
import csv
import io
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

# All available tenors from Treasury data
TENORS = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

# Treasury data sources
YEARLY_CSV_TMPL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?_format=csv&type=daily_treasury_yield_curve&field_tdr_date_value={year}"
CSV_ARCHIVE_BASE = "https://home.treasury.gov/system/files/276"
CSV_ARCHIVE_FILES = {
    "1990-2024": "yield-curve-rates-1990-2024.csv",
    "2011-2020": "yield-curve-rates-2011-2020.csv",
    "2001-2010": "yield-curve-rates-2001-2010.csv",
    "1990-2000": "yield-curve-rates-1990-2000.csv",
}

def fetch_treasury_data_for_date(target_date: date) -> Optional[Dict[str, float]]:
    """
    Fetch Treasury yield curve data for a specific date from Treasury website.
    
    Returns:
        Dictionary mapping tenor keys (e.g., "0.25", "2", "10") to yield values, or None
    """
    # Try yearly CSV first (works for recent years)
    try:
        url = YEARLY_CSV_TMPL.format(year=target_date.year)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        rdr = csv.DictReader(io.StringIO(r.text))
        target = target_date.strftime("%m/%d/%Y")
        alt = target_date.strftime("%-m/%-d/%Y") if sys.platform != "win32" else target
        
        for rec in rdr:
            if rec.get("Date") not in (target, alt):
                continue
            
            def f(col):
                v = (rec.get(col) or "").strip()
                if not v or v.upper() == "N/A":
                    return None
                try:
                    return float(v)
                except:
                    return None
            
            out = {
                "0.25": f("3 Mo") or f("6 Mo"),  # 3 months
                "1": f("1 Yr"),
                "2": f("2 Yr"),
                "3": f("3 Yr"),
                "5": f("5 Yr"),
                "7": f("7 Yr"),
                "10": f("10 Yr"),
                "20": f("20 Yr"),
                "30": f("30 Yr"),
            }
            return {k: v for k, v in out.items() if isinstance(v, float)}
    except Exception:
        pass
    
    # Try archive CSV as fallback
    try:
        archive_url = None
        if 1990 <= target_date.year <= 2024:
            archive_url = f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['1990-2024']}"
        elif 2011 <= target_date.year <= 2020:
            archive_url = f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['2011-2020']}"
        elif 2001 <= target_date.year <= 2010:
            archive_url = f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['2001-2010']}"
        elif 1990 <= target_date.year <= 2000:
            archive_url = f"{CSV_ARCHIVE_BASE}/{CSV_ARCHIVE_FILES['1990-2000']}"
        
        if archive_url:
            r = requests.get(archive_url, timeout=30)
            r.raise_for_status()
            lines = r.text.splitlines()
            rdr = csv.DictReader(io.StringIO("\n".join(lines)))
            target = target_date.strftime("%m/%d/%Y")
            alt = target_date.strftime("%-m/%-d/%Y") if sys.platform != "win32" else target
            
            for rec in rdr:
                if rec.get("Date") in (target, alt):
                    def f(col):
                        v = rec.get(col, "").strip()
                        if v in ("", "N/A"):
                            return None
                        try:
                            return float(v)
                        except:
                            return None
                    
                    out = {
                        "0.25": f("3 Mo") or f("6 Mo"),
                        "1": f("1 Yr"),
                        "2": f("2 Yr"),
                        "3": f("3 Yr"),
                        "5": f("5 Yr"),
                        "7": f("7 Yr"),
                        "10": f("10 Yr"),
                        "20": f("20 Yr"),
                        "30": f("30 Yr"),
                    }
                    return {k: v for k, v in out.items() if isinstance(v, float)}
    except Exception:
        pass
    
    return None

def fetch_historical_yield_changes(start_date: date, end_date: date, 
                                   tenor: str) -> List[float]:
    """
    Fetch historical yield changes for a tenor from Treasury website.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        tenor: Tenor name (e.g., "2Y", "10Y")
    
    Returns:
        List of daily yield changes in basis points
    """
    # Map tenor to Treasury key
    tenor_to_key = {
        "3M": "0.25",
        "2Y": "2",
        "5Y": "5",
        "10Y": "10",
        "30Y": "30"
    }
    
    treasury_key = tenor_to_key.get(tenor)
    if not treasury_key:
        return []
    
    changes = []
    prev_yield = None
    
    # Iterate through dates (business days only)
    current = start_date
    while current <= end_date:
        # Skip weekends
        if current.weekday() < 5:
            data = fetch_treasury_data_for_date(current)
            if data and treasury_key in data:
                current_yield = data[treasury_key]
                if prev_yield is not None:
                    # Calculate change in basis points
                    change_bps = (current_yield - prev_yield) * 100
                    changes.append(change_bps)
                prev_yield = current_yield
        
        current += timedelta(days=1)
    
    return changes

def calculate_rolling_statistics(tenor: str, window_days: int = 60, 
                                 min_samples: int = 20,
                                 target_date: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate rolling mean and standard deviation for a tenor's yield changes.
    Uses Treasury website historical data as the starting point.
    
    Args:
        tenor: Tenor name (e.g., "2Y", "10Y")
        window_days: Number of days to look back
        min_samples: Minimum samples required for valid statistics
        target_date: Target date (YYYY-MM-DD) for rolling window, defaults to today
    
    Returns:
        {"mean": float, "std": float, "count": int} or None if insufficient data
    """
    if target_date:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        target = date.today()
    
    # Calculate date range for rolling window
    end_date = target
    start_date = target - timedelta(days=window_days * 2)  # Fetch extra to ensure we have enough
    
    # First, try to get data from database
    conn = get_conn()
    c = conn.cursor()
    
    rows = c.execute("""
        SELECT date, delta_zeros_pct
        FROM yield_curve_daily
        WHERE date IS NOT NULL
        AND delta_zeros_pct IS NOT NULL
        AND date <= ?
        ORDER BY date DESC
        LIMIT ?
    """, (target_date or target.isoformat(), window_days)).fetchall()
    
    conn.close()
    
    # Extract changes from database
    changes = []
    tenor_key = tenor.lower().replace("M", "m").replace("Y", "y")
    
    for row in rows:
        try:
            delta_zeros = json.loads(row["delta_zeros_pct"])
            change = None
            if tenor_key in delta_zeros:
                change = delta_zeros[tenor_key]
            elif tenor.upper() in delta_zeros:
                change = delta_zeros[tenor.upper()]
            elif tenor.lower() in delta_zeros:
                change = delta_zeros[tenor.lower()]
            
            if change is not None:
                changes.append(float(change) * 100)
        except:
            continue
    
    # If we don't have enough data for the full window, fetch from Treasury website
    if len(changes) < window_days:
        # Get dates we already have from database
        existing_dates = set()
        existing_yields = {}  # date -> yield value
        
        if rows:
            # We need to reconstruct yields from changes, so fetch actual yields
            # For now, fetch historical yields directly
            pass
        
        # Fetch historical yield data for the window period
        print(f"[THRESHOLD] Fetching historical Treasury data for {tenor} (have {len(changes)} days, need {window_days})")
        
        # Fetch yields for the date range
        historical_yields = {}  # date -> yield
        current = start_date
        fetched_count = 0
        
        while current <= end_date and fetched_count < window_days * 2:
            if current.weekday() < 5:  # Business days only
                data = fetch_treasury_data_for_date(current)
                if data:
                    # Map tenor to Treasury key
                    tenor_to_key = {"3M": "0.25", "2Y": "2", "5Y": "5", "10Y": "10", "30Y": "30"}
                    treasury_key = tenor_to_key.get(tenor)
                    
                    if treasury_key and treasury_key in data:
                        historical_yields[current] = data[treasury_key]
                        fetched_count += 1
            
            current += timedelta(days=1)
        
        # Calculate changes from historical yields
        historical_changes = []
        sorted_dates = sorted(historical_yields.keys())
        
        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i-1]
            curr_date = sorted_dates[i]
            
            # Only include if within window_days of target
            days_diff = (target - curr_date).days
            if 0 <= days_diff <= window_days:
                prev_yield = historical_yields[prev_date]
                curr_yield = historical_yields[curr_date]
                change_bps = (curr_yield - prev_yield) * 100
                historical_changes.append(change_bps)
        
        # Combine: use historical data first (older), then database data (newer)
        # This ensures we have a full window ending at target_date
        all_changes = historical_changes + changes
        
        # Take the most recent window_days
        changes = all_changes[-window_days:] if len(all_changes) > window_days else all_changes
    
    if len(changes) < min_samples:
        return None
    
    changes_array = np.array(changes)
    mean = float(np.mean(changes_array))
    std = float(np.std(changes_array))
    
    return {
        "mean": mean,
        "std": std,
        "count": len(changes)
    }

def is_significant_move(tenor: str, actual_change_bps: float,
                      threshold_std: float = 2.0,
                      window_days: int = 60,
                      target_date: Optional[str] = None) -> Tuple[bool, Dict]:
    """
    Check if a yield change is significant (beyond threshold standard deviations).
    
    Args:
        tenor: Tenor name
        actual_change_bps: Actual yield change in basis points
        threshold_std: Number of standard deviations (default: 2.0)
        window_days: Rolling window for statistics
        target_date: Target date for rolling window (YYYY-MM-DD)
    
    Returns:
        (is_significant, stats_dict)
    """
    stats = calculate_rolling_statistics(tenor, window_days, target_date=target_date)
    
    if not stats:
        # If no historical data, use absolute threshold as fallback
        abs_threshold = 5.0  # 5 bps default
        is_sig = abs(actual_change_bps) >= abs_threshold
        return is_sig, {
            "mean": 0.0,
            "std": 0.0,
            "threshold_bps": abs_threshold,
            "method": "absolute_fallback"
        }
    
    mean = stats["mean"]
    std = stats["std"]
    
    # Calculate threshold in bps
    threshold_bps = threshold_std * std
    
    # Check if move is significant (beyond mean ± threshold)
    deviation = abs(actual_change_bps - mean)
    is_significant = deviation >= threshold_bps
    
    return is_significant, {
        "mean": mean,
        "std": std,
        "threshold_bps": threshold_bps,
        "deviation": deviation,
        "method": "statistical"
    }

def get_significant_moves_for_date(date: str, threshold_std: float = 2.0,
                                   window_days: int = 60) -> Dict:
    """
    Get all significant moves for a given date.
    
    Returns:
        {
            "date": date,
            "significant_tenors": [list of tenors with significant moves],
            "moves": {
                "tenor": {
                    "change_bps": float,
                    "is_significant": bool,
                    "stats": {...}
                }
            }
        }
    """
    conn = get_conn()
    c = conn.cursor()
    
    row = c.execute("""
        SELECT delta_zeros_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (date,)).fetchone()
    
    conn.close()
    
    if not row:
        return None
    
    try:
        delta_zeros = json.loads(row["delta_zeros_pct"])
    except:
        return None
    
    result = {
        "date": date,
        "significant_tenors": [],
        "moves": {}
    }
    
    # Check each tenor
    for tenor in TENORS:
        # Get change for this tenor
        change_bps = None
        tenor_key = tenor.lower().replace("M", "m").replace("Y", "y")
        
        if tenor_key in delta_zeros:
            change_bps = float(delta_zeros[tenor_key]) * 100
        elif tenor.upper() in delta_zeros:
            change_bps = float(delta_zeros[tenor.upper()]) * 100
        elif tenor.lower() in delta_zeros:
            change_bps = float(delta_zeros[tenor.lower()]) * 100
        
        if change_bps is None:
            continue
        
        # Check if significant
        is_sig, stats = is_significant_move(tenor, change_bps, threshold_std, 
                                           window_days=window_days, target_date=date)
        
        result["moves"][tenor] = {
            "change_bps": change_bps,
            "is_significant": is_sig,
            "stats": stats
        }
        
        if is_sig:
            result["significant_tenors"].append(tenor)
    
    return result

def filter_training_dates_by_significance(start_date: str, end_date: str,
                                         threshold_std: float = 2.0,
                                         min_significant_tenors: int = 1) -> List[str]:
    """
    Filter dates to only include those with significant yield movements.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        threshold_std: Standard deviation threshold
        min_significant_tenors: Minimum number of tenors with significant moves
    
    Returns:
        List of dates with significant moves
    """
    conn = get_conn()
    c = conn.cursor()
    
    dates = c.execute("""
        SELECT DISTINCT date
        FROM yield_curve_daily
        WHERE date >= ? AND date <= ?
        AND delta_zeros_pct IS NOT NULL
        ORDER BY date
    """, (start_date, end_date)).fetchall()
    
    conn.close()
    
    significant_dates = []
    
    for row in dates:
        date = row["date"]
        moves = get_significant_moves_for_date(date, threshold_std)
        
        if moves and len(moves["significant_tenors"]) >= min_significant_tenors:
            significant_dates.append(date)
    
    return significant_dates

def should_train_on_date(date: str, threshold_std: float = 2.0,
                        min_significant_tenors: int = 1,
                        window_days: int = 60) -> Tuple[bool, Dict]:
    """
    Determine if model should train on a given date based on significance.
    
    Returns:
        (should_train, significance_info)
    """
    moves = get_significant_moves_for_date(date, threshold_std, window_days=window_days)
    
    if not moves:
        return False, {"reason": "no_yield_data"}
    
    num_significant = len(moves["significant_tenors"])
    should_train = num_significant >= min_significant_tenors
    
    return should_train, {
        "significant_tenors": moves["significant_tenors"],
        "num_significant": num_significant,
        "all_moves": moves["moves"]
    }

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Analyze significant yield movements")
    ap.add_argument("--date", type=str, help="Date to check (YYYY-MM-DD)")
    ap.add_argument("--start-date", type=str, help="Start date for range analysis")
    ap.add_argument("--end-date", type=str, help="End date for range analysis")
    ap.add_argument("--threshold-std", type=float, default=2.0, help="Standard deviation threshold")
    ap.add_argument("--filter-training", action="store_true", help="Filter training dates by significance")
    args = ap.parse_args()
    
    if args.date:
        moves = get_significant_moves_for_date(args.date, args.threshold_std)
        if moves:
            print(f"\nSignificant Moves for {args.date} (threshold: {args.threshold_std}σ):")
            print("=" * 70)
            for tenor, move_info in moves["moves"].items():
                sig_marker = "***" if move_info["is_significant"] else ""
                print(f"{tenor}: {move_info['change_bps']:+.2f} bps {sig_marker}")
                if move_info["is_significant"]:
                    stats = move_info["stats"]
                    print(f"  Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}, Threshold: ±{stats['threshold_bps']:.2f} bps")
            
            print(f"\nSignificant tenors: {', '.join(moves['significant_tenors']) if moves['significant_tenors'] else 'None'}")
    
    elif args.start_date and args.end_date:
        if args.filter_training:
            significant_dates = filter_training_dates_by_significance(
                args.start_date, args.end_date, args.threshold_std
            )
            print(f"\nDates with significant moves ({args.threshold_std}σ): {len(significant_dates)}")
            print(f"Date range: {args.start_date} to {args.end_date}")
            for date in significant_dates[:20]:
                print(f"  {date}")
            if len(significant_dates) > 20:
                print(f"  ... and {len(significant_dates) - 20} more")
        else:
            # Analyze range
            conn = get_conn()
            c = conn.cursor()
            dates = c.execute("""
                SELECT DISTINCT date
                FROM yield_curve_daily
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (args.start_date, args.end_date)).fetchall()
            conn.close()
            
            significant_count = 0
            for row in dates:
                moves = get_significant_moves_for_date(row["date"], args.threshold_std)
                if moves and moves["significant_tenors"]:
                    significant_count += 1
            
            print(f"\nRange Analysis: {args.start_date} to {args.end_date}")
            print(f"Total dates: {len(dates)}")
            print(f"Dates with significant moves: {significant_count} ({100*significant_count/len(dates):.1f}%)")

if __name__ == "__main__":
    main()

