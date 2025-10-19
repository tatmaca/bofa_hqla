"""
demo_scenarios.py
-----------------
Demo applying interest rate scenarios to a simple HQLA portfolio.

Author: Togay Atmaca
Created: 2025-10-19
"""

import sys
import os

# Ensure agentic/src is on path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../agentic/src"))
)

from portfolio import Portfolio
from assets import Asset, Level1Asset
from portfolio_metrics import (
    adjusted_portfolio_value,
    compute_lcr,
    compute_nsfr,
    compute_rwa,
    portfolio_value,
)
from scenario_shocks import YCSteepening, YCFlattening

# --- Build a simple portfolio ---
p = Portfolio()
cash = Level1Asset(name="Cash", market_value=100_000_000)
ust = Level1Asset(name="UST_10Y", market_value=50_000_000)

p.add_asset(cash)
p.add_asset(ust)

print("Original Portfolio:")
print("Total market value:", portfolio_value(p))
print("Adjusted market value:", adjusted_portfolio_value(p))
print("LCR:", compute_lcr(p))
print("RWA:", compute_rwa(p))
print("NSFR:", compute_nsfr(p))
print("-" * 50)

# --- Apply YC Steepening ---
steep = YCSteepening(magnitude=0.05)
p_steep = steep.apply(p)

print(f"After YC Steepening (prob={steep.probability:.3f}):")
print("Total market value:", portfolio_value(p_steep))
print("Adjusted market value:", adjusted_portfolio_value(p_steep))
print("LCR:", compute_lcr(p_steep))
print("RWA:", compute_rwa(p_steep))
print("NSFR:", compute_nsfr(p_steep))
print("-" * 50)

# --- Apply YC Flattening ---
flat = YCFlattening(magnitude=0.05)
p_flat = flat.apply(p)

print(f"After YC Flattening (prob={flat.probability:.3f}):")
print("Total market value:", portfolio_value(p_flat))
print("Adjusted market value:", adjusted_portfolio_value(p_flat))
print("LCR:", compute_lcr(p_flat))
print("RWA:", compute_rwa(p_flat))
print("NSFR:", compute_nsfr(p_flat))
print("-" * 50)
