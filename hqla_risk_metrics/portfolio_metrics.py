"""
portfolio_metrics.py
--------------------
Compute portfolio-level HQLA metrics: LCR, NSFR, RWA, market value.

Author: Togay Atmaca
Created: 2025-10-19
"""

import os
import sys

sys.path.append(os.path.abspath("../agentic/src"))

from typing import Dict

from base import LCR_LIQUIDITY_FACTORS, RWA_WEIGHTS
from portfolio import Portfolio


def portfolio_value(portfolio: Portfolio) -> float:
    """Return total market value of portfolio."""
    return portfolio.total_value()


def adjusted_portfolio_value(portfolio: Portfolio) -> float:
    """Return adjusted value using asset-level haircuts."""
    return portfolio.adjusted_value()


def compute_lcr(portfolio: Portfolio) -> float:
    """
    Simple LCR: sum(adjusted HQLA value * liquidity factor) / total net cash outflows.
    For now, assume net cash outflows = 1 (normalized), returns ratio.
    """
    total_hqla = 0.0
    for cat, assets in portfolio.assets.items():
        factor = LCR_LIQUIDITY_FACTORS.get(cat, 0.0)
        total_hqla += factor * sum(a.adjusted_value() for a in assets)
    # Normalize by total market value (or cash outflows placeholder)
    return total_hqla / max(portfolio.total_value(), 1e-9)


def compute_rwa(portfolio: Portfolio) -> float:
    """
    Compute simple RWA = sum(asset value * risk weight)
    """
    total_rwa = 0.0
    for cat, assets in portfolio.assets.items():
        weight = RWA_WEIGHTS.get(cat, 0.0)
        total_rwa += weight * sum(a.adjusted_value() for a in assets)
    return total_rwa


def compute_nsfr(portfolio: Portfolio) -> float:
    """
    Simple NSFR: stable funding ratio
    NSFR = Available stable funding / Required stable funding
    For demo: ASF = adjusted HQLA * liquidity factor
              RSF = total portfolio value
    """
    asf = sum(
        LCR_LIQUIDITY_FACTORS.get(cat, 0.0) * sum(a.adjusted_value() for a in assets)
        for cat, assets in portfolio.assets.items()
    )
    rsf = portfolio.total_value()
    return asf / max(rsf, 1e-9)
