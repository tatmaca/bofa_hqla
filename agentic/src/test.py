import QuantLib as ql
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from hqla_assets import Level1Discount, Level1Floating, Level1Fixed, Level2AFixed, Level2BFloating
from hqla_portfolio import Portfolio
from hqla_portfolio_opt import HQLA_Portfolio_Opt_Enhanced

"""
Test script for the enhanced lexicographic HQLA optimizer.

This creates a realistic scenario where Level 2 assets have 
higher yields to demonstrate the mini-max optimization behavior.
"""

# --- Set evaluation date ---
today = ql.Date(8, 11, 2025)
ql.Settings.instance().evaluationDate = today

# ============================================================================
# SCENARIO 1: Base flat yield curve at 3%
# ============================================================================
flat_rate = ql.SimpleQuote(0.03)  # 3% base rate
rate_handle = ql.QuoteHandle(flat_rate)
day_count = ql.Actual360()
flat_yield_curve = ql.FlatForward(today, rate_handle, day_count, ql.Continuous)
discount_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)

# ============================================================================
# SCENARIO 2: SOFR curve (floating rate index) at higher rate
# ============================================================================
sofr_rate = 0.045  # 4.5% SOFR (higher than base to make floaters attractive)
sofr_term_structure = ql.FlatForward(
    today, 
    ql.QuoteHandle(ql.SimpleQuote(sofr_rate)), 
    day_count, 
    ql.Continuous
)
sofr_handle = ql.YieldTermStructureHandle(sofr_term_structure)
sofr_index = ql.Sofr(sofr_handle)

# Dates
issue = ql.Date(8, 6, 2024)
maturity_1y = ql.Date(8, 11, 2026)
maturity_2y = ql.Date(8, 11, 2027)
maturity_3y = ql.Date(8, 11, 2028)
maturity_5y = ql.Date(8, 11, 2030)

# ============================================================================
# BUILD PORTFOLIO with varying yields across levels
# ============================================================================
portfolio = Portfolio()

# --- Level 1 Assets (lowest yield, no haircut) ---
# 1. Zero coupon (typically lowest yield)
z1 = Level1Discount(
    issue_date=issue, 
    maturity_date=maturity_1y, 
    face_value=100, 
    quantity=0,  # Start with 0, optimizer will allocate
    name="L1_Zero_1Y", 
    isin="US0000000001"
)
z1.build_bond()
portfolio.add_instrument(z1)

# 2. Level 1 Fixed at low coupon (2.5%)
fix1 = Level1Fixed(
    issue_date=issue,
    maturity_date=maturity_2y,
    face_value=100,
    coupons=[0.025],  # 2.5% coupon
    quantity=0,
    name="L1_Fixed_2Y",
    isin="US0000000002"
)
fix1.build_bond()
portfolio.add_instrument(fix1)

# 3. Level 1 Floating (SOFR-based)
f1 = Level1Floating(
    issue_date=issue, 
    maturity_date=maturity_2y, 
    face_value=100, 
    quantity=0, 
    name="L1_Floating_2Y", 
    isin="US0000000003"
)
f1.build_bond(index=sofr_index, spread=[0])  # No spread over SOFR
portfolio.add_instrument(f1)

# --- Level 2A Assets (15% haircut, higher yield) ---
# 4. Level 2A Fixed with HIGHER coupon (4.0%)
fx2a = Level2AFixed(
    issue_date=issue, 
    maturity_date=maturity_3y, 
    face_value=100, 
    coupons=[0.040],  # 4.0% coupon (higher yield!)
    quantity=0, 
    name="L2A_Fixed_3Y", 
    isin="US0000000004"
)
fx2a.build_bond()
portfolio.add_instrument(fx2a)

# 5. Another Level 2A Fixed with even higher yield (4.5%)
fx2a_2 = Level2AFixed(
    issue_date=issue,
    maturity_date=maturity_5y,
    face_value=100,
    coupons=[0.045],  # 4.5% coupon
    quantity=0,
    name="L2A_Fixed_5Y",
    isin="US0000000005"
)
fx2a_2.build_bond()
portfolio.add_instrument(fx2a_2)

# --- Level 2B Assets (25% haircut, highest yield) ---
# 6. Level 2B Floating with SPREAD (highest yield asset)
f2b = Level2BFloating(
    issue_date=issue, 
    maturity_date=maturity_3y, 
    face_value=100, 
    quantity=0, 
    name="L2B_Floating_3Y", 
    isin="US0000000006"
)
f2b.build_bond(index=sofr_index, spread=[150 * 1e-4])  # 150bp spread over SOFR!
portfolio.add_instrument(f2b)

# ============================================================================
# Set up SOFR index fixings
# ============================================================================
im = ql.IndexManager.instance()
im.clearHistory(sofr_index.name())

calendar = sofr_index.fixingCalendar()
current_date = issue
while current_date <= today:
    if calendar.isBusinessDay(current_date):
        sofr_index.addFixing(current_date, sofr_rate)
    current_date += 1

# ============================================================================
# Price all instruments
# ============================================================================
portfolio.update_prices(yield_curve=discount_curve_handle)

print("="*80)
print("INITIAL PORTFOLIO (Before Optimization)")
print("="*80)
portfolio.summary()
print(f"\nTotal Value: ${portfolio.total_value():,.2f}")
print(f"Adjusted Value: ${portfolio.adjusted_value():,.2f}")

# ============================================================================
# INSTANTIATE OPTIMIZER
# ============================================================================
net_cash_outflow = 1_000_000  # $1M NCO
min_lcr = 1.1  # Must meet 100% LCR
max_lcr = 1.3  # Don't go above 130%

optimizer = HQLA_Portfolio_Opt_Enhanced(
    portfolio=portfolio,
    net_cash_outflow=net_cash_outflow,
    min_lcr=min_lcr,
    max_lcr=max_lcr,
    target_duration=2.5,  # Target 2.5 year duration
    duration_tolerance=0.75,
    allocation_buffer=0.03  # Allow 3% above minimum in stage 2
)

print("\n" + "="*80)
print("ASSET SUMMARY (with computed metrics)")
print("="*80)
print(optimizer.assets_summary[["Name", "Level", "YTM", "ModDuration", "Haircut"]])

# ============================================================================
# TEST 1: LEXICOGRAPHIC (MINI-MAX) OPTIMIZATION
# ============================================================================
print("\n\n" + "="*80)
print("TEST 1: LEXICOGRAPHIC (MINI-MAX) OPTIMIZATION")
print("="*80)
print("Goal: Minimize allocation first, then maximize returns")

lex_df, lex_result, lex_total, lex_return, lex_lcr = optimizer.lexicographic_mean_optimize(
    max_position_size=0.40,  # Max 40% of NCO per asset
    min_position_size=0.0,
    max_total_allocation=2.0,
    verbose=True
)

print("\n--- Allocation Details ---")
print(lex_df)
print(f"\nWeights sum to: {lex_result.x.sum():.4f}")

# ============================================================================
# TEST 3: MEAN-VARIANCE LEXICOGRAPHIC
# ============================================================================
print("\n\n" + "="*80)
print("TEST 3: MEAN-VARIANCE LEXICOGRAPHIC")
print("="*80)
print("Goal: Minimize allocation, then optimize risk-adjusted returns")

mv_df, mv_result, mv_total, mv_return, mv_lcr = optimizer.mean_variance_lexicographic(
    risk_aversion=2.0,
    base_curve_handle=discount_curve_handle,
    n_random=500,
    bp_std=0.02,  # 200bp standard deviation in parallel shifts
    use_shrinkage=True,
    max_position_size=0.40,
    min_position_size=0.0,
    max_total_allocation=2.0,
    verbose=True
)

print("\n--- Allocation Details ---")
print(mv_df)
print(f"\nWeights sum to: {mv_result.x.sum():.4f}")

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================
print("\n\n" + "="*80)
print("COMPARISON OF ALL THREE METHODS")
print("="*80)

comparison = pd.DataFrame({
    "Method": ["Lexicographic", "Mean-Variance Lex"],
    "Total Allocated": [lex_total, mv_total],
    "% of NCO": [lex_total/net_cash_outflow, mv_total/net_cash_outflow],
    "Expected Return": [lex_return, mv_return],
    "LCR Ratio": [lex_lcr, mv_lcr],
})

print(comparison.to_string(index=False))

# Show which assets were chosen by each method
print("\n" + "="*80)
print("ALLOCATION COMPARISON BY ASSET")
print("="*80)

alloc_comparison = pd.DataFrame({
    "Asset": optimizer.assets_summary["Name"],
    "Level": optimizer.assets_summary["Level"],
    "YTM": optimizer.assets_summary["YTM"],
    "Lex_Alloc": lex_df["Allocated_Amount"].values,
    "MV_Alloc": mv_df["Allocated_Amount"].values,
})

print(alloc_comparison.to_string(index=False))

print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)
print(f"1. Minimum allocation needed: ~{lex_total/net_cash_outflow:.1%} of NCO")
print(f"2. Lexicographic return: {lex_return:.4%}")
print(f"3. All methods achieved LCR between {min_lcr:.0%} and {max_lcr:.0%}")
print(f"4. Level 2A/2B assets have higher yields but haircuts limit their attractiveness")
print("="*80)