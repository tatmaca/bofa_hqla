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

## Issue 2: OpenMP Library Missing (macOS)

**Problem**: XGBoost requires OpenMP on macOS

**Solution**: Install OpenMP via Homebrew:
```bash
brew install libomp
```

Or use conda (handles OpenMP automatically):
```bash
conda install -c conda-forge xgboost
```

## Issue 3: No Training Data Collected

**Problem**: Need historical LLM predictions and yield curve snapshots

**Why**: The system needs:
- News articles bucketed for each date
- LLM predictions (not fallback) saved in `analyses/`
- Yield curve snapshots in `ust_curve/llm/snapshots/`

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

## Issue 4: Rolling 30-Day Updates

The system now automatically uses a rolling 30-day window:

- **Daily pipeline** automatically updates models using last 30 days
- **Manual update**: `python3 update_models_rolling.py --days 30`
- Models are retrained daily with most recent 30 days of data
- Older data is automatically excluded (rolling window)

## Complete Setup & Test

```bash
# 1. Fix dependencies
python3 fix_dependencies.py

# 2. Install OpenMP (macOS only)
brew install libomp  # if needed

# 3. Verify imports
python3 -c "import numpy, xgboost; print('✓ OK')"

# 4. Generate historical data (run for past dates)
for date in 2025-10-29 2025-10-30 2025-10-31 2025-11-03; do
    python3 daily_pipeline.py --date $date
done

# 5. Test data collection
python3 collect_training_data.py --start-date 2025-10-29 --end-date 2025-11-06

# 6. Test rolling update
python3 update_models_rolling.py --days 30
```

## Notes

- **Rolling window**: Models use only the most recent 30 days, automatically excluding older data
- **Daily updates**: Each day, models are retrained on the latest 30-day window
- **Minimum data**: Need at least 7 days of complete data (news + LLM + snapshots)

