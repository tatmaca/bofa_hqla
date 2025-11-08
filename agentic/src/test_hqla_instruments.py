import sys

import pandas as pd
import QuantLib as ql

from .hqla_instruments import Fixed, Floating

# Set the static valuation/calculation date: 2025-04-01
calc_date = ql.Date(24, 9, 2028)
ql.Settings.instance().evaluationDate = calc_date

day_count_floater = ql.Actual360()
# using 5% flat interest rate for testing
flat_rate = ql.SimpleQuote(0.05)
rate_handle = ql.QuoteHandle(flat_rate)
day_count = ql.Actual360()
calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
continuous_comp = ql.Continuous  # continously compounded rate of 5%

# Create flat yield curve with continously compounded rate of 5%
flat_yield_curve = ql.FlatForward(calc_date, rate_handle, day_count, continuous_comp)

# Add handle for yield curve
flat_yield_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)
# sofr_term_structure_handle: using 5% flat interest rate for testing
soft_rate = 5 * 1e-2
rate_handle = ql.QuoteHandle(ql.SimpleQuote(soft_rate))
sofr_term_structure = ql.FlatForward(
    calc_date, rate_handle, day_count_floater, ql.Continuous
)
sofr_term_structure_handle = ql.YieldTermStructureHandle(sofr_term_structure)

# Set SOFR index history
im = ql.IndexManager.instance()
sofr_index = ql.Sofr(sofr_term_structure_handle)

# --- Define bond parameters ---
issue_date = ql.Date(1, 4, 2025)
maturity_date = ql.Date(1, 4, 2029)
face_value = 100
coupon_frequency = ql.Period(ql.Quarterly)
spread = [0.0025]  # 25 bps
settlement_days = 1

# --- Build the Floating bond ---
floating_bond = Floating(issue_date, maturity_date, face_value, coupon_frequency)
floating_bond.build_bond(
    index=sofr_index, spread=spread, settlement_days=settlement_days
)
fixed_bond = Fixed(
    issue_date, maturity_date, face_value, coupon_frequency, coupons=[25 * 1e-6]
)
fixed_bond.build_bond(settlement_days=settlement_days)
fixing_dates = list(floating_bond.schedule)

print("========================")

im.clearHistory(sofr_index.name())
calendar = sofr_index.fixingCalendar()
for i, date in enumerate(fixing_dates):
    adjusted_date = calendar.adjust(date, ql.Preceding)
    sofr_index.addFixing(adjusted_date, soft_rate * (1 + i / 10))


print("========================")

# --- Price the bond ---
price = floating_bond.price_from_curve(
    discount_curve=flat_yield_curve_handle, clean=False
)
price2 = fixed_bond.price_from_curve(
    discount_curve=flat_yield_curve_handle, clean=False
)

print(f"Dirty price of the floating rate bond: {price:.4f}")
print(f"Dirty price of the fixed rate bond: {price2:.4f}")
