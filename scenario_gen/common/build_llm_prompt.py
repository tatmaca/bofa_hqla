# scenario_gen/common/build_llm_prompt.py
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PROBS_CSV = ROOT / "scenario_gen" / "combined_probabilities.csv"
SHOCKS_JSON = ROOT / "shocks" / "shocks_resolved.json"
CORR_CSV = ROOT / "scenario_gen" / "correlations" / "corr_21d_changes.csv"
FEATURES_CSV = ROOT / "new_credit_data" / "credit_features.csv"

SCEN_KEYS = [
    "credit/mild",
    "credit/severe",
    "credit/compress",
    "liquidity/stress",
    "interest_rate/bear_steepen",
    "interest_rate/bull_flatten",
]

FRIENDLY = {
    "credit/mild": "Mild Credit Tightening",
    "credit/severe": "Severe Credit Shock",
    "credit/compress": "Credit Spread Compression",
    "liquidity/stress": "Liquidity Stress",
    "interest_rate/bear_steepen": "Bear Steepening",
    "interest_rate/bull_flatten": "Bull Flattening",
}

PROMPT_TEMPLATE = """You are assisting the Scenario Generation team for a bank’s HQLA program. 
Produce a 6-month Scenario Matrix that is strictly formatted as a GitHub-flavored Markdown table with 5 columns:
Scenario | Description | Probability | Rationale | Impact Channels

## As-of
{AS_OF_DATE}

## Inputs (do not invent or change these)
### A) Scenario Probabilities (30d & 90d)
P30:credit/mild={P30_credit_mild:.4f},       P90:credit/mild={P90_credit_mild:.4f}           (Mild Credit Tightening)
P30:credit/severe={P30_credit_severe:.4f},   P90:credit/severe={P90_credit_severe:.4f}       (Severe Credit Shock)
P30:credit/compress={P30_credit_compress:.4f}, P90:credit/compress={P90_credit_compress:.4f} (Spread Compression)
P30:liquidity/stress={P30_liq_stress:.4f},   P90:liquidity/stress={P90_liq_stress:.4f}       (Liquidity Stress)
P30:interest_rate/bear_steepen={P30_bear:.4f}, P90:interest_rate/bear_steepen={P90_bear:.4f} (Bear Steepening)
P30:interest_rate/bull_flatten={P30_bull:.4f}, P90:interest_rate/bull_flatten={P90_bull:.4f} (Bull Flattening)

### B) Shock Vectors (from YAML; do not change magnitudes)
credit/mild: {{IG_OAS_bp: {shock_credit_mild_IG}, HY_OAS_bp: {shock_credit_mild_HY}}}
credit/severe: {{IG_OAS_bp: {shock_credit_severe_IG}, HY_OAS_bp: {shock_credit_severe_HY}}}
credit/compress: {{IG_OAS_bp: {shock_credit_compress_IG}, HY_OAS_bp: {shock_credit_compress_HY}}}
liquidity/stress: {{MOVE_pts: {shock_liq_MOVE}, SLOPE_2s10s_bps: {shock_liq_SLOPE}, funding_spread_bp: {shock_liq_FUND}}}
interest_rate/bear_steepen: {{DGS2_bp: {shock_bear_D2}, DGS10_bp: {shock_bear_D10}, SLOPE_2s10s_bps: {shock_bear_SLOPE}}}
interest_rate/bull_flatten: {{DGS2_bp: {shock_bull_D2}, DGS10_bp: {shock_bull_D10}, SLOPE_2s10s_bps: {shock_bull_SLOPE}}}

### C) Correlation Cues (21-day changes; use as rationale context, not to change probabilities)
IG_OAS_chg_21d ↔ HY_OAS_chg_21d = {corr_ig_hy:+.2f}
IG_OAS_chg_21d ↔ MOVE_chg_21d   = {corr_ig_move:+.2f}
HY_OAS_chg_21d ↔ MOVE_chg_21d   = {corr_hy_move:+.2f}
SLOPE_2s10s_bps_chg_21d ↔ IG_OAS_chg_21d = {corr_slope_ig:+.2f}
SLOPE_2s10s_bps_chg_21d ↔ MOVE_chg_21d   = {corr_slope_move:+.2f}

### D) Optional context snapshot (plain text)
- IG OAS={IG_OAS:.1f}bp (z={IG_OAS_z:.2f}, 1mΔ={IG_OAS_d1m:.1f}); HY OAS={HY_OAS:.1f}bp (z={HY_OAS_z:.2f}, 1mΔ={HY_OAS_d1m:.1f})
- MOVE={MOVE:.1f} (z={MOVE_z:.2f}, 1mΔ={MOVE_d1m:.1f}); 2s10s slope={SLOPE_2s10s_bps:.1f}bp (z={SLOPE_z:.2f}, 1mΔ={SLOPE_d1m:.1f})

## Output requirements (strict)
1) Output only one GitHub-flavored Markdown table. No prose, no headings, no code fences.
2) Columns: Scenario | Description | Probability | Rationale | Impact Channels
3) 4–6 rows; include at least one from Credit, Liquidity, and Interest Rate.
4) For Probability, use the 90d value provided above, as a single percent with one decimal (e.g., 27.3 %).
5) Keep cells ≤ 2 lines; reference shocks and correlation cues in Rationale and Impact Channels.
6) Do not invent probabilities or scenarios beyond the provided keys.

## Friendly names for the “Scenario” column
- credit/mild → Mild Credit Tightening
- credit/severe → Severe Credit Shock
- credit/compress → Credit Spread Compression
- liquidity/stress → Liquidity Stress
- interest_rate/bear_steepen → Bear Steepening
- interest_rate/bull_flatten → Bull Flattening

Now generate the table.
"""

def _latest_probs_row(probs_csv: Path) -> pd.Series:
    df = pd.read_csv(probs_csv, parse_dates=["Date"]).set_index("Date").sort_index()
    return df.iloc[-1]

def _load_shocks(shocks_json: Path) -> dict:
    return json.loads(Path(shocks_json).read_text())

def _safe_get(d: dict, key: str, default=np.nan):
    return d.get(key, default)

def _corr_lookup(corr_csv: Path, a: str, b: str) -> float:
    if not corr_csv.exists():
        return np.nan
    corr = pd.read_csv(corr_csv, index_col=0)
    # Support both square matrix and tidy long file:
    if {"var_a","var_b","roll_corr"}.issubset(corr.columns):
        # pick last available rolling corr per pair
        sub = corr[(corr["var_a"]==a) & (corr["var_b"]==b)]
        if not sub.empty:
            return float(sub["roll_corr"].dropna().iloc[-1])
        sub = corr[(corr["var_a"]==b) & (corr["var_b"]==a)]
        if not sub.empty:
            return float(sub["roll_corr"].dropna().iloc[-1])
        return np.nan
    # assume square matrix of static correlations
    if a in corr.index and b in corr.columns:
        return float(corr.loc[a, b])
    if b in corr.index and a in corr.columns:
        return float(corr.loc[b, a])
    return np.nan

def _snapshot(features_csv: Path) -> dict:
    snap = {k: np.nan for k in [
        "IG_OAS","IG_OAS_z_252","IG_OAS_chg_21d",
        "HY_OAS","HY_OAS_z_252","HY_OAS_chg_21d",
        "MOVE","MOVE_z_252","MOVE_chg_21d",
        "SLOPE_2s10s_bps","SLOPE_2s10s_bps_z_252","SLOPE_2s10s_bps_chg_21d",
    ]}
    if not features_csv.exists():
        return snap
    feats = pd.read_csv(features_csv, parse_dates=["Date"]).set_index("Date").sort_index()
    row = feats.iloc[-1]
    for k in snap.keys():
        if k in row.index:
            snap[k] = float(row[k])
    return snap

def build_prompt(as_of: str | None = None,
                 probs_csv: Path = PROBS_CSV,
                 shocks_json: Path = SHOCKS_JSON,
                 corr_csv: Path = CORR_CSV,
                 features_csv: Path = FEATURES_CSV) -> str:
    latest = _latest_probs_row(probs_csv)

    # map probs to fields expected by the template
    def getp(prefix: str, key: str) -> float:
        col = f"{prefix}:{key}"
        return float(latest[col]) if col in latest.index and pd.notna(latest[col]) else np.nan

    # shocks
    shocks = _load_shocks(shocks_json)

    # correlations (static or last rolling)
    ig_hy = _corr_lookup(corr_csv, "IG_OAS_chg_21d", "HY_OAS_chg_21d")
    ig_move = _corr_lookup(corr_csv, "IG_OAS_chg_21d", "MOVE_chg_21d")
    hy_move = _corr_lookup(corr_csv, "HY_OAS_chg_21d", "MOVE_chg_21d")
    slope_ig = _corr_lookup(corr_csv, "SLOPE_2s10s_bps_chg_21d", "IG_OAS_chg_21d")
    slope_move = _corr_lookup(corr_csv, "SLOPE_2s10s_bps_chg_21d", "MOVE_chg_21d")

    # snapshot
    s = _snapshot(features_csv)

    # convenience getters for shocks with NaN default
    def shock(key: str, var: str) -> float:
        return float(_safe_get(shocks.get(key, {}), var, np.nan))

    # render
    return PROMPT_TEMPLATE.format(
        AS_OF_DATE = as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        # probs
        P30_credit_mild = getp("P30", "credit/mild"),
        P90_credit_mild = getp("P90", "credit/mild"),
        P30_credit_severe = getp("P30", "credit/severe"),
        P90_credit_severe = getp("P90", "credit/severe"),
        P30_credit_compress = getp("P30", "credit/compress"),
        P90_credit_compress = getp("P90", "credit/compress"),
        P30_liq_stress = getp("P30", "liquidity/stress"),
        P90_liq_stress = getp("P90", "liquidity/stress"),
        P30_bear = getp("P30", "interest_rate/bear_steepen"),
        P90_bear = getp("P90", "interest_rate/bear_steepen"),
        P30_bull = getp("P30", "interest_rate/bull_flatten"),
        P90_bull = getp("P90", "interest_rate/bull_flatten"),
        # shocks
        shock_credit_mild_IG = shock("credit/mild","IG_OAS_bp"),
        shock_credit_mild_HY = shock("credit/mild","HY_OAS_bp"),
        shock_credit_severe_IG = shock("credit/severe","IG_OAS_bp"),
        shock_credit_severe_HY = shock("credit/severe","HY_OAS_bp"),
        shock_credit_compress_IG = shock("credit/compress","IG_OAS_bp"),
        shock_credit_compress_HY = shock("credit/compress","HY_OAS_bp"),
        shock_liq_MOVE = shock("liquidity/stress","MOVE_pts"),
        shock_liq_SLOPE = shock("liquidity/stress","SLOPE_2s10s_bps"),
        shock_liq_FUND = shock("liquidity/stress","funding_spread_bp"),
        shock_bear_D2 = shock("interest_rate/bear_steepen","DGS2_bp"),
        shock_bear_D10 = shock("interest_rate/bear_steepen","DGS10_bp"),
        shock_bear_SLOPE = shock("interest_rate/bear_steepen","SLOPE_2s10s_bps"),
        shock_bull_D2 = shock("interest_rate/bull_flatten","DGS2_bp"),
        shock_bull_D10 = shock("interest_rate/bull_flatten","DGS10_bp"),
        shock_bull_SLOPE = shock("interest_rate/bull_flatten","SLOPE_2s10s_bps"),
        # correlations
        corr_ig_hy = ig_hy,
        corr_ig_move = ig_move,
        corr_hy_move = hy_move,
        corr_slope_ig = slope_ig,
        corr_slope_move = slope_move,
        # snapshot
        IG_OAS = s["IG_OAS"], IG_OAS_z = s["IG_OAS_z_252"], IG_OAS_d1m = s["IG_OAS_chg_21d"],
        HY_OAS = s["HY_OAS"], HY_OAS_z = s["HY_OAS_z_252"], HY_OAS_d1m = s["HY_OAS_chg_21d"],
        MOVE = s["MOVE"], MOVE_z = s["MOVE_z_252"], MOVE_d1m = s["MOVE_chg_21d"],
        SLOPE_2s10s_bps = s["SLOPE_2s10s_bps"], SLOPE_z = s["SLOPE_2s10s_bps_z_252"], SLOPE_d1m = s["SLOPE_2s10s_bps_chg_21d"],
    )

def main():
    ap = argparse.ArgumentParser(description="Build a fully-populated LLM prompt for the Scenario Matrix.")
    ap.add_argument("--probs", default=str(PROBS_CSV))
    ap.add_argument("--shocks", default=str(SHOCKS_JSON))
    ap.add_argument("--corr", default=str(CORR_CSV))
    ap.add_argument("--features", default=str(FEATURES_CSV))
    ap.add_argument("--out", default=str(ROOT / "scenario_gen" / "LLM_prompt.txt"), help="Optional file to write the prompt.")
    ap.add_argument("--no-write", action="store_true", help="Only print to stdout, do not write to file.")
    args = ap.parse_args()

    prompt = build_prompt(
        probs_csv=Path(args.probs),
        shocks_json=Path(args.shocks),
        corr_csv=Path(args.corr),
        features_csv=Path(args.features),
    )
    print("\n=== COPY INTO LLM ===\n")
    print(prompt)
    if not args.no_write:
        Path(args.out).write_text(prompt, encoding="utf-8")
        print(f"\n[OK] wrote {args.out}")

if __name__ == "__main__":
    main()