from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
from probs import compute_credit_probs
from prompt_template import SCENARIO_PROMPT
PKG_ROOT = Path(__file__).resolve().parent

CWD = Path.cwd()
def _find_data_dir() -> Path:
    candidates = [
        PKG_ROOT.parent / "data",                 
        PKG_ROOT.parents[1] / "data",             
        CWD / "data",                            
        Path(r"C:\Users\xiang\Desktop\credit_risk\data"),  
    ]
    for p in candidates:
        if (p / "credit_features.csv").exists():
            return p
    return candidates[0]


DATA_DIR = _find_data_dir()



def _format_prompt(latest_row: pd.Series, latest_probs: pd.Series) -> str:
    def has(keys):  
        return all(k in latest_row.index for k in keys)

    opt_vix = (
        f"- VIX={latest_row['VIXCLS']:.1f} (z={latest_row['VIXCLS_z_252']:.2f}, 1mΔ={latest_row['VIXCLS_chg_21d']:.1f})"
        if has(["VIXCLS","VIXCLS_z_252","VIXCLS_chg_21d"]) else ""
    )
    opt_move = (
        f"- MOVE={latest_row['MOVE']:.1f} (z={latest_row['MOVE_z_252']:.2f}, 1mΔ={latest_row['MOVE_chg_21d']:.1f})"
        if has(["MOVE","MOVE_z_252","MOVE_chg_21d"]) else ""
    )
    opt_slope = (
        f"- 2s10s slope={latest_row['SLOPE_2s10s_bps']:.1f} bp (z={latest_row['SLOPE_2s10s_bps_z_252']:.2f}, 1mΔ={latest_row['SLOPE_2s10s_bps_chg_21d']:.1f})"
        if has(["SLOPE_2s10s_bps","SLOPE_2s10s_bps_z_252","SLOPE_2s10s_bps_chg_21d"]) else ""
    )

    return SCENARIO_PROMPT.format(
        IG_OAS=latest_row["IG_OAS"],
        IG_OAS_z=latest_row["IG_OAS_z_252"],
        IG_OAS_chg=latest_row["IG_OAS_chg_21d"],
        HY_OAS=latest_row["HY_OAS"],
        HY_OAS_z=latest_row["HY_OAS_z_252"],
        HY_OAS_chg=latest_row["HY_OAS_chg_21d"],
        OPT_VIX=opt_vix,
        OPT_MOVE=opt_move,
        OPT_SLOPE=opt_slope,
        P30_mild=latest_probs["P30_mild"],
        P90_mild=latest_probs["P90_mild"],
        P30_severe=latest_probs["P30_severe"],
        P90_severe=latest_probs["P90_severe"],
        P30_compress=latest_probs["P30_compress"],
        P90_compress=latest_probs["P90_compress"],
    )


def main():
    feats_path = DATA_DIR / "credit_features.csv"
    if not feats_path.exists():
        raise SystemExit(f"Missing {feats_path}. Run fetch_credit_data.py first")

    feats = pd.read_csv(feats_path, parse_dates=["Date"]).set_index("Date").sort_index()
    probs = compute_credit_probs(feats)

    latest_row = feats.iloc[-1]
    latest_probs = probs.iloc[-1]

    prompt = _format_prompt(latest_row, latest_probs)

    print("\n=== COPY THIS PROMPT INTO YOUR LLM ===\n")
    print(prompt)
    print("\n=== EXPECTED RESULT: a 5-column Scenario Matrix (Markdown) ===\n")


if __name__ == "__main__":
    main()
