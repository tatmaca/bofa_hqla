# scenario_gen/common/correlations.py
from __future__ import annotations
import argparse
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # repo root
FEATS = ROOT / "new_credit_data" / "credit_features.csv"
OUTDIR = ROOT / "scenario_gen" / "correlations"
OUTDIR.mkdir(parents=True, exist_ok=True)

# prefer 21d changes (scenario horizon-friendly); fall back to daily diffs if needed
CANDIDATES = [
    "IG_OAS_chg_21d",
    "HY_OAS_chg_21d",
    "VIXCLS_chg_21d",
    "MOVE_chg_21d",
    "SLOPE_2s10s_bps_chg_21d",
    # add more here if you add features later
]

def _pick_columns(df: pd.DataFrame, extra: List[str] | None) -> pd.DataFrame:
    cols = [c for c in CANDIDATES if c in df.columns]
    if extra:
        cols += [c for c in extra if c in df.columns]
    if not cols:
        raise SystemExit("No matching *_chg_21d columns found in credit_features.csv")
    X = df[cols].dropna().copy()
    # winsorize lightly to reduce outlier influence
    X = X.apply(lambda s: s.clip(s.quantile(0.01), s.quantile(0.99)))
    return X

def _zscore(X: pd.DataFrame) -> pd.DataFrame:
    return (X - X.mean()) / X.std(ddof=1)

def compute_static_corr(X: pd.DataFrame) -> pd.DataFrame:
    # use z-scored 21d changes for scale-invariant correlations
    Z = _zscore(X)
    return Z.corr(method="pearson")

def compute_rolling_corr(X: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    Z = _zscore(X)
    # build a tidy (long) table of rolling correlations for every pair
    cols = list(Z.columns)
    pairs = [(cols[i], cols[j]) for i in range(len(cols)) for j in range(i+1, len(cols))]
    out_frames = []
    for a, b in pairs:
        rc = Z[a].rolling(window).corr(Z[b])
        out_frames.append(
            pd.DataFrame({"Date": Z.index, "var_a": a, "var_b": b, "roll_corr": rc.values})
        )
    out = pd.concat(out_frames, axis=0).dropna()
    out = out.sort_values(["var_a", "var_b", "Date"])
    return out

def main():
    ap = argparse.ArgumentParser(description="Compute correlation matrices from credit_features.csv")
    ap.add_argument("--feats", default=str(FEATS), help="Path to credit_features.csv")
    ap.add_argument("--window", type=int, default=252, help="Rolling window (trading days)")
    ap.add_argument("--no-rolling", action="store_true", help="Skip writing rolling correlations")
    ap.add_argument("--extra", nargs="*", default=[], help="Additional columns to include if present")
    args = ap.parse_args()

    feats = pd.read_csv(args.feats, parse_dates=["Date"]).set_index("Date").sort_index()
    X = _pick_columns(feats, args.extra)

    corr = compute_static_corr(X)
    corr_path = OUTDIR / "corr_21d_changes.csv"
    corr.to_csv(corr_path)
    print(f"[OK] wrote {corr_path} shape={corr.shape}")

    if not args.no_rolling:
        rc = compute_rolling_corr(X, window=args.window)
        rc_path = OUTDIR / f"rolling_corr_{args.window}d_long.csv"
        rc.to_csv(rc_path, index=False)
        print(f"[OK] wrote {rc_path} rows={len(rc):,}")

    # also dump a compact preview for quick eyeballing
    preview = corr.round(2)
    print("\n[Static correlation (rounded)]")
    print(preview.to_string())

if __name__ == "__main__":
    main()