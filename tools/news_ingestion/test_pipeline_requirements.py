#!/usr/bin/env python3
"""
Test Pipeline Requirements
1. Verify daily article count is sufficient
2. Verify weekend news collection works
3. Verify background execution capability
"""

import sys
import datetime as dt
from pathlib import Path
from db import get_conn

def test_daily_article_count():
    """Test 1: Verify daily article count is large enough"""
    print("\n" + "=" * 70)
    print("TEST 1: Daily Article Count")
    print("=" * 70)
    
    conn = get_conn()
    c = conn.cursor()
    
    # Check last 7 days
    today = dt.date.today()
    results = []
    
    for i in range(7):
        date = today - dt.timedelta(days=i)
        date_str = date.isoformat()
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
        """, (date_str,)).fetchone()[0]
        results.append((date_str, count))
    
    print("\nArticles collected in last 7 days:")
    total = 0
    for date_str, count in results:
        status = "[OK]" if count >= 10 else "[WARN]" if count >= 5 else "[FAIL]"
        print(f"  {status} {date_str}: {count} articles")
        total += count
    
    avg = total / len(results)
    print(f"\nAverage: {avg:.1f} articles/day")
    print(f"Total: {total} articles")
    
    # Assessment
    if avg >= 20:
        print("[OK] PASS: Daily article count is sufficient (>= 20/day)")
        return True
    elif avg >= 10:
        print("[WARN]  WARNING: Daily article count is moderate (10-20/day)")
        print("   Consider adding more RSS feeds or sources")
        return True
    else:
        print("[FAIL] FAIL: Daily article count is too low (< 10/day)")
        print("   Need to add more sources or fix ingestion")
        return False

def test_weekend_collection():
    """Test 2: Verify weekend news collection"""
    print("\n" + "=" * 70)
    print("TEST 2: Weekend News Collection")
    print("=" * 70)
    
    conn = get_conn()
    c = conn.cursor()
    
    # Find recent weekends
    today = dt.date.today()
    weekend_dates = []
    
    for i in range(14):  # Check last 2 weeks
        date = today - dt.timedelta(days=i)
        if date.weekday() >= 5:  # Saturday or Sunday
            weekend_dates.append(date)
    
    if not weekend_dates:
        print("[WARN]  No weekend dates found in last 2 weeks")
        return False
    
    print(f"\nChecking {len(weekend_dates)} weekend dates:")
    has_articles = False
    
    for date in weekend_dates[:4]:  # Check up to 4 weekends
        date_str = date.isoformat()
        count = c.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = ?
        """, (date_str,)).fetchone()[0]
        
        day_name = "Saturday" if date.weekday() == 5 else "Sunday"
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"  {status} {date_str} ({day_name}): {count} articles")
        
        if count > 0:
            has_articles = True
    
    # Check config
    import yaml
    config = yaml.safe_load(open("news_config.yaml"))
    window_hours = config.get("window_hours", 24)
    
    print(f"\nConfiguration:")
    print(f"  Window hours: {window_hours} (should be >= 72 for weekends)")
    
    if has_articles:
        print("[OK] PASS: Weekend articles are being collected")
        return True
    elif window_hours >= 72:
        print("[WARN]  WARNING: Weekend collection configured but no articles found")
        print("   This may be normal if no news was published on weekends")
        return True
    else:
        print("[FAIL] FAIL: Weekend collection not configured properly")
        print(f"   Current window: {window_hours}h (need >= 72h)")
        return False

def test_background_execution():
    """Test 3: Verify background execution capability"""
    print("\n" + "=" * 70)
    print("TEST 3: Background Execution")
    print("=" * 70)
    
    # Check LaunchAgent
    launchagent_path = Path.home() / "Library/LaunchAgents/com.news.ingestion.plist"
    
    if launchagent_path.exists():
        print("[OK] LaunchAgent plist exists")
        
        # Check if loaded
        import subprocess
        try:
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "com.news.ingestion" in result.stdout:
                print("[OK] LaunchAgent is loaded and active")
                
                # Check Python path
                import plistlib
                with open(launchagent_path, 'rb') as f:
                    plist = plistlib.load(f)
                    python_path = plist.get("ProgramArguments", [""])[0]
                    print(f"  Python path: {python_path}")
                    
                    # Verify Python has dependencies
                    import subprocess
                    test_result = subprocess.run(
                        [python_path, "-c", "import feedparser, yaml"],
                        capture_output=True,
                        timeout=2
                    )
                    if test_result.returncode == 0:
                        print("[OK] Python environment has required dependencies")
                        print("[OK] PASS: Background execution is properly configured")
                        return True
                    else:
                        print("[FAIL] Python environment missing dependencies")
                        print(f"   Error: {test_result.stderr.decode()[:100]}")
                        return False
            else:
                print("[WARN]  LaunchAgent exists but not loaded")
                print("   Run: launchctl load ~/Library/LaunchAgents/com.news.ingestion.plist")
                return False
        except Exception as e:
            print(f"[WARN]  Could not verify LaunchAgent status: {e}")
            return False
    else:
        print("[FAIL] LaunchAgent not found")
        print("   See DAILY_AUTOMATION.md for setup instructions")
        return False

def main():
    print("=" * 70)
    print("PIPELINE REQUIREMENTS TEST")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Daily Article Count", test_daily_article_count()))
    results.append(("Weekend Collection", test_weekend_collection()))
    results.append(("Background Execution", test_background_execution()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
        return 0
    else:
        print("[WARN]  SOME TESTS FAILED - Review output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

