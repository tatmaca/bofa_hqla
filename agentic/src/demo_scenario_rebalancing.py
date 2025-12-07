import os
import QuantLib as ql
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from hqla_assets import Level1Discount, Level1Floating, Level1Fixed, Level2AFixed, Level2BFloating, Floating
from hqla_portfolio import Portfolio
from hqla_portfolio_opt import HQLA_Portfolio_Opt_Enhanced
from scenario_rebalancing import Scenario, ScenarioRebalancingEngine

"""
Test script for the scenario rebalancing. 
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




# ------------------------
# Set evaluation date
# ------------------------
today = ql.Date(8, 11, 2025)
ql.Settings.instance().evaluationDate = today


# --- Add historical fixings for all floating-rate bonds ---
sofr_rate = 0.045  # historical fixing rate
sofr_index = ql.Sofr(sofr_handle)
calendar = sofr_index.fixingCalendar()

for level in ["L1", "L2B"]:
    for inst in portfolio.assets[level]:
        if isinstance(inst, Floating) and hasattr(inst, "schedule"):
            for date in inst.schedule:
                if date <= ql.Settings.instance().evaluationDate:
                    adjusted_date = calendar.adjust(date, ql.Preceding)
                    sofr_index.addFixing(adjusted_date, sofr_rate)


# ------------------------
# Create ScenarioRebalancingEngine
# ------------------------
engine = ScenarioRebalancingEngine(base_portfolio=portfolio, net_cash_outflow=1_000_000)

# ------------------------
# Define scenarios with small yield variations
# ------------------------
scenarios_dict = {
    "Base": {"description": "Base flat yield curve", "probability": 0.4},
    "Rate_Spike": {"description": "Rates increase by 50 bps", "probability": 0.2},
    "Rate_Drop": {"description": "Rates drop by 50 bps", "probability": 0.2},
    "Liquidity_Stress": {"description": "Liquidity stress, minor haircuts applied", "probability": 0.2},
}

# Convert dict to Scenario objects
for name, data in scenarios_dict.items():
    # Create simple yield curve variation for scenario
    base_rate = 0.03
    if name == "Rate_Spike":
        rate = base_rate + 0.005
    elif name == "Rate_Drop":
        rate = base_rate - 0.005
    else:
        rate = base_rate

    simple_quote = ql.SimpleQuote(rate)
    qlh = ql.YieldTermStructureHandle(ql.FlatForward(today, ql.QuoteHandle(simple_quote), ql.Actual360()))
    
    scen = Scenario(
        name=name,
        yield_curve_handle=qlh,
        sofr_handle=None,
        probability=data["probability"],
        metadata={"description": data["description"]}
    )
    engine.add_scenario(scen)


engine.run_full_workflow_with_scenarios(scenarios_dict=scenarios_dict, openai_api_key=os.environ.get("OPENAI_API_KEY"))
