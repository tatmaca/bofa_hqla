import pytest
import numpy as np
import pandas as pd
from hqla_portfolio_opt import HQLA_Portfolio_Opt_Enhanced
from hqla_portfolio import Portfolio
from hqla_assets import Level1Discount, Level1Floating, Level1Fixed, Level2AFixed, Level2BFloating
import QuantLib as ql

# -----------------------------
# SET EVALUATION DATE & CURVES
# -----------------------------
today = ql.Date(8, 11, 2025)
ql.Settings.instance().evaluationDate = today

# Flat 3% yield curve
flat_rate = ql.SimpleQuote(0.03)
rate_handle = ql.QuoteHandle(flat_rate)
day_count = ql.Actual360()
flat_yield_curve = ql.FlatForward(today, rate_handle, day_count, ql.Continuous)
discount_curve_handle = ql.YieldTermStructureHandle(flat_yield_curve)

# SOFR curve 4.5%
sofr_rate = 0.045
sofr_term_structure = ql.FlatForward(
    today,
    ql.QuoteHandle(ql.SimpleQuote(sofr_rate)),
    day_count,
    ql.Continuous
)
sofr_handle = ql.YieldTermStructureHandle(sofr_term_structure)
sofr_index = ql.Sofr(sofr_handle)

# -----------------------------
# DATES
# -----------------------------
issue = ql.Date(8, 6, 2024)
maturity_1y = ql.Date(8, 11, 2026)
maturity_2y = ql.Date(8, 11, 2027)
maturity_3y = ql.Date(8, 11, 2028)
maturity_5y = ql.Date(8, 11, 2030)

# -----------------------------
# BUILD PORTFOLIO
# -----------------------------
@pytest.fixture(scope="module")
def portfolio():
    p = Portfolio()

    # Level 1
    z1 = Level1Discount(
    issue_date=issue, 
    maturity_date=maturity_1y, 
    face_value=100, 
    quantity=0,  # Start with 0, optimizer will allocate
    name="L1_Zero_1Y", 
    isin="US0000000001"
)
    z1.build_bond()
    p.add_instrument(z1)

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
    p.add_instrument(fix1)

    f1 = Level1Floating(
            issue_date=issue, 
            maturity_date=maturity_2y, 
            face_value=100, 
            quantity=0, 
            name="L1_Floating_2Y", 
            isin="US0000000003"
        )
    f1.build_bond(index=sofr_index, spread=[0])
    p.add_instrument(f1)

    # Level 2A
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
    p.add_instrument(fx2a)

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
    p.add_instrument(fx2a_2)

    # Level 2B
    f2b = Level2BFloating(
        issue_date=issue, 
        maturity_date=maturity_3y, 
        face_value=100, 
        quantity=0, 
        name="L2B_Floating_3Y", 
        isin="US0000000006"
    )
    f2b.build_bond(index=sofr_index, spread=[150 * 1e-4])
    p.add_instrument(f2b)

    return p

# -----------------------------
# OPTIMIZER FIXTURE
# -----------------------------
@pytest.fixture(scope="module")
def optimizer(portfolio):
    return HQLA_Portfolio_Opt_Enhanced(portfolio, 1_000_000)

# -----------------------------
# TESTS
# -----------------------------
def test_weights_within_bounds(optimizer):
    df, res, _, _, _ = optimizer.mean_optimize()
    assert np.all(df["Allocated_Amount"] >= 0)
    assert np.all(df["Allocated_Amount"] <= optimizer.net_cash_outflow * 0.5)

def test_total_allocation_lcr_constraints(optimizer):
    df, res, total_alloc, _, lcr = optimizer.mean_optimize()
    assert optimizer.min_lcr <= lcr <= optimizer.max_lcr

def test_level_composition_constraints(optimizer):
    df, res, _, _, _ = optimizer.mean_optimize()
    levels = df["Level"].values
    weights = df["Allocated_Amount"].values / optimizer.net_cash_outflow
    assert np.sum(weights[levels == "L1"]) >= 0.6
    assert np.sum(weights[levels == "L2B"]) <= 0.15

def test_return_sensitivity_to_higher_ytm(optimizer):
    df, res, _, _, _ = optimizer.mean_optimize()
    old_alloc = df.set_index("Name")["Allocated_Amount"].copy()

    # Increase YTM of L2A assets
    optimizer.assets_summary.loc[optimizer.assets_summary["Level"]=="L2A", "YTM"] += 0.05
    df2, res2, _, _, _ = optimizer.mean_optimize()
    new_alloc = df2.set_index("Name")["Allocated_Amount"]

    # Compare first L2A asset
    l2a_name = optimizer.assets_summary[optimizer.assets_summary["Level"]=="L2A"]["Name"].values[0]
    assert new_alloc[l2a_name] > old_alloc[l2a_name]

def test_portfolio_duration_within_tolerance(optimizer):
    df, res, _, _, _ = optimizer.mean_optimize()
    duration = optimizer._compute_portfolio_duration(res.x)
    tol = optimizer.duration_tolerance
    target = optimizer.target_duration
    assert target - tol <= duration <= target + tol

def test_lexicographic_min_allocation(optimizer):
    df, res, total_alloc, _, _ = optimizer.lexicographic_mean_optimize()
    assert total_alloc <= optimizer.net_cash_outflow * 2.0

def test_mean_variance_allocation_changes_with_variance(optimizer):
    df, res, total_alloc, _, _ = optimizer.mean_variance_optimize_enhanced(lam=0.5)
    old_weights = res.x.copy()

    # Increase variance of asset 2 manually
    N = len(old_weights)
    Omega = np.eye(N) * 0.05
    Omega[1,1] = 1.0
    def obj(w):
        mu = np.array(optimizer.assets_summary["YTM"].values)
        return -(0.5 * w @ mu - 0.5 * (w @ (Omega @ w)))
    from scipy.optimize import minimize
    res_new = minimize(obj, x0=np.ones(N)/N, bounds=[(0,0.5)]*N)
    assert res_new.x[1] < old_weights[1]

def test_mean_variance_allocation_increases_with_mean(optimizer):
    df, res, total_alloc, _, _ = optimizer.mean_variance_optimize_enhanced(lam=0.5)
    old_weights = res.x.copy()
    optimizer.assets_summary.loc[0, "YTM"] += 0.05
    df2, res2, _, _, _ = optimizer.mean_variance_optimize_enhanced(lam=0.5)
    assert res2.x[0] > old_weights[0]
