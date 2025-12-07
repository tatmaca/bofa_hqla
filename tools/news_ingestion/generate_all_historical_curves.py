#!/usr/bin/env python3
"""
Generate All Historical Scenario Curves
Orchestrates the full process of extracting factors and generating scenario curves
for all historical dates with available news data.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from batch_extract_factors import extract_factors_for_date_range, identify_dates_needing_extraction
from batch_generate_scenario_curves import generate_curves_for_date_range


def generate_all_historical_curves(start_date: str,
                                   end_date: str,
                                   scenarios_path: Optional[str] = None,
                                   output_dir: Optional[Path] = None,
                                   extract_factors: bool = True,
                                   overwrite_curves: bool = False,
                                   combine_with_news: bool = False,
                                   dry_run: bool = False) -> Dict:
    """
    Orchestrate the full process:
    1. Identify dates needing factor extraction
    2. Extract factors for missing dates (if requested)
    3. Generate scenario curves for all dates
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenarios_path: Path to scenarios JSONL file
        output_dir: Output directory for scenario curves
        extract_factors: If True, extract factors for dates that need them
        overwrite_curves: If True, regenerate curves even if they exist
        combine_with_news: Whether to combine scenario factors with news factors
        dry_run: If True, only report what would be done
    
    Returns:
        Dictionary with overall results
    """
    print("="*80)
    print("GENERATE ALL HISTORICAL SCENARIO CURVES")
    print("="*80)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Extract factors: {extract_factors}")
    print(f"Overwrite existing curves: {overwrite_curves}")
    print(f"Dry run: {dry_run}")
    print("="*80)
    print()
    
    overall_results = {
        "factor_extraction": {},
        "curve_generation": {},
        "total_dates": 0,
        "successful_dates": [],
        "failed_dates": []
    }
    
    # Step 1: Identify dates needing factor extraction
    if extract_factors:
        print("Step 1: Identifying dates needing factor extraction...")
        dates_needing_extraction = identify_dates_needing_extraction(start_date, end_date)
        
        if dates_needing_extraction:
            print(f"Found {len(dates_needing_extraction)} dates needing factor extraction:")
            for date in dates_needing_extraction[:10]:  # Show first 10
                print(f"  - {date}")
            if len(dates_needing_extraction) > 10:
                print(f"  ... and {len(dates_needing_extraction) - 10} more")
            print()
            
            # Extract factors
            print("Step 2: Extracting factors for missing dates...")
            extraction_results = extract_factors_for_date_range(
                start_date,
                end_date,
                dry_run=dry_run
            )
            overall_results["factor_extraction"] = extraction_results
            
            if extraction_results["failed"]:
                print(f"[WARN] Factor extraction failed for {len(extraction_results['failed'])} dates")
                print("These dates may still be able to generate curves using cold-start coefficients")
                print()
        else:
            print("All dates already have factors extracted")
            print()
    else:
        print("Skipping factor extraction (--no-extract-factors specified)")
        print()
    
    # Step 3: Generate scenario curves
    print("Step 3: Generating scenario curves for all dates...")
    generation_results = generate_curves_for_date_range(
        start_date,
        end_date,
        scenarios_path=scenarios_path,
        output_dir=output_dir,
        overwrite=overwrite_curves,
        combine_with_news=combine_with_news
    )
    overall_results["curve_generation"] = generation_results
    overall_results["total_dates"] = generation_results["total_dates"]
    overall_results["successful_dates"] = generation_results["successful"]
    overall_results["failed_dates"] = list(generation_results["failed"].keys())
    
    # Final summary
    print()
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total dates with news: {overall_results['total_dates']}")
    print(f"Successfully generated curves: {len(overall_results['successful_dates'])}")
    print(f"Failed to generate curves: {len(overall_results['failed_dates'])}")
    
    if overall_results["factor_extraction"]:
        extraction = overall_results["factor_extraction"]
        print(f"Factor extraction - successful: {len(extraction.get('successful', []))}")
        print(f"Factor extraction - failed: {len(extraction.get('failed', {}))}")
    
    print("="*80)
    print()
    
    if overall_results["successful_dates"]:
        print("Successfully generated curves for:")
        for date in overall_results["successful_dates"][:10]:
            print(f"  - {date}")
        if len(overall_results["successful_dates"]) > 10:
            print(f"  ... and {len(overall_results['successful_dates']) - 10} more")
        print()
    
    if overall_results["failed_dates"]:
        print("Failed to generate curves for:")
        for date in overall_results["failed_dates"][:10]:
            error = generation_results["failed"].get(date, "Unknown error")
            print(f"  - {date}: {error}")
        if len(overall_results["failed_dates"]) > 10:
            print(f"  ... and {len(overall_results['failed_dates']) - 10} more")
        print()
    
    return overall_results


def main():
    """Main entry point."""
    ap = argparse.ArgumentParser(
        description="Generate all historical scenario curves",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate curves for all dates (extract factors if needed)
  python3 generate_all_historical_curves.py --start-date 2025-11-06 --end-date 2025-12-04

  # Skip factor extraction (only generate for dates with existing factors)
  python3 generate_all_historical_curves.py --start-date 2025-11-06 --end-date 2025-12-04 --no-extract-factors

  # Overwrite existing curves
  python3 generate_all_historical_curves.py --start-date 2025-11-06 --end-date 2025-12-04 --overwrite

  # Dry run to see what would be done
  python3 generate_all_historical_curves.py --start-date 2025-11-06 --end-date 2025-12-04 --dry-run
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
        "--no-extract-factors",
        action="store_true",
        help="Skip factor extraction (only generate curves for dates with existing factors)"
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
    
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be done without actually doing it"
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
    
    # Run the full process
    results = generate_all_historical_curves(
        args.start_date,
        args.end_date,
        scenarios_path=args.scenarios_path,
        output_dir=output_dir,
        extract_factors=not args.no_extract_factors,
        overwrite_curves=args.overwrite,
        combine_with_news=args.combine_with_news,
        dry_run=args.dry_run
    )
    
    # Exit with error code if any failed
    if results["failed_dates"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

