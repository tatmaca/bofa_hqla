#!/usr/bin/env python3
"""
Comprehensive Health Check Script
Checks all aspects of the daily pipeline system.
"""

import os
import sys
import datetime as dt
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

def check_database():
    """Check database health."""
    print("[DATA] DATABASE HEALTH")
    print("-" * 70)
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Check tables exist
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        table_names = [t[0] for t in tables]
        print(f"  [OK] Tables: {', '.join(table_names)}")
        
        # Counts
        counts = {
            "articles": cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
            "bucketed": cursor.execute("SELECT COUNT(*) FROM articles WHERE bucket IS NOT NULL").fetchone()[0],
            "runs": cursor.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0],
            "yield_dates": cursor.execute("SELECT COUNT(*) FROM yield_curve_daily").fetchone()[0],
            "training": cursor.execute("SELECT COUNT(*) FROM news_yield_training").fetchone()[0],
        }
        
        print(f"  Articles: {counts['articles']:,}")
        print(f"  Bucketed: {counts['bucketed']:,}")
        print(f"  Ingestion runs: {counts['runs']}")
        print(f"  Yield curve dates: {counts['yield_dates']}")
        print(f"  Training records: {counts['training']:,}")
        
        conn.close()
        return True, counts
    except Exception as e:
        print(f"  [FAIL] Database error: {e}")
        return False, {}

def check_recent_runs(days=7):
    """Check recent pipeline runs."""
    print(f"\n[DATE] RECENT RUNS (last {days} days)")
    print("-" * 70)
    
    try:
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
        
        if not runs:
            print("  [WARN] No runs found")
            return []
        
        today = dt.date.today()
        for run in runs:
            run_date, started, completed, status, articles, error = run
            status_icon = "[OK]" if status == "completed" else "[FAIL]"
            
            # Check if today
            is_today = run_date == today.isoformat()
            today_marker = " [TODAY]" if is_today else ""
            
            print(f"  {status_icon} {run_date}{today_marker}: {status} ({articles} articles)")
            if error:
                print(f"      Error: {error[:60]}...")
        
        return runs
    except Exception as e:
        print(f"  [FAIL] Error checking runs: {e}")
        return []

def check_recent_data():
    """Check for recent data collection."""
    print("\nRECENT DATA")
    print("-" * 70)
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        today = dt.date.today()
        
        # Articles from today
        today_count = cursor.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(fetched_at) = ?
        """, (today.isoformat(),)).fetchone()[0]
        
        # Articles from last 3 days
        three_days_ago = (today - timedelta(days=3)).isoformat()
        recent_count = cursor.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(fetched_at) >= ?
        """, (three_days_ago,)).fetchone()[0]
        
        # Latest article date
        latest = cursor.execute("""
            SELECT MAX(DATE(fetched_at)) FROM articles
            WHERE fetched_at IS NOT NULL
        """).fetchone()[0]
        
        conn.close()
        
        if today_count > 0:
            print(f"  [OK] Articles today: {today_count}")
        else:
            print(f"  [WARN] Articles today: 0")
        
        print(f"  Articles (last 3 days): {recent_count}")
        
        if latest:
            latest_date = dt.datetime.strptime(latest, "%Y-%m-%d").date()
            days_old = (today - latest_date).days
            if days_old == 0:
                print(f"  [OK] Latest articles: {latest} (today)")
            elif days_old <= 2:
                print(f"  [WARN] Latest articles: {latest} ({days_old} days ago)")
            else:
                print(f"  [FAIL] Latest articles: {latest} ({days_old} days ago)")
        
        return today_count > 0
    except Exception as e:
        print(f"  [FAIL] Error checking data: {e}")
        return False

def check_logs(days=7):
    """Check log files."""
    print("\n[LOG] LOG FILES")
    print("-" * 70)
    
    log_dir = Path(__file__).parent / "logs"
    if not log_dir.exists():
        print("  [WARN] Logs directory doesn't exist")
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
    
    if not logs:
        print("  [WARN] No log files found")
    else:
        today = dt.date.today()
        for log_date, log_file, size in logs[:5]:
            size_kb = size / 1024
            is_today = log_date == today
            marker = " [TODAY]" if is_today else ""
            print(f"  {'[OK]' if is_today else ' '} {log_date}{marker}: {log_file.name} ({size_kb:.1f} KB)")
    
    return logs

def check_models():
    """Check model files."""
    print("\n[ML] MODEL FILES")
    print("-" * 70)
    
    model_dir = Path(__file__).parent / "models"
    if not model_dir.exists():
        print("  [WARN] Models directory doesn't exist")
        return []
    
    pkl_files = list(model_dir.glob("*.pkl"))
    json_files = list(model_dir.glob("*evaluation*.json"))
    
    if not pkl_files:
        print("  [WARN] No model files found")
        return []
    
    # Get latest model
    latest_pkl = max(pkl_files, key=lambda p: p.stat().st_mtime)
    latest_time = dt.datetime.fromtimestamp(latest_pkl.stat().st_mtime)
    days_old = (dt.date.today() - latest_time.date()).days
    
    print(f"  Model files: {len(pkl_files)}")
    print(f"  Evaluation files: {len(json_files)}")
    print(f"  Latest model: {latest_pkl.name}")
    print(f"  Last updated: {latest_time.strftime('%Y-%m-%d %H:%M')} ({days_old} days ago)")
    
    if days_old == 0:
        print("  [OK] Models updated today")
    elif days_old <= 3:
        print(f"  [WARN] Models updated {days_old} days ago")
    else:
        print(f"  [FAIL] Models are {days_old} days old")
    
    return pkl_files

def check_automation():
    """Check automation setup."""
    print("\n[CONFIG] AUTOMATION SETUP")
    print("-" * 70)
    
    # Check LaunchAgent (macOS)
    launchagent_path = Path.home() / "Library/LaunchAgents/com.news.ingestion.plist"
    if launchagent_path.exists():
        print("  [OK] LaunchAgent file exists")
        # Try to check if loaded (requires subprocess)
        import subprocess
        try:
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "com.news.ingestion" in result.stdout:
                print("  [OK] LaunchAgent is loaded")
            else:
                print("  [WARN] LaunchAgent file exists but not loaded")
        except:
            print("  ? Could not check LaunchAgent status")
    else:
        print("  [WARN] No LaunchAgent found")
        print("     See DAILY_AUTOMATION.md for setup instructions")
    
    # Check cron (basic check)
    import subprocess
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "daily_pipeline" in result.stdout or "run_daily" in result.stdout:
            print("  [OK] Cron job found")
        else:
            print("  [WARN] No cron job found")
    except:
        print("  ? Could not check crontab")

def check_dependencies():
    """Check if dependencies are available."""
    print("\n[PACKAGE] DEPENDENCIES")
    print("-" * 70)
    
    deps = {
        "feedparser": False,
        "trafilatura": False,
        "aiolimiter": False,
        "beautifulsoup4": False,
        "openai": False,
        "xgboost": False,
        "numpy": False,
        "sklearn": False,
    }
    
    for dep in deps.keys():
        try:
            if dep == "beautifulsoup4":
                import bs4
                deps[dep] = True
            elif dep == "sklearn":
                import sklearn
                deps[dep] = True
            else:
                __import__(dep)
                deps[dep] = True
        except (ImportError, AttributeError, Exception):
            # Catch all exceptions including NumPy compatibility issues
            # Silently mark as unavailable
            pass
    
    required = ["feedparser", "trafilatura", "aiolimiter", "beautifulsoup4"]
    optional_ml = ["xgboost", "numpy", "sklearn"]
    optional_llm = ["openai"]
    
    print("  Required:")
    for dep in required:
        status = "[OK]" if deps[dep] else "[FAIL]"
        print(f"    {status} {dep}")
    
    print("  Optional (ML):")
    for dep in optional_ml:
        status = "[OK]" if deps[dep] else "[WARN]"
        print(f"    {status} {dep}")
    
    print("  Optional (LLM):")
    for dep in optional_llm:
        status = "[OK]" if deps[dep] else "[WARN]"
        print(f"    {status} {dep}")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Comprehensive health check for daily pipeline")
    ap.add_argument("--days", type=int, default=7, help="Days to look back")
    args = ap.parse_args()
    
    print("\n" + "=" * 70)
    print("DAILY PIPELINE HEALTH CHECK")
    print("=" * 70 + "\n")
    
    # Run all checks
    db_ok, counts = check_database()
    runs = check_recent_runs(args.days)
    data_ok = check_recent_data()
    logs = check_logs(args.days)
    models = check_models()
    check_automation()
    check_dependencies()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    today = dt.date.today()
    today_runs = [r for r in runs if r[0] == today.isoformat()]
    
    issues = []
    if not db_ok:
        issues.append("Database issues")
    if not today_runs:
        issues.append("No run today")
    elif today_runs[0][3] != "completed":
        issues.append(f"Today's run: {today_runs[0][3]}")
    if not data_ok:
        issues.append("No articles today")
    if not logs:
        issues.append("No log files")
    if not models:
        issues.append("No model files")
    
    if not issues:
        print("  [OK] System appears healthy!")
        print("  [OK] Database OK")
        print("  [OK] Recent runs found")
        print("  [OK] Recent data collected")
    else:
        print("  [WARN] Issues detected:")
        for issue in issues:
            print(f"    - {issue}")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

