#!/usr/bin/env python3
"""
Export News Data for Scenario Generation
Exports collected news data in a clean JSON format for Charles's scenario generation pipeline.
"""

import json
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional
from db import get_conn
from bucket_news import get_bucket_counts, BUCKETS
from analyze_yield_impact import get_bucketed_news, load_curve_snapshot

def export_news_data(start_date: Optional[str] = None, end_date: Optional[str] = None, 
                     output_path: Optional[str] = None) -> Dict:
    """
    Export news data in a format suitable for scenario generation.
    
    Returns a dictionary with:
    - metadata: export info, date range, total articles
    - daily_data: list of daily summaries with:
      - date
      - bucket_counts: count of articles per bucket
      - articles_by_bucket: articles grouped by bucket (title, summary, source, url)
      - llm_analysis: yield impact predictions if available
      - yield_curve_snapshot: current yield curve data if available
    """
    if start_date is None:
        start_date = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    if end_date is None:
        end_date = dt.date.today().isoformat()
    
    # Get all dates with articles
    conn = get_conn()
    cursor = conn.cursor()
    
    dates = cursor.execute("""
        SELECT DISTINCT DATE(COALESCE(published_at, fetched_at)) as date
        FROM articles
        WHERE DATE(COALESCE(published_at, fetched_at)) >= ? 
          AND DATE(COALESCE(published_at, fetched_at)) <= ?
        ORDER BY date DESC
    """, (start_date, end_date)).fetchall()
    
    dates_list = [row[0] for row in dates]
    
    # Build export structure
    export_data = {
        "metadata": {
            "export_date": dt.datetime.now().isoformat(),
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "total_dates": len(dates_list),
            "buckets": BUCKETS,
            "description": "News data exported for scenario generation pipeline"
        },
        "daily_data": []
    }
    
    # Process each date
    for date in dates_list:
        daily_summary = {
            "date": date,
            "bucket_counts": {},
            "articles_by_bucket": {},
            "llm_analysis": None,
            "yield_curve_snapshot": None
        }
        
        # Get bucket counts
        bucket_counts = get_bucket_counts(date)
        daily_summary["bucket_counts"] = bucket_counts
        
        # Get articles by bucket
        bucketed_news = get_bucketed_news(date)
        for bucket, articles in bucketed_news.items():
            # Filter out articles with null or empty titles
            daily_summary["articles_by_bucket"][bucket] = [
                {
                    "title": art.get("title", ""),
                    "summary": art.get("summary", ""),
                    "source": art.get("source", ""),
                    "url": art.get("url", ""),
                    "bucket_confidence": art.get("bucket_confidence")
                }
                for art in articles
                if art.get("title") and art.get("title").strip()
            ]
        
        # Try to load LLM analysis if available
        analysis_path = Path(__file__).parent / "analyses" / f"yield_impact_{date}.json"
        if analysis_path.exists():
            try:
                with open(analysis_path) as f:
                    analysis = json.load(f)
                    daily_summary["llm_analysis"] = {
                        "predictions": analysis.get("predictions", {}),
                        "summary": analysis.get("summary", ""),
                        "timestamp": analysis.get("timestamp", "")
                    }
            except Exception as e:
                print(f"[WARN] Could not load analysis for {date}: {e}")
        
        # Try to load yield curve snapshot
        curve = load_curve_snapshot(date)
        if curve:
            daily_summary["yield_curve_snapshot"] = {
                "today": curve.get("today", {}),
                "yesterday": curve.get("yesterday", {}),
                "delta": curve.get("delta", {})
            }
        
        export_data["daily_data"].append(daily_summary)
    
    conn.close()
    
    # Write to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"[EXPORT] News data exported to {output_file}")
        print(f"[EXPORT] {len(dates_list)} dates, {sum(len(d['articles_by_bucket']) for d in export_data['daily_data'])} total articles")
    
    return export_data

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Export news data for scenario generation")
    ap.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD), defaults to 30 days ago")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--output", type=str, default="news_export_for_scenario_gen.json",
                   help="Output JSON file path")
    args = ap.parse_args()
    
    export_news_data(args.start_date, args.end_date, args.output)

if __name__ == "__main__":
    main()

