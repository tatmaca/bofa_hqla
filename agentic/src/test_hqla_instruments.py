import sys

import pandas as pd
import QuantLib as ql

from .hqla_instruments import Floating

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
bond_engine = ql.DiscountingBondEngine(flat_yield_curve_handle)
floating_bond.bond.setPricingEngine(bond_engine)

fixing_dates = list(floating_bond.schedule)
print("========================")

im.clearHistory(sofr_index.name())
calendar = sofr_index.fixingCalendar()
for date in fixing_dates:
    adjusted_date = calendar.adjust(date, ql.Preceding)
    sofr_index.addFixing(adjusted_date, soft_rate)


print(floating_bond.bond.dirtyPrice())
print("========================")

# --- Price the bond ---
price = floating_bond.price_from_curve(
    discount_curve=sofr_term_structure_handle, clean=False
)

print(f"Dirty price of the floating rate bond: {price:.4f}")
