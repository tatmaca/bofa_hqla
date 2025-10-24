from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass

"""
credit_risk/probs.py

Reads ./data/credit_features.csv (from fetch_credit_data.py) and computes
30d/90d probabilities for credit spread scenarios:
- Mild Credit Tightening
- Severe Credit Shock
- Spread Compression

We map standardized credit pressure (z-scores) into probabilities using
an exponential mapping (aligned with the Liquidity module), with
scenario-specific bases/sensitivities/caps.
"""

@dataclass
class MapParams:
    base_90d: float   
    sens: float       
    cap: float        
    
PARAMS = {
    "mild":     MapParams(base_90d=0.25, sens=0.60, cap=0.80),
    "severe":   MapParams(base_90d=0.08, sens=0.90, cap=0.60),
    "compress": MapParams(base_90d=0.22, sens=0.55, cap=0.75),
}

def p30_from_p90(p90: np.ndarray) -> np.ndarray:
    return 1.0 - np.power(1.0 - p90, 1.0/3.0)

def _ensure_composite(df: pd.DataFrame, roll:int=252) -> pd.DataFrame:
    out = df.copy()
    if "CREDIT_Z_COMPOSITE" not in out.columns:
        zcols = [c for c in out.columns if c.endswith(f"_z_{roll}") and any(k in c for k in ["IG_OAS","HY_OAS"])]
        if not zcols:
            raise ValueError("No *_z_252 columns for IG/HY found; cannot compute composite credit z.")
        out["CREDIT_Z_COMPOSITE"] = out[zcols].mean(axis=1)
    return out

def _map_prob(z: np.ndarray, params: MapParams) -> np.ndarray:
    p90 = params.base_90d * np.exp(params.sens * z)
    return np.clip(p90, 0.0, params.cap)

def compute_credit_probs(features: pd.DataFrame) -> pd.DataFrame:
    X = _ensure_composite(features)

    z_mild  = X["CREDIT_Z_COMPOSITE"].values
    z_sev   = np.maximum(0.0, X["CREDIT_Z_COMPOSITE"].values - 1.0)   # tail focus
    z_comp  = np.maximum(0.0, -X["CREDIT_Z_COMPOSITE"].values)        # negative side

    p90_mild = _map_prob(z_mild,  PARAMS["mild"])
    p90_sev  = _map_prob(z_sev,   PARAMS["severe"])
    p90_comp = _map_prob(z_comp,  PARAMS["compress"])

    out = pd.DataFrame({
        "P30_mild": p30_from_p90(p90_mild),  "P90_mild": p90_mild,
        "P30_severe": p30_from_p90(p90_sev), "P90_severe": p90_sev,
        "P30_compress": p30_from_p90(p90_comp), "P90_compress": p90_comp,
    }, index=X.index)

    out.attrs["z_definition"] = {
        "mild": "CREDIT_Z_COMPOSITE",
        "severe": "max(CREDIT_Z_COMPOSITE - 1.0, 0)",
        "compress": "max(-CREDIT_Z_COMPOSITE, 0)"
    }
    out.attrs["params"] = {k: vars(v) for k, v in PARAMS.items()}
    return out
