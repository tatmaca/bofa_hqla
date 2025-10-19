"""
portfolio_summary.py
--------------------
Builds a string representation of a Portfolio before and after a scenario.

Author: Togay Atmaca
Created: 2025-10-19
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../hqla_risk_metrics"))
)

from portfolio import Portfolio
from portfolio_metrics import (
    adjusted_portfolio_value,
    compute_lcr,
    compute_nsfr,
    compute_rwa,
    portfolio_value,
)


def summarize_portfolio(portfolio: Portfolio, scenario_name: str = "Base") -> str:
    """
    Construct a summary string for a portfolio with metrics.

    Args:
        portfolio: Portfolio object
        scenario_name: Name of the scenario applied

    Returns:
        Multi-line string summary
    """
    lines = []
    lines.append(f"Scenario: {scenario_name}")
    lines.append("Asset        | Category | Market Value")
    lines.append("-" * 40)

    for cat, assets in portfolio.assets.items():
        for a in assets:
            lines.append(f"{a.name:<12} | {cat:<6} | {a.market_value:,.2f}")

    lines.append("-" * 40)
    lines.append(f"Total market value: {portfolio_value(portfolio):,.2f}")
    lines.append(f"Adjusted market value: {adjusted_portfolio_value(portfolio):,.2f}")
    lines.append(f"LCR: {compute_lcr(portfolio):.3f}")
    lines.append(f"NSFR: {compute_nsfr(portfolio):.3f}")
    lines.append(f"RWA: {compute_rwa(portfolio):,.2f}")

    return "\n".join(lines)
