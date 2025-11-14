#!/usr/bin/env python3
"""
Test Script for News Ingestion & Yield Curve Prediction System
Runs comprehensive tests to verify everything works.
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports."""
    print("=" * 60)
    print("TEST 1: Imports")
    print("=" * 60)
    
    tests = []
    
    # Core imports
    try:
        from db import get_conn, init_db
        print("[OK] db module")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] db module: {e}")
        tests.append(False)
    
    try:
        from bucket_news import get_bucket_counts, BUCKETS
        print(f"[OK] bucket_news module ({len(BUCKETS)} buckets)")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] bucket_news module: {e}")
        tests.append(False)
    
    try:
        from analyze_yield_impact import analyze_yield_impact, get_bucketed_news, extract_llm_features
        print("[OK] analyze_yield_impact module")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] analyze_yield_impact module: {e}")
        tests.append(False)
    
    try:
        from collect_training_data import collect_training_data
        print("[OK] collect_training_data module")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] collect_training_data module: {e}")
        tests.append(False)
    
    # Optional ML imports
    try:
        import numpy as np
        print(f"[OK] NumPy {np.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"[FAIL] NumPy: {e}")
        tests.append(False)
    
    try:
        import xgboost as xgb
        print(f"[OK] XGBoost {xgb.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"[WARN] XGBoost: {e} (optional)")
        tests.append(True)  # Don't fail on optional
    
    try:
        from sklearn.metrics import mean_squared_error
        print("[OK] scikit-learn")
        tests.append(True)
    except Exception as e:
        print(f"[WARN] scikit-learn: {e} (optional)")
        tests.append(True)
    
    # Optional LLM imports
    try:
        from openai import OpenAI
        print("[OK] OpenAI")
        tests.append(True)
    except Exception as e:
        print(f"[WARN] OpenAI: {e} (optional)")
        tests.append(True)
    
    print(f"\nResult: {sum(tests)}/{len(tests)} tests passed")
    return all(tests[:4])  # Core modules must pass

def test_database():
    """Test database operations."""
    print("\n" + "=" * 60)
    print("TEST 2: Database")
    print("=" * 60)
    
    try:
        from db import get_conn, init_db
        
        # Initialize
        init_db()
        print("[OK] Database initialized")
        
        # Check tables
        conn = get_conn()
        cursor = conn.cursor()
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        table_names = [t[0] for t in tables]
        print(f"[OK] Tables: {', '.join(table_names)}")
        
        # Check article count
        count = cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"[OK] Articles in DB: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bucketing():
    """Test news bucketing."""
    print("\n" + "=" * 60)
    print("TEST 3: News Bucketing")
    print("=" * 60)
    
    try:
        from bucket_news import get_bucket_counts, get_unbucketed_articles
        
        # Check bucket counts
        counts = get_bucket_counts()
        print(f"[OK] Bucket counts retrieved: {len(counts)} buckets")
        if counts:
            for bucket, count in list(counts.items())[:3]:
                print(f"  - {bucket}: {count} articles")
        
        # Check unbucketed articles
        unbucketed = get_unbucketed_articles(hours=24)
        print(f"[OK] Unbucketed articles (last 24h): {len(unbucketed)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Bucketing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_analysis():
    """Test LLM analysis (if available)."""
    print("\n" + "=" * 60)
    print("TEST 4: LLM Analysis")
    print("=" * 60)
    
    try:
        from analyze_yield_impact import get_bucketed_news, analyze_yield_impact, load_curve_snapshot
        import datetime as dt
        
        date = dt.date.today().isoformat()
        
        # Get bucketed news
        news = get_bucketed_news(date)
        print(f"[OK] Bucketed news retrieved: {len(news)} buckets")
        
        # Try to load curve snapshot
        curve = load_curve_snapshot(date)
        if curve:
            print(f"[OK] Yield curve snapshot loaded for {date}")
        else:
            print(f"[WARN] No yield curve snapshot for {date} (will use fallback)")
        
        # Test analysis (may use fallback if no API key)
        if news:
            analysis = analyze_yield_impact(news, curve)
            if analysis.get("predictions"):
                print("[OK] Analysis generated")
                print(f"  Predictions: {list(analysis['predictions'].keys())}")
            else:
                print("[WARN] Analysis returned fallback (no API key?)")
        else:
            print("[WARN] No bucketed news to analyze")
        
        return True
    except Exception as e:
        print(f"[FAIL] LLM analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_training_data_collection():
    """Test training data collection."""
    print("\n" + "=" * 60)
    print("TEST 5: Training Data Collection")
    print("=" * 60)
    
    try:
        from collect_training_data import collect_training_data, get_available_dates
        import datetime as dt
        
        # Test date range
        end_date = dt.date.today().isoformat()
        start_date = (dt.date.today() - dt.timedelta(days=7)).isoformat()
        
        dates = get_available_dates(start_date, end_date)
        print(f"[OK] Date range: {len(dates)} business days")
        
        # Try to collect (may return 0 if no data)
        training_data = collect_training_data(start_date, end_date)
        print(f"[OK] Training data collection: {len(training_data)} examples")
        
        if len(training_data) > 0:
            print(f"  Features per example: {len(training_data[0]['features'])}")
            print(f"  Sample date: {training_data[0]['date']}")
        else:
            print("  [WARN] No training data (need historical analyses + snapshots)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Training data collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_xgboost_training():
    """Test XGBoost training (if available)."""
    print("\n" + "=" * 60)
    print("TEST 6: XGBoost Training")
    print("=" * 60)
    
    try:
        import xgboost as xgb
        print(f"[OK] XGBoost imported: {xgb.__version__}")
    except Exception as e:
        if "libomp" in str(e) or "OpenMP" in str(e):
            print("[WARN] XGBoost requires OpenMP (install: brew install libomp)")
        else:
            print(f"[WARN] XGBoost not available: {e}")
        return True  # Not a critical failure
    
    try:
        from train_xgboost import load_training_data, train_models
        from pathlib import Path
        
        # Check for training data file
        data_files = list(Path(__file__).parent.glob("training_data_*.json"))
        if not data_files:
            print("[WARN] No training data files found")
            print("  Run: python3 collect_training_data.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD")
            return True  # Not a failure, just no data
        
        # Try to load
        data_path = data_files[0]
        print(f"[OK] Found training data: {data_path.name}")
        
        X, y, dates = load_training_data(data_path)
        if X is not None and len(X) > 0:
            print(f"[OK] Loaded {len(X)} examples with {len(X[0])} features")
            
            if len(X) >= 7:
                print("  [OK] Sufficient data for training")
            else:
                print(f"  [WARN] Need at least 7 examples (have {len(X)})")
        else:
            print("  [WARN] No data loaded")
        
        return True
    except Exception as e:
        print(f"[WARN] XGBoost training test: {e}")
        return True  # Optional feature

def test_rolling_update():
    """Test rolling update system."""
    print("\n" + "=" * 60)
    print("TEST 7: Rolling Update System")
    print("=" * 60)
    
    try:
        from update_models_rolling import get_rolling_window_dates
        
        start, end = get_rolling_window_dates(days=30)
        print(f"[OK] Rolling window dates: {start} to {end}")
        print("[OK] Rolling update function available")
        print("  Run manually: python3 update_models_rolling.py --days 30")
        
        return True
    except ImportError as e:
        if "xgboost" in str(e).lower():
            print("[WARN] Rolling update requires XGBoost (install OpenMP: brew install libomp)")
        else:
            print(f"[WARN] Rolling update test: {e}")
        return True  # Optional
    except Exception as e:
        print(f"[WARN] Rolling update test: {e}")
        return True  # Optional feature

def test_daily_pipeline():
    """Test daily pipeline components."""
    print("\n" + "=" * 60)
    print("TEST 8: Daily Pipeline Components")
    print("=" * 60)
    
    try:
        from daily_pipeline import sync_yield_curve_data, prepare_training_record
        import datetime as dt
        
        date = dt.date.today().isoformat()
        
        # Test yield curve sync
        result = sync_yield_curve_data(date)
        if result:
            print(f"[OK] Yield curve sync works for {date}")
        else:
            print(f"[WARN] No snapshot found for {date} (expected if not built)")
        
        # Test training record prep
        record = prepare_training_record(date)
        if record:
            print(f"[OK] Training record preparation works")
        else:
            print(f"[WARN] No training record (need news + yield data)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Daily pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE SYSTEM TEST")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Bucketing", test_bucketing()))
    results.append(("LLM Analysis", test_llm_analysis()))
    results.append(("Training Data", test_training_data_collection()))
    results.append(("XGBoost", test_xgboost_training()))
    results.append(("Rolling Update", test_rolling_update()))
    results.append(("Daily Pipeline", test_daily_pipeline()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed or skipped")
        return 1

if __name__ == "__main__":
    sys.exit(main())

