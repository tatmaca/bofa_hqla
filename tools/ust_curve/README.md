# UST Zero Curve Builder & LLM Integration

This module builds, visualizes, and summarizes the **U.S. Treasury zero-coupon yield curve**.  
It supports **daily automation** and **LLM-ready analytics**, enabling models (and humans) to interpret curve shifts, steepening/flattening patterns, and risk signals.

---

## Directory Structure

```
tools/ust_curve/
├── bookirds/                # Core math and curve-fitting library
├── curves.py                # Core Curve, SolvedCurve, and Swap classes
├── run_curve.py             # Builds the curve for a specified date
├── llm/
│   ├── build_snapshots.py   # Builds today vs previous-day zero curve snapshot
│   ├── make_summary.py      # Generates summary files (Markdown + compact JSON)
│   ├── analyze_snapshot.py  # Prints curve interpretation to console
│   ├── plot_snapshot.py     # Creates yield/spread plots
│   ├── daily.sh             # End-to-end daily runner
│   ├── snapshots/           # JSON data outputs
│   ├── summaries/           # Markdown and JSON summaries
│   ├── plots/               # PNG plots
│   └── curve_daily_log.md   # Rolling text log of daily summaries
├── requirements.txt
└── README.md
```

---

## Environment Setup

From the repo root (`bofa_hqla`):

```bash
cd tools/ust_curve
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH="$(git rev-parse --show-toplevel)/tools/ust_curve:$(git rev-parse --show-toplevel):$PYTHONPATH"
```

---

## Build a Single-Day Curve

To build and visualize the curve for a given business day:

```bash
python tools/ust_curve/run_curve.py --core-module tools.ust_curve.curves 2025-10-30 --lookback 30
```

This will:
- Download official **U.S. Treasury par yield** data  
- Fit a smooth **zero-coupon yield curve**  
- Output files:

```
tools/ust_curve/ust_zero_curve_2025-10-30.csv
tools/ust_curve/ust_zero_curve_2025-10-30.json
tools/ust_curve/ust_zero_curve_2025-10-30.png
```

---

## Generate LLM Snapshots and Summaries

Run the full daily pipeline (curve build + LLM summary + plots):

```bash
./tools/ust_curve/llm/daily.sh 2025-10-30
```

The script performs:
1. Curve fitting (`build_snapshots.py`)
2. Summary creation (`make_summary.py`)
3. Plotting (`plot_snapshot.py`)
4. Log append (`curve_daily_log.md`)

You can re-run for past business days:
```bash
./tools/ust_curve/llm/daily.sh 2025-10-29
./tools/ust_curve/llm/daily.sh 2025-10-28
```

---

##  Outputs

### JSON Snapshot
`tools/ust_curve/llm/snapshots/curve_snapshot_<DATE>.json`
```json
{
  "as_of": "2025-10-30",
  "prev": "2025-10-29",
  "today": {"zeros_pct": {...}, "spreads_pct": {...}},
  "prev_day": {"zeros_pct": {...}, "spreads_pct": {...}},
  "delta": {"zeros_pct": {...}, "spreads_pct": {...}}
}
```

### Markdown Summary
`tools/ust_curve/llm/summaries/curve_summary_<DATE>.md`
```
**UST Yield Curve Summary — 2025-10-30 vs 2025-10-29**
- Largest yield increase: 20y (+0.06%) → Bear-steepening bias
- 2s10s spread = 0.543% (steepened by 1.1 bps)
- Average shift: +2.3 bps → Bearish tone
- Risks: Long-end duration volatility
```

### Plots
All saved to `tools/ust_curve/llm/plots/`:
- `ust_curve_<DATE>.png` → Today vs previous-day levels  
- `ust_curve_delta_<DATE>.png` → Day-over-day changes by tenor  
- `ust_spreads_<DATE>.png` → Spread curve (2s10s, 2s30s, 5s30s)

Open locally:
```bash
open tools/ust_curve/llm/plots/ust_curve_2025-10-30.png
```

---

## Analyze a Snapshot Manually

```bash
python tools/ust_curve/llm/analyze_snapshot.py   tools/ust_curve/llm/snapshots/curve_snapshot_2025-10-30.json
```

Console output:
```
**UST Yield Curve Summary — 2025-10-30 vs 2025-10-29**
- Largest yield increase: 20y (+0.06%) → Bear-steepening bias.
- 2s10s spread = 0.543% (steepened by 1.1 bps).
- Average shift: yields rose by 2.3 bps (bearish tone).
- Risks: Long-end duration volatility.
```

---

## Version Control

Ignored by Git:
```
tools/ust_curve/venv/
tools/ust_curve/llm/snapshots/
tools/ust_curve/llm/summaries/
tools/ust_curve/llm/plots/
tools/ust_curve/ust_zero_curve_*.*
```

Tracked scripts:
```
tools/ust_curve/curves.py
tools/ust_curve/run_curve.py
tools/ust_curve/llm/*.py
tools/ust_curve/llm/daily.sh
tools/ust_curve/README.md
```

Push updates:
```bash
git add tools/ust_curve/llm/curve_daily_log.md
git commit -m "Add yield curve snapshots and summaries for <DATE>"
git push
```

---

## Future Enhancements

- Automate daily curve updates via GitHub Actions  
- Extend summaries with **DV01, convexity, and curvature risk**  
- Add **LLM embeddings** for curve regime classification  
- Integrate macro event tags (Fed, CPI, auctions) for causal reasoning  

---

*Maintained by the Valuation & Risk Analytics Team — Bank of America Project Lab.*
