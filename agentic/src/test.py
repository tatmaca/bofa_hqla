import QuantLib as ql
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from hqla_assets import Level1Discount, Level1Floating, Level2AFixed, Level2BFloating
from hqla_portfolio import Portfolio
from hqla_portfolio_opt import HQLA_Portfolio_Opt, ScenarioGenerator  # your optimizer classes

# --- Set evaluation date ---
today = ql.Date(8, 11, 2025)
ql.Settings.instance().evaluationDate = today

# base flat yield curve
flat_rate = ql.SimpleQuote(0.05)  # 5% flat
rate_handle = ql.QuoteHandle(flat_rate)
day_count = ql.Actual360()
flat_yield_curve = ql.FlatForward(today, rate_handle, day_count, ql.Continuous)
discount_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)

# SOFR curve
sofr_rate = 0.005  # 50 bp
sofr_term_structure = ql.FlatForward(today, ql.QuoteHandle(ql.SimpleQuote(sofr_rate)), day_count, ql.Continuous)
sofr_handle = ql.YieldTermStructureHandle(sofr_term_structure)
sofr_index = ql.Sofr(sofr_handle)

# dates
issue = ql.Date(8, 6, 2024)
maturity_1y = ql.Date(8, 11, 2026)
maturity_2y = ql.Date(8, 11, 2027)
maturity_3y = ql.Date(8, 11, 2028)

# test portfolio
portfolio = Portfolio()

# Level 1 Discount
z1 = Level1Discount(issue_date=issue, maturity_date=maturity_1y, face_value=100, quantity=10, name="L1_Zero_1Y", isin="US0000000001")
z1.build_bond()
portfolio.add_instrument(z1)

# Level 1 Floating
f1 = Level1Floating(issue_date=issue, maturity_date=maturity_2y, face_value=100, quantity=5, name="L1_Floating_2Y", isin="US0000000002")
f1.build_bond(index=sofr_index)
portfolio.add_instrument(f1)

# Level 2A Fixed
fx1 = Level2AFixed(issue_date=issue, maturity_date=maturity_2y, face_value=100, coupons=[0.03], quantity=8, name="L2A_Fixed_2Y", isin="US0000000003")
fx1.build_bond()
portfolio.add_instrument(fx1)

# Level 2B Floating
f2 = Level2BFloating(issue_date=issue, maturity_date=maturity_3y, face_value=100, quantity=12, name="L2B_Floating_3Y", isin="US0000000004")
f2.build_bond(index=sofr_index)
portfolio.add_instrument(f2)

# update SOFR fixings
im = ql.IndexManager.instance()
im.clearHistory(sofr_index.name())

calendar = sofr_index.fixingCalendar()
current_date = issue
while current_date <= today:
    if calendar.isBusinessDay(current_date):
        sofr_index.addFixing(current_date, sofr_rate)
    current_date += 1  # step 1 day

# --- Update bond prices using base curve ---
portfolio.update_prices(yield_curve=discount_curve_handle)

print("=== Portfolio Summary ===")
portfolio.summary()
print(f"Total Value: {portfolio.total_value():.2f}")
print(f"Adjusted Value: {portfolio.adjusted_value():.2f}")

# --- Instantiate optimizer ---
optimizer = HQLA_Portfolio_Opt(portfolio, 100_000, 1.3)

# manually overriding to see if there are differences
optimizer.assets_summary.loc[optimizer.assets_summary["Name"] == "L2A_Fixed_2Y", "YTM"] = 0.10

# --- Mean-only optimization ---
print("\n=== Running Mean-Only Optimization ===")
mean_df, mean_result, mean_total_value, mean_expected_return = optimizer.mean_optimize()
print(mean_df)  # already contains Name, Level, Price, YTM, Allocated_Amount
print(f"Total Portfolio Value: {mean_total_value:.2f}")
print(f"Portfolio Expected Return: {mean_expected_return:.6f}")

# --- Mean-Variance optimization ---
print("\n=== Running Mean-Variance Optimization ===")
mv_df, mv_res, mv_total_value, mv_expected_return = optimizer.mean_variance_optimize(
    lam=0.5,
    base_curve_handle=discount_curve_handle,
    n_random=1000,  
    bp_std=0.05,
    use_mu="ytm"
)
print(mv_df)  # already contains Name, Level, Price, YTM, Allocated_Amount
print(f"Total Portfolio Value: {mv_total_value:.2f}")
print(f"Portfolio Expected Return: {mv_expected_return:.6f}")
