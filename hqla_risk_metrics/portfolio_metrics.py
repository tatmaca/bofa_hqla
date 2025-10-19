"""
portfolio_metrics.py
--------------------
Calculates portfolio-level HQLA metrics under stress scenarios.

Author: Togay Atmaca
Created: 2025-10-19
"""

from portfolio import Portfolio

# Haircuts for each HQLA level (illustrative)
L1_HAIRCUT = 0.0  # Level 1 assets (cash + sovereigns)
L2A_HAIRCUT = 0.15  # Level 2A assets
L2B_HAIRCUT = 0.25  # Level 2B assets

# Risk weights for RWA calculation
RWA_WEIGHTS = {"L1": 0.0, "L2A": 0.2, "L2B": 0.5}

# Stable funding factors (illustrative)
STABLE_FUNDING_FACTORS = {
    "L1": 100.0,  # fully count towards stable funding
    "L2A": 50.0,  # 50% counts
    "L2B": 50.0,  # 50% counts
}


def portfolio_value(p: Portfolio) -> float:
    """Total market value of portfolio."""
    return sum(a.market_value for group in p.assets.values() for a in group)


def adjusted_portfolio_value(p: Portfolio) -> float:
    """Market value adjusted for haircuts."""
    total = 0.0
    for cat, assets in p.assets.items():
        haircut = 0.0
        if cat == "L1":
            haircut = L1_HAIRCUT
        elif cat == "L2A":
            haircut = L2A_HAIRCUT
        elif cat == "L2B":
            haircut = L2B_HAIRCUT
        total += sum(a.market_value * (1 - haircut) for a in assets)
    return total


def compute_lcr(p: Portfolio) -> float:
    """Liquidity Coverage Ratio under scenario-adjusted asset values."""
    hqla_adjusted = adjusted_portfolio_value(p)
    return hqla_adjusted / p.total_expected_outflows_30d


def compute_rwa(p: Portfolio) -> float:
    """Risk Weighted Assets under scenario-adjusted asset values."""
    total_rwa = 0.0
    for cat, assets in p.assets.items():
        weight = RWA_WEIGHTS.get(cat, 0.0)
        total_rwa += sum(a.market_value * weight for a in assets)
    return total_rwa


def compute_nsfr(p: Portfolio) -> float:
    """Net Stable Funding Ratio under scenario-adjusted asset values."""
    numerator = 0.0
    for cat, assets in p.assets.items():
        factor = STABLE_FUNDING_FACTORS.get(cat, 0.0) / 100.0
        numerator += sum(a.market_value * factor for a in assets)
    denominator = p.required_stable_funding
    return numerator / denominator
