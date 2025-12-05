#!/usr/bin/env python3
"""
Batch Accuracy Calculation
Calculates accuracy metrics for all scenario curves in a date range.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from calculate_prediction_accuracy import calculate_accuracy_for_scenario_curves
from db import get_conn


def get_dates_with_scenario_curves(start_date: str, end_date: str) -> List[str]:
    """
    Get all dates with scenario curve files in the specified range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        List of date strings in chronological order
    """
    scenario_dir = Path(__file__).parent / "scenario_predictions"
    if not scenario_dir.exists():
        return []
    
    dates = []
    for file_path in scenario_dir.glob("scenario_curves_*.json"):
        try:
            date_str = file_path.stem.replace("scenario_curves_", "")
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate format
            if start_date <= date_str <= end_date:
                dates.append(date_str)
        except ValueError:
            continue
    
    return sorted(dates)


def batch_calculate_accuracy(start_date: str,
                            end_date: str,
                            overwrite: bool = False) -> Dict[str, Dict]:
    """
    Calculate accuracy for all scenario curves in date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        overwrite: If True, recalculate even if accuracy already exists
    
    Returns:
        Dictionary with results:
        {
            "total_dates": int,
            "successful": List[str],
            "failed": Dict[str, str],
            "skipped": List[str]
        }
    """
    dates = get_dates_with_scenario_curves(start_date, end_date)
    
    if not dates:
        print(f"[WARN] No scenario curve files found in range {start_date} to {end_date}")
        return {
            "total_dates": 0,
            "successful": [],
            "failed": {},
            "skipped": []
        }
    
    # Check which dates already have accuracy data
    existing_dates = set()
    if not overwrite:
        conn = get_conn()
        c = conn.cursor()
        rows = c.execute("""
            SELECT DISTINCT date
            FROM daily_accuracy_summary
            WHERE date >= ? AND date <= ?
        """, (start_date, end_date)).fetchall()
        existing_dates = {row["date"] for row in rows}
        conn.close()
    
    print(f"\n{'='*60}")
    print(f"BATCH ACCURACY CALCULATION")
    print(f"{'='*60}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total dates with curves: {len(dates)}")
    print(f"Dates with existing accuracy: {len(existing_dates)}")
    print(f"Overwrite existing: {overwrite}")
    print(f"{'='*60}\n")
    
    successful = []
    failed = {}
    skipped = []
    
    for i, date in enumerate(dates, 1):
        if date in existing_dates and not overwrite:
            print(f"[{i}/{len(dates)}] Skipping {date} (accuracy already calculated)")
            skipped.append(date)
            continue
        
        print(f"[{i}/{len(dates)}] Calculating accuracy for {date}...")
        try:
            results = calculate_accuracy_for_scenario_curves(date)
            
            if results:
                num_scenarios = len(results)
                print(f"[OK] Calculated accuracy for {num_scenarios} scenarios")
                
                # Show summary
                baseline_mae = results.get("baseline", {}).get("mae_bps")
                if baseline_mae is not None:
                    print(f"     Baseline MAE: {baseline_mae:.2f} bps")
                
                successful.append(date)
            else:
                error_msg = "No accuracy calculated (missing actuals or predictions)"
                print(f"[WARN] {error_msg}")
                failed[date] = error_msg
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Failed to calculate accuracy for {date}: {error_msg}")
            failed[date] = error_msg
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"CALCULATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total dates processed: {len(dates)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Skipped (already exist): {len(skipped)}")
    print(f"{'='*60}\n")
    
    if failed:
        print("Failed dates:")
        for date, error in failed.items():
            print(f"  {date}: {error}")
        print()
    
    return {
        "total_dates": len(dates),
        "successful": successful,
        "failed": failed,
        "skipped": skipped
    }


def main():
    """Main entry point for batch accuracy calculation."""
    ap = argparse.ArgumentParser(
        description="Batch calculate accuracy for scenario curves",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate accuracy for all dates in range
  python3 batch_calculate_accuracy.py --start-date 2025-11-06 --end-date 2025-12-04

  # Overwrite existing accuracy calculations
  python3 batch_calculate_accuracy.py --start-date 2025-11-06 --end-date 2025-12-04 --overwrite
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
        "--overwrite",
        action="store_true",
        help="Overwrite existing accuracy calculations"
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
    
    # Calculate accuracy
    results = batch_calculate_accuracy(
        args.start_date,
        args.end_date,
        overwrite=args.overwrite
    )
    
    # Exit with error code if any failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

