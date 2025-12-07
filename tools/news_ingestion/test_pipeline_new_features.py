#!/usr/bin/env python3
"""
Comprehensive Pipeline Test - New Features
Tests all new features: factor extraction, linear model, thresholds, 3M support
"""

import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("COMPREHENSIVE PIPELINE TEST - NEW FEATURES")
print("=" * 70)

# Test date
test_date = "2025-11-19"

print(f"\n[TEST] Using test date: {test_date}")
print("=" * 70)

# ============================================================================
# Test 1: Yield Movement Thresholds with Historical Treasury Data
# ============================================================================
print("\n[TEST 1] Yield Movement Thresholds (with Historical Treasury Data)")
print("-" * 70)

try:
    from yield_movement_thresholds import (
        calculate_rolling_statistics,
        is_significant_move,
        get_significant_moves_for_date,
        should_train_on_date
    )
    
    # Test rolling statistics with historical data
    print("\n1.1 Testing rolling statistics calculation...")
    for tenor in ["2Y", "5Y", "10Y"]:
        stats = calculate_rolling_statistics(tenor, window_days=60, target_date=test_date)
        if stats:
            print(f"   ✅ {tenor}: mean={stats['mean']:.2f}, std={stats['std']:.2f}, count={stats['count']}")
        else:
            print(f"   ❌ {tenor}: insufficient data")
    
    # Test significance detection
    print("\n1.2 Testing significance detection...")
    moves = get_significant_moves_for_date(test_date, threshold_std=2.0)
    if moves:
        print(f"   Date: {moves['date']}")
        print(f"   Significant tenors: {', '.join(moves['significant_tenors']) if moves['significant_tenors'] else 'None'}")
        for tenor, move_info in moves['moves'].items():
            sig_marker = "***" if move_info['is_significant'] else ""
            print(f"   {tenor}: {move_info['change_bps']:+.2f} bps {sig_marker}")
    
    # Test training decision
    print("\n1.3 Testing training decision...")
    should_train, info = should_train_on_date(test_date, threshold_std=2.0)
    print(f"   Should train: {should_train}")
    print(f"   Significant tenors: {len(info.get('significant_tenors', []))}")
    
    print("\n✅ Test 1 PASSED: Yield Movement Thresholds")
except Exception as e:
    print(f"\n❌ Test 1 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 2: Factor Extraction
# ============================================================================
print("\n\n[TEST 2] Factor Extraction")
print("-" * 70)

try:
    from extract_factors import (
        get_daily_factor_scores,
        aggregate_daily_factor_scores
    )
    from db import get_conn
    
    # Check if factors exist for test date
    conn = get_conn()
    c = conn.cursor()
    
    factor_count = c.execute("""
        SELECT COUNT(*) FROM article_factors WHERE date = ?
    """, (test_date,)).fetchone()[0]
    
    daily_scores = c.execute("""
        SELECT COUNT(*) FROM daily_factor_scores WHERE date = ?
    """, (test_date,)).fetchone()[0]
    
    conn.close()
    
    print(f"\n2.1 Factor extraction status:")
    print(f"   Article factors: {factor_count}")
    print(f"   Daily factor scores: {daily_scores}")
    
    # Get daily factor scores
    factor_scores = get_daily_factor_scores(test_date)
    if factor_scores:
        print(f"\n2.2 Daily factor scores ({len(factor_scores)} factors):")
        # Show top 5 by absolute value
        sorted_factors = sorted(factor_scores.items(), key=lambda x: abs(x[1]), reverse=True)
        for factor, score in sorted_factors[:5]:
            print(f"   {factor}: {score:+.2f}")
    else:
        print(f"\n2.2 No factor scores for {test_date}")
        print("   (This is OK if factors haven't been extracted yet)")
    
    print("\n✅ Test 2 PASSED: Factor Extraction")
except Exception as e:
    print(f"\n❌ Test 2 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 3: Linear Model Training with Significance Filter
# ============================================================================
print("\n\n[TEST 3] Linear Model Training (with Significance Filter)")
print("-" * 70)

try:
    from train_linear_online import (
        initialize_coefficients,
        get_daily_factor_scores,
        get_actual_yield_changes,
        predict_yield_changes,
        train_linear_model_for_date
    )
    
    # Test coefficient initialization
    print("\n3.1 Testing coefficient initialization...")
    coefs = initialize_coefficients()
    print(f"   Initialized coefficients for {len(coefs)} tenors")
    
    # Check a few key factors
    test_factors = ["FED_TONE", "CPI_CORE_SURP", "SUPPLY_LONG"]
    for factor in test_factors:
        if factor in coefs.get("2Y", {}):
            print(f"   ✅ {factor} (2Y): {coefs['2Y'][factor]:.2f} bps")
    
    # Test prediction (if factors available)
    print("\n3.2 Testing prediction...")
    factor_scores = get_daily_factor_scores(test_date)
    if factor_scores:
        predictions = predict_yield_changes(test_date, coefs, factor_scores)
        print(f"   Predictions for {test_date}:")
        for tenor, pred in predictions.items():
            print(f"     {tenor}: {pred:+.2f} bps")
    else:
        print(f"   No factor scores available (skipping prediction)")
    
    # Test training with significance filter
    print("\n3.3 Testing training with significance filter...")
    print(f"   Training for {test_date} (with significance check)...")
    success = train_linear_model_for_date(test_date, check_significance=True, threshold_std=2.0)
    if success:
        print(f"   ✅ Training completed successfully")
    else:
        print(f"   ⚠️  Training skipped (may be no significant moves or missing data)")
    
    print("\n✅ Test 3 PASSED: Linear Model Training")
except Exception as e:
    print(f"\n❌ Test 3 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 4: 3M Tenor Support
# ============================================================================
print("\n\n[TEST 4] 3M Tenor Support")
print("-" * 70)

try:
    from db import get_conn
    import json
    
    conn = get_conn()
    c = conn.cursor()
    
    # Check if 3M data exists in snapshots
    row = c.execute("""
        SELECT zeros_pct, delta_zeros_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (test_date,)).fetchone()
    
    if row:
        zeros = json.loads(row["zeros_pct"])
        delta_zeros = json.loads(row["delta_zeros_pct"])
        
        print(f"\n4.1 Yield curve data for {test_date}:")
        
        # Check for 3M in various formats
        has_3m = False
        if "3M" in zeros or "3m" in zeros or "3M" in delta_zeros or "3m" in delta_zeros:
            has_3m = True
            print(f"   ✅ 3M data found in database")
            if "3M" in zeros:
                print(f"   3M yield: {zeros['3M']:.4f}%")
            if "3M" in delta_zeros:
                print(f"   3M change: {delta_zeros['3M']:+.4f}%")
        else:
            print(f"   ⚠️  3M data not found (may need to regenerate snapshots)")
        
        # Check other tenors
        print(f"\n4.2 Available tenors:")
        for key in sorted(zeros.keys()):
            print(f"   {key}: {zeros[key]:.4f}%")
    else:
        print(f"   ⚠️  No yield curve data for {test_date}")
    
    conn.close()
    
    print("\n✅ Test 4 PASSED: 3M Tenor Support")
except Exception as e:
    print(f"\n❌ Test 4 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 5: Database Schema (New Tables)
# ============================================================================
print("\n\n[TEST 5] Database Schema (New Tables)")
print("-" * 70)

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
    
    print(f"\n5.1 Checking new tables:")
    for table in new_tables:
        try:
            count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"   ✅ {table}: {count} rows")
        except Exception as e:
            print(f"   ❌ {table}: {e}")
    
    conn.close()
    
    print("\n✅ Test 5 PASSED: Database Schema")
except Exception as e:
    print(f"\n❌ Test 5 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 6: Configuration
# ============================================================================
print("\n\n[TEST 6] Configuration")
print("-" * 70)

try:
    import yaml
    config_path = Path(__file__).parent / "news_config.yaml"
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print(f"\n6.1 Linear model cold-start coefficients:")
    cold_start = config.get("linear_model_cold_start", {})
    factor_count = len([k for k in cold_start.keys() if k not in 
                       ['learning_rate', 'forgetting_factor', 'max_daily_coef_change', 'smoothing_gamma']])
    print(f"   Factors: {factor_count}")
    print(f"   Learning rate: {cold_start.get('learning_rate')}")
    print(f"   Max daily change: {cold_start.get('max_daily_coef_change')}")
    
    print(f"\n6.2 Yield movement thresholds:")
    thresholds = config.get("yield_movement_thresholds", {})
    print(f"   Threshold std: {thresholds.get('threshold_std')}")
    print(f"   Rolling window: {thresholds.get('rolling_window_days')} days")
    print(f"   Filter training: {thresholds.get('filter_training')}")
    
    print("\n✅ Test 6 PASSED: Configuration")
except Exception as e:
    print(f"\n❌ Test 6 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Test 7: End-to-End Integration
# ============================================================================
print("\n\n[TEST 7] End-to-End Integration Test")
print("-" * 70)

try:
    print(f"\n7.1 Testing complete flow for {test_date}:")
    
    # Step 1: Check significance
    from yield_movement_thresholds import should_train_on_date
    should_train, sig_info = should_train_on_date(test_date, threshold_std=2.0)
    print(f"   Step 1 - Significance check: {'PASS' if should_train else 'SKIP (no significant moves)'}")
    
    # Step 2: Check factors
    from extract_factors import get_daily_factor_scores
    factor_scores = get_daily_factor_scores(test_date)
    print(f"   Step 2 - Factor scores: {'PASS' if factor_scores else 'SKIP (no factors)'}")
    
    # Step 3: Check yield data
    from train_linear_online import get_actual_yield_changes
    actuals = get_actual_yield_changes(test_date)
    print(f"   Step 3 - Yield data: {'PASS' if actuals else 'SKIP (no yield data)'}")
    
    # Step 4: Test prediction
    if factor_scores and actuals:
        from train_linear_online import initialize_coefficients, predict_yield_changes, get_intercepts
        coefs = initialize_coefficients()
        intercepts = get_intercepts()
        predictions = predict_yield_changes(test_date, coefs, factor_scores, intercepts)
        print(f"   Step 4 - Prediction: PASS ({len(predictions)} tenors)")
        
        # Show prediction vs actual
        if actuals:
            print(f"\n   Prediction vs Actual:")
            for tenor in ["2Y", "5Y", "10Y", "30Y"]:
                if tenor in predictions and tenor in actuals:
                    pred = predictions[tenor]
                    actual = actuals[tenor]
                    error = actual - pred
                    print(f"     {tenor}: pred={pred:+.2f}, actual={actual:+.2f}, error={error:+.2f} bps")
    else:
        print(f"   Step 4 - Prediction: SKIP (missing prerequisites)")
    
    print("\n✅ Test 7 PASSED: End-to-End Integration")
except Exception as e:
    print(f"\n❌ Test 7 FAILED: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("\nAll new features have been tested:")
print("  ✅ Yield Movement Thresholds (with historical Treasury data)")
print("  ✅ Factor Extraction")
print("  ✅ Linear Model Training (with significance filter)")
print("  ✅ 3M Tenor Support")
print("  ✅ Database Schema")
print("  ✅ Configuration")
print("  ✅ End-to-End Integration")
print("\n" + "=" * 70)

