"""
fetch_credit_data.py

Purpose
-------
Fetch core credit-risk time series from FRED and prepare a feature set
that matches the Scenario Generation pipeline (z-scores + 1M changes),
so it can be plugged into your `scenario_gen/credit_risk/` module.

What it grabs (defaults; configurable via SERIES dict):
- IG_OAS  : ICE BofA US Corporate Index OAS        (FRED code: BAMLC0A0CM)
- HY_OAS  : ICE BofA US High Yield Index OAS       (FRED code: BAMLH0A0HYM2)
- DGS2    : 2-Year Treasury Yield
- DGS10   : 10-Year Treasury Yield
- VIXCLS  : CBOE Volatility Index (close)          (market risk proxy)
- MOVE    : ICE BofA MOVE Index (if available on FRED for your locale; otherwise skipped)

Outputs
-------
Creates a folder `./data` and writes:
- ./data/IG_OAS.csv, HY_OAS.csv, DGS2.csv, DGS10.csv, VIXCLS.csv, (MOVE.csv if fetched)
- ./data/credit_features.csv  (merged & engineered features)
All CSVs have a first column `Date` and one or more numeric columns.

Usage
-----
$ python3 fetch_credit_data.py
(Optionally set START=YYYY-MM-DD END=YYYY-MM-DD as env vars.)

"""

from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from pandas_datareader import data as pdr


# Default series to fetch from FRED: {local_name: fred_code}
SERIES: Dict[str, str] = {
    "IG_OAS":  "BAMLC0A0CM",
    "HY_OAS":  "BAMLH0A0HYM2",
    "DGS2":    "DGS2",
    "DGS10":   "DGS10",
    "VIXCLS":  "VIXCLS",
    # "MOVE":  "MOVE",   # Uncomment if your FRED instance provides MOVE; otherwise we'll try/except fetch below.
}

# Try to include MOVE opportunistically (won't fail the run if unavailable)
TRY_MOVE = True

ROLL_Z   = 252   
DELTA_N  = 21    

# Date range (read from env or defaults)
START = os.environ.get("START", "2005-01-01")
END   = os.environ.get("END",   datetime.today().strftime("%Y-%m-%d"))

# Output directory
OUT_DIR = Path(__file__).resolve().parents[2] / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_fred_series(code: str, start: str, end: str) -> pd.Series:
    """Fetch a single FRED series and return a clean Series indexed by DatetimeIndex."""
    df = pdr.DataReader(code, "fred", start=start, end=end)
    s = df.squeeze("columns")
    s = s.rename(code).dropna()
    s.index.name = "Date"
    return s

def _save_csv(series: pd.Series, local_name: str):
    """Save a single series as ./data/{name}.csv with 'Date' as the first column."""
    df = series.to_frame(name=local_name).copy()
    df.index = pd.to_datetime(df.index)
    df.reset_index(inplace=True)
    df.to_csv(OUT_DIR / f"{local_name}.csv", index=False)

def _rolling_z(x: pd.Series, window: int, min_periods: int | None = None, eps: float = 1e-8) -> pd.Series:
    mu = x.rolling(window, min_periods=min_periods or window//2).mean()
    sd = x.rolling(window, min_periods=min_periods or window//2).std(ddof=1).clip(lower=eps)
    return (x - mu) / sd

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add slope, 1m deltas, and rolling z-scores for IG/HY and VIX/MOVE where available."""
    out = df.copy()

    # 2s10s slope in bps if both columns exist
    if {"DGS2","DGS10"}.issubset(out.columns):
        out["SLOPE_2s10s_bps"] = (out["DGS10"] - out["DGS2"]) * 100.0

    base_cols = [c for c in out.columns if c in ["IG_OAS","HY_OAS","VIXCLS","MOVE","SLOPE_2s10s_bps"]]
    for c in base_cols:
        out[f"{c}_chg_{DELTA_N}d"] = out[c].diff(DELTA_N)
        out[f"{c}_z_{ROLL_Z}"]     = _rolling_z(out[c], ROLL_Z)

    # Composite credit pressure index: average of available z-scores among IG/HY (and optionally MOVE/VIX)
    z_cols = [c for c in out.columns if c.endswith(f"_z_{ROLL_Z}") and any(k in c for k in ["IG_OAS","HY_OAS"])]
    if not z_cols:
        raise ValueError("No z-score columns found for IG/HY OAS; cannot build composite credit pressure.")
    out["CREDIT_Z_COMPOSITE"] = out[z_cols].mean(axis=1)

    return out.dropna().copy()


def main():
    print(f"[INFO] Fetching FRED series from {START} to {END} ...")

    local_to_series = SERIES.copy()

    # Opportunistically include MOVE (won't fail if unavailable)
    if TRY_MOVE and "MOVE" not in local_to_series:
        try:
            s = _fetch_fred_series("MOVE", START, END)
            local_to_series["MOVE"] = "MOVE"
            print("[INFO] MOVE fetched successfully.")
        except Exception as e:
            print(f"[WARN] MOVE not available on your FRED endpoint: {e}")

    # Fetch all series
    fetched = {}
    for local_name, fred_code in local_to_series.items():
        try:
            s = _fetch_fred_series(fred_code, START, END)
            fetched[local_name] = s.rename(local_name)
            _save_csv(fetched[local_name], local_name)
            print(f"[OK] Saved {local_name}.csv  ({len(s):,} rows)")
        except Exception as e:
            print(f"[ERR] Failed to fetch {local_name} ({fred_code}): {e}")

    if not fetched:
        raise SystemExit("No series fetched. Check your internet or FRED availability.")

    # Merge to daily frame
    df = pd.concat(fetched.values(), axis=1).sort_index().dropna(how="all")

    # Engineer features
    feats = _engineer_features(df)

    # Save merged features
    feats_out = OUT_DIR / "credit_features.csv"
    feats.reset_index().rename(columns={"index":"Date"}).to_csv(feats_out, index=False)
    print(f"[OK] Saved engineered features -> {feats_out}  ({len(feats):,} rows)")

    # Print a small preview
    print("\n[HEAD] credit_features.csv preview:")
    print(feats.tail(5).to_string())

if __name__ == "__main__":
    main()
