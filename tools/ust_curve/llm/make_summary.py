#!/usr/bin/env python3
import os, sys, json, argparse
from pathlib import Path

# Get repo root - use git if available, otherwise go up 3 levels from script location
try:
    import subprocess as sp
    ROOT = Path(sp.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
except:
    ROOT = Path(__file__).resolve().parents[3]  # repo root
OUT_DIR = ROOT / "tools" / "ust_curve" / "llm" / "summaries"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def likely_drivers(delta, spreads_today):
    ideas = []
    dz = delta["zeros_pct"]; dsp = delta["spreads_pct"]
    # Short-end down more than long-end → dovish shift / cut odds
    if dz.get("2y", 0) <= -5*0.01 and dz.get("10y", 0) > dz.get("2y", 0):
        ideas.append("Market-implied policy path shifted dovish (front-end fell more than long-end).")
    # Long-end up with front-end stable → term-premium/supply
    if dz.get("30y", 0) >= 5*0.01 and abs(dz.get("2y", 0)) < 3*0.01:
        ideas.append("Long-end under pressure, consistent with higher term premium or duration supply.")
    # Belly up vs ends → macro growth optimism or issuance in belly
    if dz.get("5y", 0) - max(dz.get("2y",0), dz.get("10y",0)) >= 3*0.01:
        ideas.append("Belly led the selloff; could reflect growth optimism or belly-heavy issuance.")
    # Steepening 2s10s
    if dsp.get("2s10s", 0) > 5*0.01:
        ideas.append("Curve steepened (2s10s); often follows easing expectations or stronger long-run growth.")
    # Flattening long end
    if dsp.get("2s30s", 0) < -5*0.01:
        ideas.append("Long-end flattened; consistent with duration demand or disinflation impulse.")
    return ideas

def mk_md(snapshot):
    as_of = snapshot["as_of"]; prev = snapshot["prev"]
    zt = snapshot["today"]["zeros_pct"]
    zp = snapshot["prev_day"]["zeros_pct"]
    sp_t = snapshot["today"]["spreads_pct"]
    sp_p = snapshot["prev_day"]["spreads_pct"]
    dz = snapshot["delta"]["zeros_pct"]
    dsp = snapshot["delta"]["spreads_pct"]
    risks = snapshot["risks"]

    def row(k):
        return f"- **{k}**: {zt[k]:.2f}% (Δ {dz[k]:+,.02f}%) — prev {zp[k]:.2f}%"
    def srow(k, label):
        return f"- **{label}**: {sp_t[k]:.2f}% (Δ {dsp[k]:+,.02f}%) — prev {sp_p[k]:.2f}%"

    md = []
    md.append(f"# UST Zero Curve — {as_of}\n")
    md.append(f"Prev business day: {prev}\n")
    md.append("## Level (zeros, %)\n")
    for k in ["6m","1y","2y","3y","5y","7y","10y","20y","30y"]:
        if k in zt: md.append(row(k))
    md.append("\n## Slopes / Spreads\n")
    md.append(srow("2s10s","2s10s"))
    md.append(srow("2s30s","2s30s"))
    md.append(srow("5s30s","5s30s"))

    if risks:
        md.append("\n## Risk Flags")
        for r in risks:
            md.append(f"- **{r['flag']}** ({r['severity']}): {r['why']}")

    ideas = likely_drivers(snapshot["delta"], snapshot["today"]["spreads_pct"])
    if ideas:
        md.append("\n## Possible drivers (hypotheses)")
        for s in ideas:
            md.append(f"- {s}")
        md.append("\n*Heuristics only; confirm with news/auction calendars, inflation data, and Fed commentary.*")
    return "\n".join(md) + "\n"

def mk_llm_json(snapshot):
    return {
        "as_of": snapshot["as_of"],
        "prev": snapshot["prev"],
        "zeros_pct_today": snapshot["today"]["zeros_pct"],
        "zeros_pct_prev": snapshot["prev_day"]["zeros_pct"],
        "delta_zeros_pct": snapshot["delta"]["zeros_pct"],
        "spreads_today": snapshot["today"]["spreads_pct"],
        "spreads_prev": snapshot["prev_day"]["spreads_pct"],
        "delta_spreads_pct": snapshot["delta"]["spreads_pct"],
        "risk_flags": snapshot["risks"],
        "disclaimer": "Drivers listed are hypotheses based on curve geometry; verify with news and data."
    }

def main():
    ap = argparse.ArgumentParser(description="Create Markdown + compact JSON summaries for LLM from a curve snapshot.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (same as snapshot date)")
    args = ap.parse_args()

    snap_path = ROOT / "tools" / "ust_curve" / "llm" / "snapshots" / f"curve_snapshot_{args.date}.json"
    if not snap_path.exists():
        print(f"[ERR] Snapshot not found: {snap_path}")
        sys.exit(1)
    snapshot = json.loads(snap_path.read_text())

    md = mk_md(snapshot)
    md_path = OUT_DIR / f"curve_summary_{args.date}.md"
    md_path.write_text(md)
    print(f"[OK] Wrote {md_path}")

    lj = mk_llm_json(snapshot)
    lj_path = OUT_DIR / f"curve_llm_{args.date}.json"
    lj_path.write_text(json.dumps(lj, indent=2))
    print(f"[OK] Wrote {lj_path}")

if __name__ == "__main__":
    main()
