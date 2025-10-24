from __future__ import annotations
import numpy as np
import pandas as pd

BASE = 0.25
SENS = 0.60
CAP  = 0.80

def _ensure_col(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    # build slope if missing
    if "SLOPE_2s10s_bps" not in X.columns and {"DGS2","DGS10"}.issubset(X.columns):
        X["SLOPE_2s10s_bps"] = (X["DGS10"] - X["DGS2"]) * 100.0
    # build z-scores if missing
    for col in ["MOVE", "SLOPE_2s10s_bps", "SURPRISE", "EFFR"]:
        if col in X.columns and f"{col}_z_252" not in X.columns:
            mu = X[col].rolling(252, min_periods=126).mean()
            sd = X[col].rolling(252, min_periods=126).std(ddof=1).clip(lower=1e-8)
            X[f"{col}_z_252"] = (X[col] - mu) / sd
    return X

def compute_liquidity_probs(features: pd.DataFrame) -> pd.DataFrame:
    """
    Deterministic mapping for liquidity stress probs using available z-scores.
    Prefers MOVE z; falls back to SLOPE z, then averages if both exist.
    Returns columns: P30_stress, P90_stress on the SAME index as features.
    """
    X = _ensure_col(features)

    zcands = [c for c in ["MOVE_z_252","SLOPE_2s10s_bps_z_252","SURPRISE_z_252","EFFR_z_252"] if c in X.columns]
    if not zcands:
        raise ValueError("Liquidity mapping needs at least one of MOVE/SLOPE/SURPRISE/EFFR z-scores.")

    # prefer MOVE; else average available
    if "MOVE_z_252" in zcands:
        zbar = X["MOVE_z_252"]
    elif "SLOPE_2s10s_bps_z_252" in zcands:
        zbar = X["SLOPE_2s10s_bps_z_252"]
    else:
        zbar = X[zcands].mean(axis=1)

    p90 = np.clip(BASE * np.exp(SENS * zbar), 0.0, CAP)
    p30 = 1 - (1 - p90) ** (1/3)

    # no dropna on the tail; keep index aligned
    return pd.DataFrame({"P30_stress": p30, "P90_stress": p90}, index=X.index)