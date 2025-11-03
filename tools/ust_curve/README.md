# UST Zero Curve Runner (vendored)

## Quick start
python -m pip install -r tools/ust_curve/requirements.txt
python tools/ust_curve/run_curve.py --core-module tools.ust_curve.curves 2025-10-30 --lookback 30

## Outputs (ignored by git)
- tools/ust_curve/ust_zero_curve_<date>.csv
- tools/ust_curve/ust_zero_curve_<date>.json
- tools/ust_curve/ust_zero_curve_<date>.png
