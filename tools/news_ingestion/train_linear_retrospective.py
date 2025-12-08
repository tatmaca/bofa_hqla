#!/usr/bin/env python3
"""
Retrospective Linear Model Training
Trains the linear online learning model on all available historical dates.
Processes dates in chronological order to simulate online learning.
"""

import os
import sys
import datetime as dt
from pathlib import Path
from typing import List, Optional
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn
from train_linear_online import train_linear_model_for_date, get_daily_factor_scores, get_actual_yield_changes

def get_available_training_dates(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
    """
    Get dates that have both factor scores and yield curve data.
    """
    conn = get_conn()
    c = conn.cursor()
    
    # Get dates with factor scores
    factor_dates = c.execute("""
        SELECT DISTINCT date
        FROM daily_factor_scores
        WHERE date IS NOT NULL
    """).fetchall()
    factor_date_set = {row["date"] for row in factor_dates}
    
    # Get dates with yield curve data
    yield_dates = c.execute("""
        SELECT DISTINCT date
        FROM yield_curve_daily
        WHERE date IS NOT NULL
        AND delta_zeros_pct IS NOT NULL
    """).fetchall()
    yield_date_set = {row["date"] for row in yield_dates}
    
    # Intersection: dates with both
    available_dates = sorted(list(factor_date_set & yield_date_set))
    
    # Filter by date range if provided
    if start_date:
        available_dates = [d for d in available_dates if d >= start_date]
    if end_date:
        available_dates = [d for d in available_dates if d <= end_date]
    
    conn.close()
    
    return available_dates

def train_retrospective(start_date: Optional[str] = None, 
                       end_date: Optional[str] = None,
                       skip_existing: bool = True,
                       check_significance: bool = True,
                       threshold_std: float = 2.0) -> dict:
    """
    Train linear model retrospectively on all available dates.
    
    Args:
        start_date: Start date (YYYY-MM-DD), defaults to earliest available
        end_date: End date (YYYY-MM-DD), defaults to latest available
        skip_existing: If True, skip dates that already have coefficients
    
    Returns:
        Dictionary with training statistics
    """
    print("=" * 70)
    print("RETROSPECTIVE LINEAR MODEL TRAINING")
    print("=" * 70)
    
    # Get available dates
    available_dates = get_available_training_dates(start_date, end_date)
    
    if not available_dates:
        print("[ERROR] No dates found with both factor scores and yield curve data")
        return {"success": False, "error": "No training data available"}
    
    print(f"\n[INFO] Found {len(available_dates)} dates with training data")
    print(f"[INFO] Date range: {available_dates[0]} to {available_dates[-1]}")
    
    # Check which dates already have coefficients
    if skip_existing:
        conn = get_conn()
        c = conn.cursor()
        existing_dates = c.execute("""
            SELECT DISTINCT date
            FROM linear_model_coefficients
        """).fetchall()
        existing_date_set = {row["date"] for row in existing_dates}
        conn.close()
        
        dates_to_train = [d for d in available_dates if d not in existing_date_set]
        print(f"[INFO] {len(existing_date_set)} dates already trained, {len(dates_to_train)} dates to train")
    else:
        dates_to_train = available_dates
        print(f"[INFO] Training all {len(dates_to_train)} dates (including re-training existing)")
    
    if not dates_to_train:
        print("[INFO] All dates already trained")
        return {"success": True, "trained": 0, "skipped": len(available_dates)}
    
    # Train in chronological order (important for online learning)
    if check_significance:
        print(f"\n[INFO] Filtering by significance (threshold: {threshold_std}σ)...")
        from yield_movement_thresholds import filter_training_dates_by_significance
        significant_dates = filter_training_dates_by_significance(
            dates_to_train[0] if dates_to_train else start_date or "",
            dates_to_train[-1] if dates_to_train else end_date or "",
            threshold_std
        )
        dates_to_train = [d for d in dates_to_train if d in significant_dates]
        print(f"[INFO] {len(dates_to_train)} dates with significant moves (filtered from {len(available_dates)} total)")
    
    print(f"\n[INFO] Training in chronological order...")
    print("=" * 70)
    
    trained_count = 0
    failed_count = 0
    skipped_count = 0
    failed_dates = []
    
    for i, date in enumerate(dates_to_train, 1):
        print(f"\n[{i}/{len(dates_to_train)}] Training for {date}...")
        
        try:
            success = train_linear_model_for_date(date, check_significance=check_significance, 
                                                 threshold_std=threshold_std)
            if success:
                trained_count += 1
                print(f"[OK] Successfully trained for {date}")
            else:
                if check_significance:
                    skipped_count += 1
                    print(f"[SKIP] Skipped {date} (no significant moves)")
                else:
                    failed_count += 1
                    failed_dates.append(date)
                    print(f"[WARN] Training failed for {date} (may be missing data)")
        except Exception as e:
            failed_count += 1
            failed_dates.append(date)
            print(f"[ERROR] Exception training {date}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"Total dates available: {len(available_dates)}")
    print(f"Dates trained: {trained_count}")
    if check_significance:
        print(f"Dates skipped (insignificant): {skipped_count}")
    print(f"Dates failed: {failed_count}")
    if failed_dates:
        print(f"\nFailed dates: {', '.join(failed_dates[:10])}")
        if len(failed_dates) > 10:
            print(f"... and {len(failed_dates) - 10} more")
    
    return {
        "success": True,
        "total_available": len(available_dates),
        "trained": trained_count,
        "skipped": skipped_count if check_significance else 0,
        "failed": failed_count,
        "failed_dates": failed_dates
    }

def main():
    ap = argparse.ArgumentParser(description="Train linear model retrospectively on historical dates")
    ap.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD), defaults to earliest available")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to latest available")
    ap.add_argument("--no-skip-existing", action="store_true", help="Re-train dates that already have coefficients")
    ap.add_argument("--no-significance-filter", action="store_true", help="Train on all dates, not just significant moves")
    ap.add_argument("--threshold-std", type=float, default=2.0, help="Standard deviation threshold for significance (default: 2.0)")
    args = ap.parse_args()
    
    result = train_retrospective(
        start_date=args.start_date,
        end_date=args.end_date,
        skip_existing=not args.no_skip_existing,
        check_significance=not args.no_significance_filter,
        threshold_std=args.threshold_std
    )
    
    if not result.get("success"):
        sys.exit(1)

if __name__ == "__main__":
    main()

