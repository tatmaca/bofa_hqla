#!/usr/bin/env python3
"""
Status Checker for Daily Pipeline
Shows recent runs, data counts, and system health.
"""

import os
import sys
import datetime as dt
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

def check_recent_runs(days=7):
    """Check recent ingestion runs."""
    conn = get_conn()
    cursor = conn.cursor()
    
    cutoff = (dt.date.today() - timedelta(days=days)).isoformat()
    runs = cursor.execute("""
        SELECT run_date, started_at, completed_at, status, total_new_articles, error_message
        FROM ingestion_runs
        WHERE run_date >= ?
        ORDER BY run_date DESC
    """, (cutoff,)).fetchall()
    
    conn.close()
    return runs

def get_data_counts():
    """Get current data counts."""
    conn = get_conn()
    cursor = conn.cursor()
    
    counts = {
        "articles": cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "bucketed": cursor.execute("SELECT COUNT(*) FROM articles WHERE bucket IS NOT NULL").fetchone()[0],
        "yield_dates": cursor.execute("SELECT COUNT(*) FROM yield_curve_daily").fetchone()[0],
        "training_records": cursor.execute("SELECT COUNT(*) FROM news_yield_training").fetchone()[0],
    }
    
    # Date ranges
    article_dates = cursor.execute("""
        SELECT MIN(DATE(published_at)), MAX(DATE(published_at))
        FROM articles WHERE published_at IS NOT NULL
    """).fetchone()
    
    yield_dates = cursor.execute("""
        SELECT MIN(date), MAX(date) FROM yield_curve_daily
    """).fetchone()
    
    conn.close()
    
    counts["article_date_range"] = article_dates
    counts["yield_date_range"] = yield_dates
    
    return counts

def check_logs(days=7):
    """Check recent log files."""
    log_dir = Path(__file__).parent / "logs"
    if not log_dir.exists():
        return []
    
    cutoff = dt.date.today() - timedelta(days=days)
    logs = []
    
    for log_file in sorted(log_dir.glob("daily_pipeline_*.log"), reverse=True):
        try:
            date_str = log_file.stem.replace("daily_pipeline_", "")
            log_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            if log_date >= cutoff:
                size = log_file.stat().st_size
                logs.append((log_date, log_file, size))
        except:
            pass
    
    return logs

def check_missing_data(days_back=7):
    """Check for missing snapshots and analyses."""
    repo_root = Path(__file__).parent.parent.parent
    snapshots_dir = repo_root / "tools" / "ust_curve" / "llm" / "snapshots"
    analyses_dir = Path(__file__).parent / "analyses"
    
    # Get business days
    today = dt.date.today()
    dates = []
    current = today
    for _ in range(days_back * 2):
        if current.weekday() < 5:  # Business day
            dates.append(current.isoformat())
        if len(dates) >= days_back:
            break
        current -= timedelta(days=1)
    
    missing_snapshots = []
    missing_analyses = []
    
    for date in dates:
        snapshot_path = snapshots_dir / f"curve_snapshot_{date}.json"
        analysis_path = analyses_dir / f"yield_impact_{date}.json"
        
        if not snapshot_path.exists():
            missing_snapshots.append(date)
        if not analysis_path.exists():
            missing_analyses.append(date)
    
    return {
        "missing_snapshots": sorted(missing_snapshots),
        "missing_analyses": sorted(missing_analyses),
        "total_checked": len(dates)
    }

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Check daily pipeline status")
    ap.add_argument("--days", type=int, default=7, help="Days to look back")
    args = ap.parse_args()
    
    print(f"\n{'='*70}")
    print(f"DAILY PIPELINE STATUS")
    print(f"{'='*70}\n")
    
    # Data counts
    print("📊 DATA COUNTS")
    print("-" * 70)
    counts = get_data_counts()
    print(f"  Articles: {counts['articles']:,}")
    print(f"  Bucketed: {counts['bucketed']:,}")
    print(f"  Yield curve dates: {counts['yield_dates']}")
    print(f"  Training records: {counts['training_records']:,}")
    
    if counts["article_date_range"][0]:
        print(f"\n  Article date range: {counts['article_date_range'][0]} to {counts['article_date_range'][1]}")
    if counts["yield_date_range"][0]:
        print(f"  Yield curve range: {counts['yield_date_range'][0]} to {counts['yield_date_range'][1]}")
    
    # Recent runs
    print(f"\n📅 RECENT RUNS (last {args.days} days)")
    print("-" * 70)
    runs = check_recent_runs(args.days)
    
    if not runs:
        print("  No runs found")
    else:
        for run in runs:
            run_date, started, completed, status, articles, error = run
            status_icon = "✓" if status == "completed" else "✗"
            print(f"  {status_icon} {run_date}: {status} ({articles} articles)")
            if error:
                print(f"      Error: {error[:60]}")
    
    # Logs
    print(f"\n📝 RECENT LOGS (last {args.days} days)")
    print("-" * 70)
    logs = check_logs(args.days)
    
    if not logs:
        print("  No log files found")
    else:
        for log_date, log_file, size in logs[:5]:
            size_kb = size / 1024
            print(f"  {log_date}: {log_file.name} ({size_kb:.1f} KB)")
    
    # Health check
    print(f"\n💚 HEALTH CHECK")
    print("-" * 70)
    
    today = dt.date.today()
    today_runs = [r for r in runs if r[0] == today.isoformat()]
    
    if today_runs:
        latest = today_runs[0]
        if latest[3] == "completed":
            print("  ✓ Today's run completed successfully")
        else:
            print(f"  ✗ Today's run status: {latest[3]}")
    else:
        print("  ⚠ No run today yet")
    
    # Check for recent data
    if counts["article_date_range"][1]:
        latest_article_date = dt.datetime.strptime(counts["article_date_range"][1], "%Y-%m-%d").date()
        days_old = (today - latest_article_date).days
        if days_old == 0:
            print("  ✓ Articles from today")
        elif days_old <= 2:
            print(f"  ⚠ Latest articles are {days_old} day(s) old")
        else:
            print(f"  ✗ Latest articles are {days_old} days old")
    
    # Check for missing data
    print(f"\n🔍 MISSING DATA CHECK (last {args.days} days)")
    print("-" * 70)
    try:
        missing = check_missing_data(args.days)
        if missing["missing_snapshots"]:
            print(f"  ⚠ Missing {len(missing['missing_snapshots'])} yield curve snapshots:")
            for date in missing["missing_snapshots"][:5]:
                print(f"     - {date}")
            if len(missing["missing_snapshots"]) > 5:
                print(f"     ... and {len(missing['missing_snapshots']) - 5} more")
        else:
            print("  ✓ All yield curve snapshots exist")
        
        if missing["missing_analyses"]:
            print(f"\n  ⚠ Missing {len(missing['missing_analyses'])} news analyses:")
            for date in missing["missing_analyses"][:5]:
                print(f"     - {date}")
            if len(missing["missing_analyses"]) > 5:
                print(f"     ... and {len(missing['missing_analyses']) - 5} more")
        else:
            print("  ✓ All news analyses exist")
        
        if missing["missing_snapshots"] or missing["missing_analyses"]:
            print(f"\n  💡 Run catch-up script to fill missing data:")
            print(f"     python3 catch_up_missing_data.py --days-back {args.days}")
    except Exception as e:
        print(f"  ⚠ Could not check missing data: {e}")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()

