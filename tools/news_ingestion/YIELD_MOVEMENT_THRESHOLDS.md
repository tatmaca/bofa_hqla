# Yield Movement Thresholds

## Overview

This module implements statistical thresholds to identify **significant yield curve movements** and filter out noise/mean-reverting movements. This is critical for:

1. **Model Training**: Only train on significant moves (>2σ) to avoid learning noise
2. **Monitoring**: Focus alerts on meaningful market events
3. **Analysis**: Concentrate analysis on days with substantial yield changes

## How It Works

### Statistical Threshold

Uses a **rolling window** (default: 60 days) to calculate:
- **Mean** of daily yield changes
- **Standard deviation** of daily yield changes
- **Threshold** = mean ± (threshold_std × std)

A move is considered **significant** if it deviates from the mean by more than `threshold_std` standard deviations.

**Default**: `threshold_std = 2.0` (captures ~95% of significant moves)

### Fallback Threshold

When insufficient historical data exists (< 20 days), uses an **absolute threshold**:
- **Default**: 5 bps
- Any move ≥ 5 bps is considered significant

## Configuration

In `news_config.yaml`:

```yaml
yield_movement_thresholds:
  threshold_std: 2.0              # Standard deviation threshold
  absolute_threshold_bps: 5.0     # Fallback absolute threshold
  rolling_window_days: 60         # Rolling window for statistics
  min_samples: 20                 # Minimum samples required
  filter_training: true           # Enable filtering for training
  min_significant_tenors: 1       # Min tenors with significant moves
```

## Usage

### Check Significance for a Date

```bash
python3 yield_movement_thresholds.py --date 2025-11-06 --threshold-std 2.0
```

### Filter Training Dates

```bash
python3 yield_movement_thresholds.py --start-date 2025-09-26 --end-date 2025-11-19 --filter-training --threshold-std 2.0
```

### Train with Significance Filter

```bash
# Retrospective training (only significant moves)
python3 train_linear_retrospective.py --threshold-std 2.0

# Train on all dates (disable filter)
python3 train_linear_retrospective.py --no-significance-filter
```

## Integration

### Daily Pipeline

The daily pipeline automatically uses significance filtering:
- **Step 5**: Linear model only trains on significant moves
- Skips dates with no significant moves (logs as `[SKIP]`)

### Retrospective Training

The retrospective training script filters dates by significance:
- Calculates statistics from available historical data
- Only trains on dates with ≥1 significant tenor
- Reports how many dates were filtered out

## Example Output

```
Significant Moves for 2025-11-06 (threshold: 2.0σ):
======================================================================
2Y: -5.91 bps 
5Y: -6.92 bps ***
10Y: -5.74 bps 
30Y: -4.77 bps 

Significant tenors: 5Y

[INFO] Mean: -0.5, Std: 3.2, Threshold: ±6.4 bps
```

## Benefits

1. **Better Model Training**: Models learn from meaningful moves, not noise
2. **Reduced Overfitting**: Avoids fitting to random fluctuations
3. **Focused Analysis**: Concentrates on days with substantial market impact
4. **Efficient Training**: Skips dates with no significant moves

## Statistics Calculation

- Uses **rolling window** (default: 60 days) for adaptive thresholds
- Calculates per-tenor statistics (3M, 2Y, 5Y, 10Y, 30Y)
- Updates automatically as new data arrives
- Handles missing data gracefully

## Future Enhancements

- Per-tenor threshold customization
- Volatility-adjusted thresholds (higher threshold in volatile periods)
- Spread-based significance (2s10s, 2s30s)
- Alert system for significant moves

