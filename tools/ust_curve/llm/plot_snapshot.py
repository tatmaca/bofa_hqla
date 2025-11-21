#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
# Force a non-interactive backend so it always saves a PNG even on servers/CLI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SNAP_DIR = HERE / "snapshots"
PLOT_DIR = HERE / "plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

def load_snapshot(date_str: str):
    p = SNAP_DIR / f"curve_snapshot_{date_str}.json"
    with open(p, "r") as f:
        return json.load(f)

def _pair_series(d):
    # returns two parallel lists: tenor labels & values
    labels = ["6m","1y","2y","3y","5y","7y","10y","20y","30y"]
    vals = [d["zeros_pct"][k] for k in labels]
    return labels, vals

def plot_curve(date_str: str):
    data = load_snapshot(date_str)
    today_labels, today_vals = _pair_series(data["today"])
    prev_labels, prev_vals = _pair_series(data["prev_day"])

    # Sanity: same x-axis in both
    assert today_labels == prev_labels
    x = today_labels

    # 1) Curve levels (today vs prev)
    fig, ax = plt.subplots(figsize=(8,4.5))
    ax.plot(x, np.array(today_vals), marker="o", label=f"{data['as_of']}")
    ax.plot(x, np.array(prev_vals), marker="o", linestyle="--", label=f"{data['prev']}")
    ax.set_title(f"UST Zero Curve: {data['as_of']} vs {data['prev']}")
    ax.set_xlabel("Tenor")
    ax.set_ylabel("Zero Rate (%)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out1 = PLOT_DIR / f"ust_curve_{date_str}.png"
    fig.savefig(out1, dpi=150)
    plt.close(fig)

    # 2) Day-over-day delta by tenor
    d = data["delta"]["zeros_pct"]
    delta_vals = np.array([d[k] for k in x])
    fig, ax = plt.subplots(figsize=(8,4.5))
    ax.bar(x, delta_vals)
    ax.set_title(f"DoD Change in UST Zeros (%): {data['as_of']} vs {data['prev']}")
    ax.set_xlabel("Tenor")
    ax.set_ylabel("Δ Zero (%)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out2 = PLOT_DIR / f"ust_curve_delta_{date_str}.png"
    fig.savefig(out2, dpi=150)
    plt.close(fig)

    # 3) Key spreads today (optional small bar)
    s = data["today"]["spreads_pct"]
    sp_labels = list(s.keys())
    sp_vals = np.array([s[k] for k in sp_labels])
    fig, ax = plt.subplots(figsize=(6,4))
    ax.bar(sp_labels, sp_vals)
    ax.set_title(f"Key Spreads on {data['as_of']} (pct)")
    ax.set_ylabel("Spread (%)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out3 = PLOT_DIR / f"ust_spreads_{date_str}.png"
    fig.savefig(out3, dpi=150)
    plt.close(fig)

    print(f"[OK] Plots saved:\n - {out1}\n - {out2}\n - {out3}")

if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not date_arg:
        raise SystemExit("Usage: plot_snapshot.py YYYY-MM-DD")
    plot_curve(date_arg)
