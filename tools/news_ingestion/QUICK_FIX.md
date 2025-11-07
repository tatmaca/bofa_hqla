# Quick Fix Guide

## Issue 1: NumPy/XGBoost Compatibility

**Problem**: NumPy 2.x is incompatible with XGBoost/scipy

**Solution**: Run the fix script:
```bash
cd tools/news_ingestion
python3 fix_dependencies.py
```

Or manually:
```bash
pip install "numpy>=1.24.0,<2.0.0" --upgrade
pip install xgboost --upgrade
```

## Issue 2: No Training Data Collected

**Problem**: Need historical LLM predictions and yield curve snapshots

**Solution**: 
1. Run daily pipeline for past dates to generate analyses:
```bash
# For each date in the past
python3 daily_pipeline.py --date 2025-10-29
python3 daily_pipeline.py --date 2025-10-30
# ... etc
```

2. Or build yield curve snapshots manually:
```bash
cd ../ust_curve/llm
python3 build_snapshots.py --core-module tools.ust_curve.curves 2025-10-29
```

3. Then collect training data:
```bash
cd ../../news_ingestion
python3 collect_training_data.py --start-date 2025-10-29 --end-date 2025-11-06
```

## Issue 3: Rolling 30-Day Updates

The system now automatically uses a rolling 30-day window:

- **Daily pipeline** automatically updates models using last 30 days
- **Manual update**: `python3 update_models_rolling.py --days 30`
- Models are retrained daily with most recent 30 days of data

## Testing After Fix

```bash
# 1. Fix dependencies
python3 fix_dependencies.py

# 2. Verify imports
python3 -c "import numpy, xgboost; print('OK')"

# 3. Test data collection (if you have historical data)
python3 collect_training_data.py --start-date 2025-10-29 --end-date 2025-11-06

# 4. Test rolling update
python3 update_models_rolling.py --days 30
```

