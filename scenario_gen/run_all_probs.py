from __future__ import annotations
from pathlib import Path
import pandas as pd

from scenario_gen.credit_risk.probs import compute_credit_probs
from scenario_gen.liquidity_risk.probs import compute_liquidity_probs
from scenario_gen.interest_rate_risk.irr_probs import compute_irr_probs

ROOT = Path(__file__).resolve().parents[1]
FEATS = ROOT / "new_credit_data" / "credit_features.csv"
OUT  = ROOT / "scenario_gen" / "combined_probabilities.csv"

def _canon(df: pd.DataFrame, risk: str) -> pd.DataFrame:
    """
    Convert columns like 'P90_mild' or 'P90_stress' to 'P90:<risk>/<scenario>'
    """
    out = {}
    for c in df.columns:
        h, sid = c.split("_", 1)  # e.g., P90, mild
        out[c] = f"{h}:{risk}/{sid}"
    return df.rename(columns=out)

def main():
    feats = pd.read_csv(FEATS, parse_dates=["Date"]).set_index("Date").sort_index()

    credit = _canon(compute_credit_probs(feats), "credit")
    liq    = _canon(compute_liquidity_probs(feats), "liquidity")
    rates  = _canon(compute_irr_probs(feats), "interest_rate")

    merged = pd.concat([credit, liq, rates], axis=1).sort_index()
    # tidy col order
    def _key(c):
        h, rest = c.split(":", 1); r, s = rest.split("/", 1)
        return (h, r, s)
    merged = merged.reindex(sorted(merged.columns, key=_key), axis=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT, float_format="%.6f")
    print(f"[OK] wrote {OUT} shape={merged.shape}")
    print(merged.tail(2).to_string())

if __name__ == "__main__":
    main()