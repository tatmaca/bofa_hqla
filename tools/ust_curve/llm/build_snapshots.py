#!/usr/bin/env python3
import os, sys, json, argparse, math, datetime as dt
from pathlib import Path

# --- Make repo root importable (so run_curve & book_irds3 work) ---
# Script is in tools/ust_curve/llm/, so go up 3 levels to get repo root
try:
    import subprocess as sp
    ROOT = Path(sp.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
except:
    ROOT = Path(__file__).resolve().parents[3]  # repo root
# Add both repo root and ust_curve directory to path for bookirds module
UST_CURVE_DIR = ROOT / "tools" / "ust_curve"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(UST_CURVE_DIR))

from tools.ust_curve import run_curve as rc  # reuse fetch/solve helpers

# ---------- simple linear interpolator on (x, y) points ----------
def lininterp(x, xs, ys):
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for (x0,y0),(x1,y1) in zip(zip(xs,ys), zip(xs[1:], ys[1:])):
        if x0 <= x <= x1:
            w = (x - x0)/(x1 - x0)
            return (1-w)*y0 + w*y1
    return ys[-1]

def pillars_to_zero_curve(pillars):
    # pillars: list of (tyears, DF, z_cc)
    xs = [t for t,_,_ in pillars]
    zs = [z for _,_,z in pillars]  # continuous comp (decimal, not %)
    return xs, zs

def compute_metrics(pillars):
    xs, zs = pillars_to_zero_curve(pillars)
    std_tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]  # Added 0.25 (3M)
    zeros = {int(t if t>=1 else 1 if math.isclose(t,0.5) else t): lininterp(t, xs, zs)*100.0 for t in std_tenors}
    # name keys nicely: 0.25 -> "3M", 0.5 -> "6m", 1+ -> "Ny"
    k = lambda y: f"{int(y)}y" if y>=1 else ("3M" if math.isclose(y, 0.25) else "6m")
    zeros_map = {k(t): round(lininterp(t, xs, zs)*100.0, 4) for t in std_tenors}
    # spreads (in %)
    s_2s10  = zeros_map["10y"] - zeros_map["2y"]
    s_2s30  = zeros_map["30y"] - zeros_map["2y"]
    s_5s30  = zeros_map["30y"] - zeros_map["5y"]
    return {
        "zeros_pct": zeros_map,
        "spreads_pct": {
            "2s10s": round(s_2s10, 4),
            "2s30s": round(s_2s30, 4),
            "5s30s": round(s_5s30, 4)
        }
    }

def detect_risks(metrics_today):
    z = metrics_today["zeros_pct"]; sp = metrics_today["spreads_pct"]
    risks = []
    if sp["2s10s"] < 0.0:
        risks.append({"flag":"inversion_2s10s", "severity":"high", "why":"2s10s spread < 0"})
    if sp["2s30s"] < 0.25:
        risks.append({"flag":"flat_long_end", "severity":"medium", "why":"2s30s < 25bp"})
    # belly hump: 5y materially above both 2y and 10y
    if z["5y"] > z["2y"] and z["5y"] > z["10y"] and (z["5y"] - max(z["2y"], z["10y"])) >= 0.30:
        risks.append({"flag":"belly_hump", "severity":"info", "why":"5y > 2y & 10y by ≥30bp"})
    return risks

def delta_map(m_today, m_prev, key):
    a, b = m_today[key], m_prev[key]
    out = {}
    for k in a.keys():
        out[k] = round(a[k]-b[k], 4)
    return out

def main():
    ap = argparse.ArgumentParser(description="Build as-of & prior-day UST curve snapshots for LLM.")
    ap.add_argument("--core-module", required=True,
                    help="Module path to curves (e.g., book_irds3.notebooks.curves OR tools.ust_curve.curves)")
    ap.add_argument("date", nargs="?", help="YYYY-MM-DD (defaults to today)")
    ap.add_argument("--lookback", type=int, default=30)
    args = ap.parse_args()

    # Import curves from the chosen module
    m = __import__(args.core_module, fromlist=["Curve","SolvedCurve","Swap","Dual"])
    Curve, SolvedCurve, Swap, Dual = m.Curve, m.SolvedCurve, m.Swap, m.Dual

    as_of = dt.date.today() if not args.date else dt.datetime.strptime(args.date, "%Y-%m-%d").date()

    # Fetch par for as_of (with lookback), and prior business date (as_of - 1)
    eff_today, par_today = rc.fetch_with_lookback(as_of, lookback_days=args.lookback)
    if not par_today:
        print(f"[ERROR] No par data for or before {as_of}."); sys.exit(1)

    prior_seed = eff_today - dt.timedelta(days=1)
    eff_prev, par_prev = rc.fetch_with_lookback(prior_seed, lookback_days=args.lookback)
    if not par_prev:
        print(f"[ERROR] No prior-day par data for or before {prior_seed}."); sys.exit(1)

    # Build quotes & solve both curves
    q_today = rc.par_map_to_months(par_today)
    q_prev  = rc.par_map_to_months(par_prev)

    as_of_dt_today = dt.datetime.combine(eff_today, dt.time())
    as_of_dt_prev  = dt.datetime.combine(eff_prev, dt.time())

    curve_today, pillars_today = rc.solve_curve(
        SolvedCurve, Dual, Swap, as_of_dt_today, q_today,
        fixed_leg_m=6, float_leg_m=3, interpolation="log_linear",
        algorithm="gauss_newton", flat_guess=0.04, months_for_nodes=None, verbose=False
    )
    curve_prev, pillars_prev = rc.solve_curve(
        SolvedCurve, Dual, Swap, as_of_dt_prev, q_prev,
        fixed_leg_m=6, float_leg_m=3, interpolation="log_linear",
        algorithm="gauss_newton", flat_guess=0.04, months_for_nodes=None, verbose=False
    )

    # Metrics & risks
    met_today = compute_metrics(pillars_today)
    met_prev  = compute_metrics(pillars_prev)
    risks_today = detect_risks(met_today)

    # Changes
    dz = delta_map(met_today, met_prev, "zeros_pct")
    dspread = delta_map(met_today, met_prev, "spreads_pct")

    payload = {
        "as_of": eff_today.isoformat(),
        "prev": eff_prev.isoformat(),
        "today": met_today,
        "prev_day": met_prev,
        "delta": {
            "zeros_pct": dz,
            "spreads_pct": dspread,
        },
        "risks": risks_today,
        "pillars_today": [{"tenor_years": t, "DF": DF, "zero_cc": z} for t,DF,z in pillars_today],
        "pillars_prev":  [{"tenor_years": t, "DF": DF, "zero_cc": z} for t,DF,z in pillars_prev],
        "source": "UST daily par (Treasury CSV), swap-style zero fit"
    }

    outdir = ROOT / "tools" / "ust_curve" / "llm" / "snapshots"
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"curve_snapshot_{eff_today.isoformat()}.json"
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[OK] Wrote {outpath}")

if __name__ == "__main__":
    main()
