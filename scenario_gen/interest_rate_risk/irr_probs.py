from __future__ import annotations
import numpy as np
import pandas as pd

def compute_irr_probs(features: pd.DataFrame) -> pd.DataFrame:
    """
    Use simple z-based mapping on SLOPE_2s10s_bps_z_252 to produce:
      P30_bear_steepen, P90_bear_steepen,
      P30_bull_flatten, P90_bull_flatten
    Deterministic, calibrated-by-constants (tune later).
    """
    X = features.copy()
    if "SLOPE_2s10s_bps_z_252" not in X.columns:
        # build z if missing
        if "SLOPE_2s10s_bps" not in X.columns:
            X["SLOPE_2s10s_bps"] = (X["DGS10"] - X["DGS2"]) * 100.0
        mu = X["SLOPE_2s10s_bps"].rolling(252, min_periods=126).mean()
        sd = X["SLOPE_2s10s_bps"].rolling(252, min_periods=126).std(ddof=1).clip(lower=1e-8)
        X["SLOPE_2s10s_bps_z_252"] = (X["SLOPE_2s10s_bps"] - mu) / sd

    z = X["SLOPE_2s10s_bps_z_252"].values

    # simple, tunable maps
    def map_exp(z_, base, sens, cap):
        p90 = np.clip(base * np.exp(sens * z_), 0.0, cap)
        p30 = 1 - (1 - p90) ** (1/3)
        return p30, p90

    # bear steepen (z positive → higher prob)
    p30_bs, p90_bs = map_exp(z, base=0.18, sens=0.45, cap=0.70)
    # bull flatten (z negative → higher prob) -> use -z
    p30_bf, p90_bf = map_exp(-z, base=0.15, sens=0.50, cap=0.65)

    out = pd.DataFrame({
        "P30_bear_steepen": p30_bs, "P90_bear_steepen": p90_bs,
        "P30_bull_flatten": p30_bf, "P90_bull_flatten": p90_bf,
    }, index=X.index)
    return out.dropna()