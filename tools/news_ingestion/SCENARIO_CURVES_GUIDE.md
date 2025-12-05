# Scenario-Based Yield Curve Predictions Guide

## Overview

This system generates 10 yield curve predictions per day:
- **1 baseline curve**: Predicted from day t's news using linear attribution (t+1 prediction)
- **9 scenario curves**: Each scenario treated as major news that will definitely happen the next day

## Quick Start

### Generate Scenario Curves

```bash
cd tools/news_ingestion

# Generate for today
python3 generate_scenario_curves.py

# Generate for specific date
python3 generate_scenario_curves.py --date 2025-12-01

# Specify custom scenarios file
python3 generate_scenario_curves.py --date 2025-12-01 --scenarios-path /path/to/scenarios.jsonl
```

### Output Location

By default, output is saved to:
```
tools/news_ingestion/scenario_predictions/scenario_curves_{date}.json
```

## Output Format

The output JSON has the following structure:

```json
{
  "date": "2025-12-01",
  "base_date": "2025-12-01",
  "prediction_date": "2025-12-02",
  "baseline": {
    "scenario_name": "baseline",
    "scenario_description": "Prediction from 2025-12-01's news",
    "predictions": {
      "3M": 1.2,
      "2Y": 2.5,
      "5Y": 3.1,
      "10Y": 4.0,
      "30Y": 5.2
    },
    "factor_scores": {...},
    "attribution": {...}
  },
  "Mild Rate Hike Surprise": {
    "scenario_name": "Mild Rate Hike Surprise",
    "scenario_description": "Unexpected 25 bps rate hike...",
    "predictions": {
      "3M": 2.5,
      "2Y": 5.0,
      "5Y": 4.5,
      "10Y": 4.2,
      "30Y": 3.8
    },
    "factor_scores": {...},
    "attribution": {...}
  },
  ... (8 more scenarios)
}
```

### Fields

- **date**: Date of news used for baseline (day t)
- **base_date**: Same as date (for clarity)
- **prediction_date**: Target date for predictions (t+1)
- **baseline**: Baseline prediction from day's news
- **{scenario_name}**: One key for each of the 9 scenarios

Each curve contains:
- **scenario_name**: Name of scenario (or "baseline")
- **scenario_description**: Description of scenario
- **predictions**: Yield change predictions in bps for all tenors (3M, 2Y, 5Y, 10Y, 30Y)
- **factor_scores**: Factor scores used for prediction
- **attribution**: Factor attribution breakdown per tenor

## How It Works

### 1. Baseline Prediction

- Uses factor scores from day t's news articles
- Applies linear model: `Δy = Σ(coefficient × factor_score) + intercept`
- Generates predictions for t+1

### 2. Scenario Predictions

For each of the 9 scenarios:
1. **Extract factors**: Use LLM to extract economic factors from scenario description
2. **Generate prediction**: Apply linear model using scenario factors (treating scenario as major news)
3. **Compute attribution**: Calculate factor contributions per tenor

**Note**: By default, scenario factors **replace** day's news factors (scenario-only prediction). Use `--combine-with-news` to add scenario factors to day's news.

### 3. Factor Extraction

Scenarios are analyzed using GPT-4o to extract:
- **Factor names**: From the 20+ economic factors (FED_TONE, CPI_HEAD_SURP, etc.)
- **Intensity**: -2.0 to +2.0 (direction and strength)
- **Confidence**: 0.0 to 1.0 (certainty factor is present)

Factors are aggregated using: `factor_score = sum(confidence × intensity)` clipped to [-2.5, +2.5]

### 4. Caching

Scenario factors are cached in `scenario_factors_cache.json` since scenarios don't change daily. This avoids re-extracting factors on every run.

## Integration with Daily Pipeline

The scenario curve generation is integrated as **Step 9** in the daily pipeline:

```python
# Step 9: Generate Scenario-Based Predictions (optional)
```

It runs automatically if:
- Scenarios file exists at: `backend/mad_debate/data/scenarios/out.jsonl`
- All dependencies are available

## Command-Line Options

```bash
python3 generate_scenario_curves.py [OPTIONS]

Options:
  --date DATE              Date (YYYY-MM-DD) whose news is used for baseline
  --scenarios-path PATH    Path to scenarios JSONL file
  --output-path PATH       Output JSON file path
  --combine-with-news      Combine scenario factors with day's news factors
  --no-cache               Don't use cached scenario factors
```

## Scenarios File Format

The scenarios file should be a JSONL file (one JSON object per line) with the following structure:

```json
{
  "Scenario": "Scenario Name",
  "Description": "Detailed description of the scenario...",
  "Probability": 0.4,
  "Rationale": "...",
  "ImpactChannels": [...],
  "Shocks": {...},
  ...
}
```

**Required fields**:
- `Scenario`: Scenario name (used as key in output)
- `Description`: Scenario description (used for factor extraction)

## Example Usage

### Generate for Today

```bash
python3 generate_scenario_curves.py
```

### Generate for Historical Date

```bash
python3 generate_scenario_curves.py --date 2025-11-28
```

### Use Custom Scenarios File

```bash
python3 generate_scenario_curves.py \
  --date 2025-12-01 \
  --scenarios-path /path/to/custom_scenarios.jsonl \
  --output-path /path/to/output.json
```

### Combine Scenario with News

```bash
python3 generate_scenario_curves.py \
  --date 2025-12-01 \
  --combine-with-news
```

This adds scenario factors to the day's news factors (instead of replacing them).

## Accessing Results

### From Python

```python
import json
from pathlib import Path

# Load scenario curves
curves_path = Path("scenario_predictions/scenario_curves_2025-12-01.json")
with open(curves_path) as f:
    curves = json.load(f)

# Get baseline prediction
baseline = curves["baseline"]
baseline_preds = baseline["predictions"]
print(f"Baseline 10Y prediction: {baseline_preds['10Y']} bps")

# Get scenario prediction
scenario = curves["Mild Rate Hike Surprise"]
scenario_preds = scenario["predictions"]
print(f"Scenario 10Y prediction: {scenario_preds['10Y']} bps")
```

### From Other Components

The JSON file can be read by any component that needs scenario-based yield curve predictions. The format is standardized and includes all necessary information:
- Predictions for all tenors
- Factor scores used
- Attribution breakdown

## Troubleshooting

### Scenarios File Not Found

**Error**: `[ERROR] Scenarios file not found`

**Solution**: 
- Check if file exists at: `backend/mad_debate/data/scenarios/out.jsonl`
- Or provide path with `--scenarios-path`

### No Factor Scores for Baseline

**Warning**: `[WARN] No factor scores for {date}`

**Solution**: 
- Ensure factor extraction has run for that date
- Run: `python3 extract_factors.py --date {date}`

### Scenario Factor Extraction Fails

**Warning**: `[WARN] No factors extracted for scenario: {name}`

**Solution**:
- Check OpenAI API key is set
- Scenario may not map to any economic factors
- Check scenario description is clear

### Cache Issues

If scenario factors seem incorrect:
```bash
# Re-extract factors (ignore cache)
python3 generate_scenario_curves.py --date 2025-12-01 --no-cache
```

## Files

- **load_scenarios.py**: Load scenarios from JSONL file
- **extract_scenario_factors.py**: Extract factors from scenario descriptions
- **generate_scenario_predictions.py**: Generate predictions for baseline and scenarios
- **generate_scenario_curves.py**: Main script with CLI
- **scenario_factors_cache.json**: Cached scenario factors (auto-generated)
- **scenario_predictions/**: Output directory (auto-created)

## Dependencies

- OpenAI API key (for factor extraction)
- Existing linear model coefficients (from daily training)
- Scenarios JSONL file

## Notes

- Scenario factors are cached since scenarios don't change daily
- Baseline uses day t's news to predict t+1
- Scenarios are treated as major news events (high intensity factors)
- All predictions use the same linear model coefficients and intercepts
- Output format is designed for easy integration with other components

---

*Last Updated: 2025-12-01*

