#!/usr/bin/env python3
"""
Batch Scenario Curve Generation
Generates scenario-based yield curve predictions for multiple dates in batch.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from db import get_conn
from generate_scenario_predictions import generate_all_scenario_curves
from load_scenarios import get_default_scenarios_path


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


def get_existing_curve_files(output_dir: Path) -> set:
    """
    Get set of dates that already have scenario curve files.
    
    Args:
        output_dir: Directory containing scenario curve files
    
    Returns:
        Set of date strings (from filenames)
    """
    if not output_dir.exists():
        return set()
    
    existing_dates = set()
    for file_path in output_dir.glob("scenario_curves_*.json"):
        # Extract date from filename: scenario_curves_YYYY-MM-DD.json
        try:
            date_str = file_path.stem.replace("scenario_curves_", "")
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate format
            existing_dates.add(date_str)
        except ValueError:
            continue
    
    return existing_dates


def generate_curves_for_date_range(start_date: str,
                                   end_date: str,
                                   scenarios_path: Optional[str] = None,
                                   output_dir: Optional[Path] = None,
                                   overwrite: bool = False,
                                   combine_with_news: bool = False) -> Dict[str, Dict]:
    """
    Generate scenario curves for all dates in range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenarios_path: Path to scenarios JSONL file (if None, uses default)
        output_dir: Output directory (if None, uses default)
        overwrite: If True, regenerate curves even if they already exist
        combine_with_news: Whether to combine scenario factors with news factors
    
    Returns:
        Dictionary with generation results:
        {
            "total_dates": int,
            "successful": List[str],
            "failed": Dict[str, str],  # {date: error_message}
            "skipped": List[str]  # dates that already have curves
        }
    """
    # Get dates with news
    dates_with_news = get_dates_with_news(start_date, end_date)
    
    if not dates_with_news:
        print(f"[WARN] No dates with news articles found in range {start_date} to {end_date}")
        return {
            "total_dates": 0,
            "successful": [],
            "failed": {},
            "skipped": []
        }
    
    # Determine output directory
    if output_dir is None:
        output_dir = Path(__file__).parent / "scenario_predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get existing curve files
    existing_dates = get_existing_curve_files(output_dir) if not overwrite else set()
    
    # Determine scenarios path
    if not scenarios_path:
        default_path = get_default_scenarios_path()
        if default_path:
            scenarios_path = str(default_path)
        else:
            print("[ERROR] No scenarios path provided and default not found")
            return {
                "total_dates": len(dates_with_news),
                "successful": [],
                "failed": {"all": "Scenarios file not found"},
                "skipped": []
            }
    
    if not Path(scenarios_path).exists():
        print(f"[ERROR] Scenarios file not found: {scenarios_path}")
        return {
            "total_dates": len(dates_with_news),
            "successful": [],
            "failed": {"all": f"Scenarios file not found: {scenarios_path}"},
            "skipped": []
        }
    
    print(f"\n{'='*60}")
    print(f"BATCH SCENARIO CURVE GENERATION")
    print(f"{'='*60}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total dates with news: {len(dates_with_news)}")
    print(f"Dates with existing curves: {len(existing_dates)}")
    print(f"Overwrite existing: {overwrite}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")
    
    # Generate curves for each date
    successful = []
    failed = {}
    skipped = []
    
    for i, date in enumerate(dates_with_news, 1):
        # Check if already exists
        if date in existing_dates and not overwrite:
            print(f"[{i}/{len(dates_with_news)}] Skipping {date} (curve already exists)")
            skipped.append(date)
            continue
        
        print(f"[{i}/{len(dates_with_news)}] Generating curves for {date}...")
        try:
            curves = generate_all_scenario_curves(
                date,
                scenarios_path,
                combine_with_news=combine_with_news
            )
            
            if curves:
                output_path = output_dir / f"scenario_curves_{date}.json"
                with open(output_path, 'w') as f:
                    json.dump(curves, f, indent=2)
                
                num_scenarios = len([k for k in curves.keys() 
                                   if k not in ["date", "base_date", "prediction_date", "baseline"]])
                print(f"[OK] Generated {num_scenarios + 1} curves for {date} (saved to {output_path})")
                successful.append(date)
            else:
                error_msg = "generate_all_scenario_curves returned None"
                print(f"[ERROR] Failed to generate curves for {date}: {error_msg}")
                failed[date] = error_msg
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Failed to generate curves for {date}: {error_msg}")
            failed[date] = error_msg
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total dates processed: {len(dates_with_news)}")
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
        "total_dates": len(dates_with_news),
        "successful": successful,
        "failed": failed,
        "skipped": skipped
    }


def main():
    """Main entry point for batch scenario curve generation."""
    ap = argparse.ArgumentParser(
        description="Batch generate scenario curves for historical dates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate curves for all dates in range
  python3 batch_generate_scenario_curves.py --start-date 2025-11-06 --end-date 2025-12-04

  # Overwrite existing curves
  python3 batch_generate_scenario_curves.py --start-date 2025-11-06 --end-date 2025-12-04 --overwrite

  # Specify custom output directory
  python3 batch_generate_scenario_curves.py --start-date 2025-11-06 --end-date 2025-12-04 --output-dir /path/to/output
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
        "--scenarios-path",
        type=str,
        help="Path to scenarios JSONL file (if not provided, uses default)"
    )
    
    ap.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for scenario curves (default: scenario_predictions/)"
    )
    
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing curve files"
    )
    
    ap.add_argument(
        "--combine-with-news",
        action="store_true",
        help="Combine scenario factors with day's news factors"
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
    
    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    # Generate curves
    results = generate_curves_for_date_range(
        args.start_date,
        args.end_date,
        scenarios_path=args.scenarios_path,
        output_dir=output_dir,
        overwrite=args.overwrite,
        combine_with_news=args.combine_with_news
    )
    
    # Exit with error code if any failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

