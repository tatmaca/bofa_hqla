# XGBoost-Based Prediction Improvement System

This system improves the accuracy of news-to-yield-curve predictions by training XGBoost models on historical LLM predictions and actual yield curve movements.

## Overview

The system implements a feedback loop:
1. **Collect** historical LLM predictions and actual yield changes
2. **Train** XGBoost models to learn patterns from historical data
3. **Evaluate** model accuracy against a threshold (default: 3 bps MAE)
4. **Enhance** future predictions using trained models
5. **Iterate** until accuracy threshold is met

## Quick Start

### 1. Install Dependencies

```bash
cd tools/news_ingestion
pip install xgboost>=2.0.0
```

### 2. Collect Historical Training Data

First, ensure you have:
- Historical news analyses (from `analyze_yield_impact.py`)
- Historical yield curve snapshots (from `ust_curve/llm/build_snapshots.py`)

Then collect training data:

```bash
# Collect data for past 30 days
python3 collect_training_data.py --start-date 2025-10-07 --end-date 2025-11-06
```

This creates `training_data_historical.json` with:
- News bucket features (counts, weights)
- LLM prediction features (magnitude, direction, signed values)
- Actual yield changes (ground truth)

### 3. Train XGBoost Models

```bash
# Train models with default threshold (3 bps MAE)
python3 train_xgboost.py --data training_data_historical.json --threshold-mae 3.0

# Or with custom threshold
python3 train_xgboost.py --data training_data_historical.json --threshold-mae 2.5
```

The script will:
- Split data using time series split (respects temporal order)
- Train XGBoost models for each tenor/spread
- Evaluate accuracy metrics (R², MAE, RMSE)
- Check if threshold is met
- Save models and metadata

### 4. Use Complete Training Pipeline

For automated end-to-end training:

```bash
# Run complete pipeline (collects data, trains, evaluates)
python3 training_pipeline.py --start-date 2025-10-07 --end-date 2025-11-06 --threshold-mae 3.0

# With multiple iterations
python3 training_pipeline.py --start-date 2025-10-07 --threshold-mae 3.0 --max-iterations 5
```

### 5. Enhance Predictions

Use trained models to improve predictions:

```bash
# Get enhanced prediction for today
python3 enhance_predictions.py

# For specific date
python3 enhance_predictions.py --date 2025-11-07

# Use saved LLM prediction (don't call LLM)
python3 enhance_predictions.py --date 2025-11-07 --no-llm
```

## Components

### `collect_training_data.py`
- Collects historical LLM predictions from `analyses/` directory
- Gets actual yield changes from `ust_curve/llm/snapshots/`
- Extracts features: news buckets + LLM predictions
- Creates training examples: features → actual changes

### `train_xgboost.py`
- Trains XGBoost regression models for each tenor/spread
- Uses time series split (no data leakage)
- Evaluates accuracy metrics
- Checks against threshold
- Saves models and feature importance

### `enhance_predictions.py`
- Loads trained XGBoost models
- Enhances LLM predictions with model outputs
- Combines news features + LLM features → model prediction

### `training_pipeline.py`
- Orchestrates complete workflow
- Builds historical snapshots if needed
- Iterative training until threshold met
- Saves best models

## Model Features

Each training example includes:

**News Bucket Features (16 features):**
- Count and weight for each of 8 buckets

**LLM Prediction Features (18 features):**
- Magnitude, direction, and signed magnitude for:
  - 4 tenors (2y, 5y, 10y, 30y)
  - 2 spreads (2s10s, 2s30s)

**Total: 34 features per example**

## Accuracy Metrics

Models are evaluated on:
- **R² Score**: Explained variance (higher is better)
- **MAE (Mean Absolute Error)**: Average error in basis points
- **RMSE (Root Mean Squared Error)**: Penalizes large errors more

Default threshold: **3 bps MAE** (all targets must meet threshold)

## Model Outputs

Trained models are saved to `models/`:
- `xgb_{target}_{date}.pkl`: Trained model for each target
- `xgb_metadata_{date}.json`: Model metadata and metrics
- `evaluation_{date}.json`: Accuracy evaluation results

## Integration with Daily Pipeline

To integrate into daily workflow, modify `daily_pipeline.py`:

```python
# After LLM analysis, enhance with XGBoost
from enhance_predictions import enhance_prediction
enhanced = enhance_prediction(analysis, date)
```

## Example Workflow

```bash
# 1. Ensure you have historical data
# (Run daily pipeline for past few weeks to generate analyses)

# 2. Collect training data
python3 collect_training_data.py --start-date 2025-10-07 --end-date 2025-11-06

# 3. Train models
python3 train_xgboost.py --data training_data_2025-10-07_2025-11-06.json

# 4. Check evaluation
cat models/evaluation_2025-11-07.json

# 5. Use enhanced predictions
python3 enhance_predictions.py --date 2025-11-07
```

## Tips

1. **More data = better models**: Collect at least 2-4 weeks of data
2. **Time series split**: Always use time series split (default) to avoid lookahead bias
3. **Threshold tuning**: Adjust threshold based on your accuracy needs
4. **Feature importance**: Check `xgb_metadata_*.json` to see which features matter most
5. **Iterative improvement**: Run pipeline multiple times as more data accumulates

## Troubleshooting

**"Insufficient training data"**
- Need at least 7 days of aligned news + yield curve data
- Run daily pipeline to generate more analyses

**"No yield curve snapshot found"**
- Build snapshots: `cd ../ust_curve/llm && python3 build_snapshots.py --core-module tools.ust_curve.curves YYYY-MM-DD`

**"Models don't meet threshold"**
- Collect more training data
- Lower threshold (e.g., 4 bps instead of 3 bps)
- Check feature importance to understand what drives predictions

