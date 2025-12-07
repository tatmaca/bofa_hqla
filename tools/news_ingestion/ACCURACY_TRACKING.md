# Prediction Accuracy Tracking System

## Overview

The accuracy tracking system measures and visualizes prediction accuracy for all yield curve predictions (baseline + 9 scenarios) over time. This enables monitoring of model improvement and identification of best-performing scenarios.

## Features

- **Comprehensive Metrics**: MAE, RMSE, R², directional accuracy, Pearson correlation
- **Multi-Scenario Tracking**: Tracks accuracy for baseline and all 9 scenarios
- **Time Series Analysis**: Visualize accuracy trends over time
- **Per-Tenor Analysis**: Identify which tenors are predicted most accurately
- **Automated Reporting**: Integrated into daily pipeline

## Quick Start

### Calculate Accuracy for a Date

```bash
python3 calculate_prediction_accuracy.py --date 2025-12-04
```

### Batch Calculate Accuracy

```bash
python3 batch_calculate_accuracy.py --start-date 2025-11-06 --end-date 2025-12-04
```

### Generate Accuracy Report

```bash
python3 generate_accuracy_report.py --start-date 2025-11-06 --end-date 2025-12-04
```

This generates:
- Markdown report: `accuracy_analysis/accuracy_report_{start}_{end}.md`
- JSON data: `accuracy_analysis/accuracy_report_{start}_{end}.json`
- Visualizations: Multiple PNG files in `accuracy_analysis/`

## Metrics Explained

### MAE (Mean Absolute Error)
Average absolute difference between predicted and actual yield changes across all tenors.
- Lower is better
- Units: basis points (bps)

### RMSE (Root Mean Squared Error)
Square root of average squared errors. Penalizes larger errors more than MAE.
- Lower is better
- Units: basis points (bps)

### R² (Coefficient of Determination)
Proportion of variance in actual changes explained by predictions.
- Range: -∞ to 1.0
- 1.0 = perfect prediction
- 0.0 = predictions no better than mean
- Negative = predictions worse than mean

### Directional Accuracy
Percentage of tenors where prediction direction (up/down) matches actual direction.
- Range: 0% to 100%
- Higher is better
- 50% = random guessing

### Correlation
Pearson correlation coefficient between predicted and actual changes.
- Range: -1.0 to 1.0
- 1.0 = perfect positive correlation
- 0.0 = no correlation
- -1.0 = perfect negative correlation

## Database Schema

Accuracy data is stored in two tables:

### `scenario_prediction_accuracy`
Per-tenor accuracy data:
- `date`: Prediction date (when prediction was made)
- `actual_date`: Actual yield change date (prediction_date)
- `scenario_name`: 'baseline' or scenario name
- `tenor`: Tenor (1M, 3M, 6M, etc.)
- `predicted_delta_bps`: Predicted yield change
- `actual_delta_bps`: Actual yield change
- `error_bps`: actual - predicted

### `daily_accuracy_summary`
Aggregated metrics per date and scenario:
- `date`: Prediction date
- `actual_date`: Actual yield change date
- `scenario_name`: Scenario name
- `mae_bps`: Mean Absolute Error
- `rmse_bps`: Root Mean Squared Error
- `r2`: R-squared
- `directional_accuracy`: Directional accuracy percentage
- `correlation`: Pearson correlation

## Visualizations

### Time Series Plots
Show accuracy metrics over time for all scenarios:
- `accuracy_over_time_mae_bps_{start}_{end}.png`
- `accuracy_over_time_rmse_bps_{start}_{end}.png`
- `accuracy_over_time_r2_{start}_{end}.png`
- `accuracy_over_time_directional_accuracy_{start}_{end}.png`

### Heatmap
Shows accuracy by scenario and date:
- `accuracy_heatmap_mae_bps_{start}_{end}.png`

### Per-Tenor Comparison
Shows which tenors are predicted most accurately:
- `tenor_accuracy_mae_bps_{start}_{end}.png`

### Error Distribution
Histogram of prediction errors:
- `error_distribution_all_{start}_{end}.png`

### Dashboard
Comprehensive multi-panel dashboard:
- `accuracy_dashboard_{start}_{end}.png`

## Daily Pipeline Integration

Accuracy calculation is automatically integrated into the daily pipeline (Step 10):
- Calculates accuracy for previous day's predictions
- Only runs when actual yield data is available
- Saves results to database

## Files

### Core Modules
- `calculate_prediction_accuracy.py`: Core accuracy calculation functions
- `batch_calculate_accuracy.py`: Batch processing for date ranges
- `visualize_accuracy.py`: Visualization generation
- `generate_accuracy_report.py`: Report generation

### Database
- `schema_accuracy.sql`: Database schema for accuracy tracking

### Documentation
- `ACCURACY_TRACKING.md`: This file
- `accuracy_analysis/accuracy_report_*.md`: Generated reports

## Usage Examples

### Check Accuracy for Specific Scenario

```python
from calculate_prediction_accuracy import load_accuracy_history

history = load_accuracy_history("2025-11-06", "2025-12-04", scenario_name="baseline")
for record in history:
    print(f"{record['date']}: MAE={record['mae_bps']:.2f} bps, R²={record['r2']:.3f}")
```

### Generate Custom Visualization

```python
from visualize_accuracy import plot_accuracy_over_time

plot_accuracy_over_time(
    "2025-11-06",
    "2025-12-04",
    metric="mae_bps",
    scenarios=["baseline", "Stable Economic Conditions"]
)
```

## Best Practices

1. **Regular Monitoring**: Generate reports weekly to track trends
2. **Scenario Comparison**: Compare baseline vs. scenarios to identify best performers
3. **Tenor Analysis**: Review per-tenor accuracy to identify weak points
4. **Historical Analysis**: Use batch processing to analyze long-term trends

## Troubleshooting

### No Accuracy Data
- Ensure scenario curves have been generated for the dates
- Check that actual yield data is available for prediction_date
- Run `batch_calculate_accuracy.py` to backfill missing data

### Missing Visualizations
- Ensure matplotlib and seaborn are installed
- Check that accuracy data exists in database
- Verify date ranges are correct

### Negative R² Values
- This indicates predictions are worse than using the mean
- Common early in training when model hasn't converged
- Should improve as more training data is collected

