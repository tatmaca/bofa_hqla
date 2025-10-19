"""
irr_yc_probs.py
-----------------------
Computes historical 6-month probabilities of yield curve steepening and flattening
for 2y/10y U.S. Treasuries using CSV yield data.

Author: Togay Atmaca
Created: 2025-10-19
"""

import sys

import pandas as pd

sys.path.append("../../src")  # adjust if running from interest_rate_risk folder
from irr_historical import compute_2s10s, historical_probabilities

# Load yield data
dgs2 = pd.read_csv(
    "../../data/DGS2.csv",
    parse_dates=["observation_date"],
    index_col="observation_date",
)
dgs10 = pd.read_csv(
    "../../data/DGS10.csv",
    parse_dates=["observation_date"],
    index_col="observation_date",
)

# Align dates
df = pd.concat([dgs2["DGS2"], dgs10["DGS10"]], axis=1).dropna()
df.columns = ["yield_2y", "yield_10y"]

# Compute 2s10s spread in bps
spread = compute_2s10s(df["yield_2y"], df["yield_10y"])

# Historical probability calculation (6 months ~ 126 trading days)
hist_stats = historical_probabilities(spread, horizon_days=126, threshold=25.0)
print("Historical probability results:")
for k, v in hist_stats.items():
    print(f"{k}: {v}")
