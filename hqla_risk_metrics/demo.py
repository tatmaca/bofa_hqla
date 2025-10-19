import os
import sys

# Ensure agentic/src is on path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../agentic/src"))
)

from assets import Asset, Level1Asset

# Imports from src
from portfolio import Portfolio

# Imports from local package
from portfolio_metrics import (
    adjusted_portfolio_value,
    compute_lcr,
    compute_nsfr,
    compute_rwa,
    portfolio_value,
)

# --- Demo code ---
p = Portfolio()
cash = Level1Asset(name="Cash", market_value=100_000_000)
ust = Level1Asset(name="UST_10Y", market_value=50_000_000)

p.add_asset(cash)
p.add_asset(ust)

print("Total market value:", portfolio_value(p))
print("Adjusted market value:", adjusted_portfolio_value(p))
print("LCR:", compute_lcr(p))
print("RWA:", compute_rwa(p))
print("NSFR:", compute_nsfr(p))
