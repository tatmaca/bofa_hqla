#!/usr/bin/env python3
"""
Incremental Pipeline Test - New Features
Test each component separately for faster feedback
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_thresholds(test_date: str):
    """Test 1: Yield Movement Thresholds"""
    print("\n" + "=" * 70)
    print("TEST 1: Yield Movement Thresholds (with Historical Treasury Data)")
    print("=" * 70)
    
    try:
        from yield_movement_thresholds import (
            calculate_rolling_statistics,
            get_significant_moves_for_date,
            should_train_on_date
        )
        
        # Test rolling statistics
        print(f"\n[1.1] Calculating rolling statistics for 2Y (target: {test_date})...")
        stats = calculate_rolling_statistics("2Y", window_days=60, target_date=test_date)
        if stats:
            print(f"   ✅ Mean: {stats['mean']:.2f} bps")
            print(f"   ✅ Std: {stats['std']:.2f} bps")
            print(f"   ✅ Count: {stats['count']} days")
            print(f"   ✅ Threshold (±2σ): ±{2.0 * stats['std']:.2f} bps")
        else:
            print(f"   ⚠️  Insufficient data")
        
        # Test significance detection
        print(f"\n[1.2] Checking significant moves for {test_date}...")
        moves = get_significant_moves_for_date(test_date, threshold_std=2.0)
        if moves:
            sig_count = len(moves['significant_tenors'])
            print(f"   ✅ Significant tenors: {sig_count}")
            for tenor, move_info in moves['moves'].items():
                sig_marker = "***" if move_info['is_significant'] else ""
                print(f"      {tenor}: {move_info['change_bps']:+.2f} bps {sig_marker}")
        
        # Test training decision
        print(f"\n[1.3] Training decision for {test_date}...")
        should_train, info = should_train_on_date(test_date, threshold_std=2.0)
        print(f"   ✅ Should train: {should_train}")
        print(f"   ✅ Significant tenors: {len(info.get('significant_tenors', []))}")
        
        print("\n✅ TEST 1 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factor_extraction(test_date: str):
    """Test 2: Factor Extraction"""
    print("\n" + "=" * 70)
    print("TEST 2: Factor Extraction")
    print("=" * 70)
    
    try:
        from extract_factors import get_daily_factor_scores
        from db import get_conn
        
        conn = get_conn()
        c = conn.cursor()
        
        # Check article factors
        factor_count = c.execute("""
            SELECT COUNT(*) FROM article_factors WHERE date = ?
        """, (test_date,)).fetchone()[0]
        
        # Check daily scores
        score_count = c.execute("""
            SELECT COUNT(*) FROM daily_factor_scores WHERE date = ?
        """, (test_date,)).fetchone()[0]
        
        conn.close()
        
        print(f"\n[2.1] Factor extraction status for {test_date}:")
        print(f"   ✅ Article factors: {factor_count}")
        print(f"   ✅ Daily factor scores: {score_count}")
        
        # Get daily factor scores
        factor_scores = get_daily_factor_scores(test_date)
        if factor_scores:
            print(f"\n[2.2] Daily factor scores ({len(factor_scores)} factors):")
            sorted_factors = sorted(factor_scores.items(), key=lambda x: abs(x[1]), reverse=True)
            for factor, score in sorted_factors[:5]:
                print(f"      {factor}: {score:+.2f}")
        else:
            print(f"\n[2.2] ⚠️  No factor scores (may need to extract factors)")
        
        print("\n✅ TEST 2 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_linear_model(test_date: str):
    """Test 3: Linear Model"""
    print("\n" + "=" * 70)
    print("TEST 3: Linear Online Learning Model")
    print("=" * 70)
    
    try:
        from train_linear_online import (
            initialize_coefficients,
            get_daily_factor_scores,
            get_actual_yield_changes,
            predict_yield_changes,
            get_intercepts
        )
        
        # Test initialization
        print(f"\n[3.1] Coefficient initialization...")
        coefs = initialize_coefficients()
        print(f"   ✅ Initialized for {len(coefs)} tenors")
        
        # Check key factors
        test_factors = ["FED_TONE", "CPI_CORE_SURP", "SUPPLY_LONG", "RISK_OFF"]
        for factor in test_factors:
            if factor in coefs.get("2Y", {}):
                print(f"      {factor} (2Y): {coefs['2Y'][factor]:+.2f} bps")
        
        # Test prediction
        print(f"\n[3.2] Prediction for {test_date}...")
        factor_scores = get_daily_factor_scores(test_date)
        if factor_scores:
            intercepts = get_intercepts()
            predictions = predict_yield_changes(test_date, coefs, factor_scores, intercepts)
            print(f"   ✅ Predictions generated:")
            for tenor in ["3M", "2Y", "5Y", "10Y", "30Y"]:
                if tenor in predictions:
                    print(f"      {tenor}: {predictions[tenor]:+.2f} bps")
        else:
            print(f"   ⚠️  No factor scores (skipping prediction)")
        
        # Test actuals
        print(f"\n[3.3] Actual yield changes for {test_date}...")
        actuals = get_actual_yield_changes(test_date)
        if actuals:
            print(f"   ✅ Actuals available:")
            for tenor in ["3M", "2Y", "5Y", "10Y", "30Y"]:
                if tenor in actuals:
                    print(f"      {tenor}: {actuals[tenor]:+.2f} bps")
        else:
            print(f"   ⚠️  No actuals (may need yield curve data)")
        
        print("\n✅ TEST 3 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3m_support(test_date: str):
    """Test 4: 3M Tenor Support"""
    print("\n" + "=" * 70)
    print("TEST 4: 3M Tenor Support")
    print("=" * 70)
    
    try:
        from db import get_conn
        import json
        
        conn = get_conn()
        c = conn.cursor()
        
        row = c.execute("""
            SELECT zeros_pct, delta_zeros_pct
            FROM yield_curve_daily
            WHERE date = ?
        """, (test_date,)).fetchone()
        
        if row:
            zeros = json.loads(row["zeros_pct"])
            delta_zeros = json.loads(row["delta_zeros_pct"])
            
            print(f"\n[4.1] Yield curve data for {test_date}:")
            
            # Check for 3M
            has_3m = "3M" in zeros or "3m" in zeros
            has_3m_delta = "3M" in delta_zeros or "3m" in delta_zeros
            
            print(f"   ✅ 3M in zeros: {has_3m}")
            print(f"   ✅ 3M in deltas: {has_3m_delta}")
            
            if has_3m:
                val = zeros.get("3M") or zeros.get("3m")
                print(f"   ✅ 3M yield: {val:.4f}%")
            if has_3m_delta:
                val = delta_zeros.get("3M") or delta_zeros.get("3m")
                print(f"   ✅ 3M change: {val:+.4f}%")
            
            # List all tenors
            print(f"\n[4.2] All available tenors:")
            for key in sorted(zeros.keys()):
                print(f"      {key}: {zeros[key]:.4f}%")
        else:
            print(f"   ⚠️  No yield curve data for {test_date}")
        
        conn.close()
        
        print("\n✅ TEST 4 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test 5: Database Schema"""
    print("\n" + "=" * 70)
    print("TEST 5: Database Schema (New Tables)")
    print("=" * 70)
    
    try:
        from db import get_conn
        
        conn = get_conn()
        c = conn.cursor()
        
        new_tables = [
            "article_factors",
            "daily_factor_scores",
            "linear_model_coefficients",
            "linear_model_intercepts",
            "linear_model_predictions"
        ]
        
        print(f"\n[5.1] Checking new tables:")
        all_exist = True
        for table in new_tables:
            try:
                count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"   ✅ {table}: {count} rows")
            except Exception as e:
                print(f"   ❌ {table}: {e}")
                all_exist = False
        
        conn.close()
        
        if all_exist:
            print("\n✅ TEST 5 PASSED")
            return True
        else:
            print("\n⚠️  TEST 5 PARTIAL: Some tables missing")
            return False
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test 6: Configuration"""
    print("\n" + "=" * 70)
    print("TEST 6: Configuration")
    print("=" * 70)
    
    try:
        import yaml
        config_path = Path(__file__).parent / "news_config.yaml"
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        print(f"\n[6.1] Linear model configuration:")
        cold_start = config.get("linear_model_cold_start", {})
        factor_count = len([k for k in cold_start.keys() if k not in 
                           ['learning_rate', 'forgetting_factor', 'max_daily_coef_change', 'smoothing_gamma']])
        print(f"   ✅ Factors: {factor_count}")
        print(f"   ✅ Learning rate: {cold_start.get('learning_rate')}")
        print(f"   ✅ Max daily change: {cold_start.get('max_daily_coef_change')} bps")
        
        print(f"\n[6.2] Yield movement thresholds:")
        thresholds = config.get("yield_movement_thresholds", {})
        print(f"   ✅ Threshold std: {thresholds.get('threshold_std')}")
        print(f"   ✅ Rolling window: {thresholds.get('rolling_window_days')} days")
        print(f"   ✅ Filter training: {thresholds.get('filter_training')}")
        
        print("\n✅ TEST 6 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration(test_date: str):
    """Test 7: Integration Test"""
    print("\n" + "=" * 70)
    print("TEST 7: Integration Test (Complete Flow)")
    print("=" * 70)
    
    try:
        print(f"\n[7.1] Testing complete flow for {test_date}:")
        
        # Step 1: Significance check
        from yield_movement_thresholds import should_train_on_date
        should_train, sig_info = should_train_on_date(test_date, threshold_std=2.0)
        print(f"   Step 1 - Significance: {'✅ PASS' if should_train else '⚠️  SKIP (no significant moves)'}")
        
        # Step 2: Factor scores
        from extract_factors import get_daily_factor_scores
        factor_scores = get_daily_factor_scores(test_date)
        print(f"   Step 2 - Factor scores: {'✅ PASS' if factor_scores else '⚠️  SKIP (no factors)'}")
        
        # Step 3: Yield data
        from train_linear_online import get_actual_yield_changes
        actuals = get_actual_yield_changes(test_date)
        print(f"   Step 3 - Yield data: {'✅ PASS' if actuals else '⚠️  SKIP (no yield data)'}")
        
        # Step 4: Prediction
        if factor_scores and actuals:
            from train_linear_online import initialize_coefficients, predict_yield_changes, get_intercepts
            coefs = initialize_coefficients()
            intercepts = get_intercepts()
            predictions = predict_yield_changes(test_date, coefs, factor_scores, intercepts)
            print(f"   Step 4 - Prediction: ✅ PASS ({len(predictions)} tenors)")
            
            # Show comparison
            print(f"\n[7.2] Prediction vs Actual:")
            for tenor in ["2Y", "5Y", "10Y", "30Y"]:
                if tenor in predictions and tenor in actuals:
                    pred = predictions[tenor]
                    actual = actuals[tenor]
                    error = actual - pred
                    print(f"      {tenor}: pred={pred:+.2f}, actual={actual:+.2f}, error={error:+.2f} bps")
        else:
            print(f"   Step 4 - Prediction: ⚠️  SKIP (missing prerequisites)")
        
        print("\n✅ TEST 7 PASSED")
        return True
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    ap = argparse.ArgumentParser(description="Incremental pipeline test")
    ap.add_argument("--test", type=str, choices=["1", "2", "3", "4", "5", "6", "7", "all"],
                   default="all", help="Which test to run (1=thresholds, 2=factors, 3=linear, 4=3m, 5=schema, 6=config, 7=integration, all=all)")
    ap.add_argument("--date", type=str, default="2025-11-19", help="Test date (YYYY-MM-DD)")
    args = ap.parse_args()
    
    test_date = args.date
    
    print("=" * 70)
    print("INCREMENTAL PIPELINE TEST - NEW FEATURES")
    print("=" * 70)
    print(f"Test date: {test_date}")
    print(f"Running test: {args.test}")
    
    results = {}
    
    if args.test in ["1", "all"]:
        results["1"] = test_thresholds(test_date)
    if args.test in ["2", "all"]:
        results["2"] = test_factor_extraction(test_date)
    if args.test in ["3", "all"]:
        results["3"] = test_linear_model(test_date)
    if args.test in ["4", "all"]:
        results["4"] = test_3m_support(test_date)
    if args.test in ["5", "all"]:
        results["5"] = test_database_schema()
    if args.test in ["6", "all"]:
        results["6"] = test_configuration()
    if args.test in ["7", "all"]:
        results["7"] = test_integration(test_date)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_num, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  Test {test_num}: {status}")
    
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

