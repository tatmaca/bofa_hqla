#!/usr/bin/env python3
import json
from pathlib import Path
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
    plt.figure(figsize=(8,4.5))
    plt.plot(x, today_vals, marker="o", label=f"{data['as_of']}")
    plt.plot(x, prev_vals, marker="o", linestyle="--", label=f"{data['prev']}")
    plt.title(f"UST Zero Curve: {data['as_of']} vs {data['prev']}")
    plt.xlabel("Tenor")
    plt.ylabel("Zero Rate (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out1 = PLOT_DIR / f"ust_curve_{date_str}.png"
    plt.savefig(out1, dpi=150)
    plt.close()

    # 2) Day-over-day delta by tenor
    d = data["delta"]["zeros_pct"]
    delta_vals = [d[k] for k in x]
    plt.figure(figsize=(8,4.5))
    plt.bar(x, delta_vals)
    plt.title(f"DoD Change in UST Zeros (%): {data['as_of']} vs {data['prev']}")
    plt.xlabel("Tenor")
    plt.ylabel("Δ Zero (%)")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out2 = PLOT_DIR / f"ust_curve_delta_{date_str}.png"
    plt.savefig(out2, dpi=150)
    plt.close()

    # 3) Key spreads today (optional small bar)
    s = data["today"]["spreads_pct"]
    sp_labels = list(s.keys())
    sp_vals = [s[k] for k in sp_labels]
    plt.figure(figsize=(6,4))
    plt.bar(sp_labels, sp_vals)
    plt.title(f"Key Spreads on {data['as_of']} (pct)")
    plt.ylabel("Spread (%)")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    out3 = PLOT_DIR / f"ust_spreads_{date_str}.png"
    plt.savefig(out3, dpi=150)
    plt.close()

    print(f"[OK] Plots saved:\n - {out1}\n - {out2}\n - {out3}")

if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not date_arg:
        raise SystemExit("Usage: plot_snapshot.py YYYY-MM-DD")
    plot_curve(date_arg)
