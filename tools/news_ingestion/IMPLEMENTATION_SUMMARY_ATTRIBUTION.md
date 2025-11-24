# Attribution Analysis Implementation Summary

## Overview

This implementation addresses the feedback about:
1. Finding evidence on which factors push more in YC changes (attribution analysis)
2. SHAP analysis for nonlinear models to understand feature importance
3. Connecting the two steps (linear model and XGBoost)

## What Was Implemented

### 1. Linear Model Attribution Analysis ✅

**File:** `train_linear_online.py`

**New Functions:**
- `compute_factor_attribution(date, coefficients, factor_scores)`: Computes per-factor contributions
  - Formula: `Contribution_f,k = B_k,f × x_t,f` (coefficient × factor score)
  - Returns factors ranked by absolute contribution per tenor
- `get_top_factors_by_tenor(attribution, top_n)`: Gets top N factors by contribution

**Usage:**
```python
from train_linear_online import compute_factor_attribution

attribution = compute_factor_attribution("2025-11-17")
# Returns: {tenor: {factor_name: contribution_bps}} sorted by absolute value
```

**What it answers:**
- "Which factors really push more in the YC change that day?"
- Attribution from the factor side (coefficient × factor score)

### 2. SHAP Integration for XGBoost ✅

**File:** `train_xgboost.py`

**New Functions:**
- `compute_shap_values(model, X_sample, feature_names)`: Computes SHAP values
- Automatically integrated into training pipeline
- SHAP values saved to `models/xgb_{target}_{date}_shap.json`

**What it answers:**
- "Which features are more important in the nonlinear model?"
- Feature importance ranking with direction and magnitude

**Output:**
- Top features ranked by mean absolute SHAP value
- Saved during model training
- Available in model metadata

### 3. Model Connection ✅

**Files Modified:**
- `collect_training_data.py`: Adds factor scores as features
- `enhance_predictions.py`: Includes factor scores in prediction features

**Connection Mechanism:**
- Factor scores from linear model are included as features in XGBoost
- Features named `factor_{FACTOR_NAME}` (e.g., `factor_FED_TONE`)
- Creates direct connection: linear model factors → XGBoost features

**What it answers:**
- "The two steps should have connections"
- Factor scores bridge the linear and nonlinear models

### 4. Visualization Functions ✅

**File:** `visualize_attribution.py`

**Visualizations Created:**

1. **Factor Attribution by Tenor** (`plot_factor_attribution_by_tenor`)
   - Bar charts showing top factors per tenor
   - Color-coded (green = positive, red = negative)
   - Shows which factors push yields up vs down

2. **Factor Contribution Heatmap** (`plot_factor_contribution_heatmap`)
   - Heatmap: factors (rows) × tenors (columns)
   - Shows which factors affect which parts of the curve
   - Easy to spot patterns (front-end vs long-end)

3. **SHAP Summary Plot** (`plot_shap_summary`)
   - Bar chart of mean absolute SHAP values
   - Shows top features by importance
   - Includes factor features alongside other features

4. **Linear vs SHAP Comparison** (`compare_linear_shap_importance`)
   - Side-by-side comparison
   - Shows alignment between models
   - Identifies factors important in both

**Usage:**
```bash
python visualize_attribution.py --date 2025-11-17
```

**Output:**
- `attribution_analysis/factor_attribution_{date}.png`
- `attribution_analysis/factor_heatmap_{date}.png`
- `attribution_analysis/attribution_report_{date}.json`

### 5. Model Comparison Analysis ✅

**File:** `compare_models.py`

**Functions:**
- `compare_all_tenors(date)`: Compares linear and SHAP for all tenors
- `compute_alignment_metrics()`: Computes correlation and overlap
- `generate_comparison_report()`: Creates comprehensive report

**Metrics:**
- **Correlation**: Pearson correlation between coefficients and SHAP
- **Rank Correlation**: Spearman correlation
- **Top-10 Overlap**: How many top-10 factors overlap
- **Alignment Score**: Weighted combination (0-1 scale)

**Usage:**
```bash
python compare_models.py --date 2025-11-17
```

**Output:**
- `attribution_analysis/model_comparison_{date}.json`
- Console summary with alignment metrics

## Files Created/Modified

### New Files:
1. `visualize_attribution.py` - Visualization functions
2. `compare_models.py` - Model comparison analysis
3. `ATTRIBUTION_ANALYSIS.md` - Documentation
4. `IMPLEMENTATION_SUMMARY_ATTRIBUTION.md` - This file

### Modified Files:
1. `train_linear_online.py` - Added attribution functions
2. `train_xgboost.py` - Added SHAP integration
3. `collect_training_data.py` - Added factor scores as features
4. `enhance_predictions.py` - Added factor scores to predictions

## Key Features

### 1. Attribution Analysis
- **Linear Model**: Shows which factors contribute most to yield changes
- **Ranking**: Factors sorted by absolute contribution per tenor
- **Visualization**: Bar charts and heatmaps

### 2. SHAP Analysis
- **Automatic**: Computed during XGBoost training
- **Feature Importance**: Shows which features matter most
- **Factor Features**: Includes factor scores in analysis

### 3. Model Connection
- **Factor Scores as Features**: Linear model output → XGBoost input
- **Comparison**: Aligns linear coefficients with SHAP importance
- **Alignment Metrics**: Quantifies agreement between models

### 4. Visualizations
- **Factor Attribution Charts**: Per-tenor bar charts
- **Heatmaps**: Cross-tenor factor impact
- **SHAP Plots**: Feature importance rankings
- **Comparison Charts**: Side-by-side model comparison

## Example Workflow

```python
# 1. Get attribution for a date
from train_linear_online import compute_factor_attribution, get_top_factors_by_tenor

attribution = compute_factor_attribution("2025-11-17")
top_factors = get_top_factors_by_tenor(attribution, top_n=5)

print("Top 5 factors for 10Y:")
for factor, contrib in top_factors["10Y"]:
    print(f"  {factor}: {contrib:.2f} bps")

# 2. Generate visualizations
from visualize_attribution import generate_attribution_report

report = generate_attribution_report("2025-11-17")
print(f"Visualizations: {report['visualizations']}")

# 3. Compare models
from compare_models import generate_comparison_report

comparison = generate_comparison_report("2025-11-17")
print(f"Alignment score: {comparison['mean_alignment_score']:.3f}")
```

## Dependencies

```bash
# Required
pip install matplotlib numpy

# Optional but recommended
pip install seaborn shap scipy
```

## Output Structure

```
tools/news_ingestion/
├── attribution_analysis/
│   ├── factor_attribution_{date}.png
│   ├── factor_heatmap_{date}.png
│   ├── attribution_report_{date}.json
│   └── model_comparison_{date}.json
├── models/
│   ├── xgb_{target}_{date}.pkl
│   └── xgb_{target}_{date}_shap.json
└── [implementation files]
```

## Questions Answered

✅ **"Which factors really push more in the YC change that day?"**
→ `compute_factor_attribution()` ranks factors by contribution

✅ **"Attribution from the factor side"**
→ Linear coefficients × factor scores = contribution per factor

✅ **"SHAP analysis for nonlinear models"**
→ Integrated into XGBoost training, shows feature importance

✅ **"Which feature is more important"**
→ SHAP ranking shows top features, including factor features

✅ **"The two steps should have connections"**
→ Factor scores are features in XGBoost; comparison shows alignment

## Next Steps

1. **Run Analysis**: Generate attribution reports for recent dates
2. **Review Visualizations**: Check factor rankings and heatmaps
3. **Compare Models**: Run comparison analysis to see alignment
4. **Iterate**: Use insights to refine factor extraction or model training

## Notes

- SHAP computation may be slow for large datasets (limited to 100 samples by default)
- Visualizations require matplotlib (and optionally seaborn)
- Comparison analysis requires scipy for rank correlation
- All functions handle missing data gracefully

