# Attribution Analysis and Model Comparison

This document describes the attribution analysis features that connect the linear model and XGBoost models, addressing the feedback about understanding which factors drive yield curve changes and how the two models relate.

## Overview

The pipeline now includes:

1. **Linear Model Attribution**: Identifies which factors contribute most to yield changes on a given day
2. **SHAP Analysis for XGBoost**: Explains which features are most important in the nonlinear model
3. **Model Connection**: Factor scores from the linear model are used as features in XGBoost
4. **Comparison Analysis**: Aligns linear model coefficients with SHAP feature importance

## Components

### 1. Linear Model Attribution (`train_linear_online.py`)

**New Functions:**
- `compute_factor_attribution(date, coefficients, factor_scores)`: Computes per-factor contributions
- `get_top_factors_by_tenor(attribution, top_n)`: Gets top N factors by absolute contribution

**Usage:**
```python
from train_linear_online import compute_factor_attribution, get_top_factors_by_tenor

# Get attribution for a date
attribution = compute_factor_attribution("2025-11-17")

# Get top 5 factors for each tenor
top_factors = get_top_factors_by_tenor(attribution, top_n=5)

# For a specific tenor (e.g., 10Y)
for factor, contribution in top_factors["10Y"]:
    print(f"{factor}: {contribution:.2f} bps")
```

**What it shows:**
- For each tenor, which factors contribute most to the yield change
- Contribution = coefficient × factor_score (in basis points)
- Factors ranked by absolute contribution

### 2. SHAP Analysis (`train_xgboost.py`)

**New Functions:**
- `compute_shap_values(model, X_sample, feature_names)`: Computes SHAP values
- Automatically integrated into training pipeline

**What it shows:**
- Which features (including factor scores) are most important in XGBoost predictions
- Direction and magnitude of each feature's impact
- Feature interactions

**Output:**
- SHAP values saved during training
- Top features ranked by mean absolute SHAP value
- Saved to `models/xgb_{target}_{date}_shap.json`

### 3. Model Connection

**Factor Scores as Features:**
- Factor scores from the linear model are automatically included as features in XGBoost
- Features named `factor_{FACTOR_NAME}` (e.g., `factor_FED_TONE`, `factor_CPI_CORE_SURP`)
- This creates a direct connection between the two models

**Files Modified:**
- `collect_training_data.py`: Adds factor scores to training data
- `enhance_predictions.py`: Includes factor scores in prediction features

### 4. Visualization (`visualize_attribution.py`)

**Visualizations Generated:**

1. **Factor Attribution by Tenor** (`plot_factor_attribution_by_tenor`)
   - Bar charts showing top factors per tenor
   - Color-coded by positive/negative contribution
   - Shows which factors push yields up vs down

2. **Factor Contribution Heatmap** (`plot_factor_contribution_heatmap`)
   - Heatmap across factors (rows) and tenors (columns)
   - Shows which factors affect which parts of the curve
   - Easy to spot patterns (e.g., front-end vs long-end factors)

3. **SHAP Summary Plot** (`plot_shap_summary`)
   - Bar chart of mean absolute SHAP values
   - Shows top features by importance
   - Includes factor features alongside other features

4. **Linear vs SHAP Comparison** (`compare_linear_shap_importance`)
   - Side-by-side comparison of linear coefficients and SHAP importance
   - Shows alignment between the two models
   - Identifies factors important in both models

**Usage:**
```bash
# Generate attribution report for a date
python visualize_attribution.py --date 2025-11-17

# Output saved to attribution_analysis/
# - factor_attribution_2025-11-17.png
# - factor_heatmap_2025-11-17.png
# - attribution_report_2025-11-17.json
```

### 5. Model Comparison (`compare_models.py`)

**Functions:**
- `compare_all_tenors(date)`: Compares linear and SHAP for all tenors
- `compute_alignment_metrics()`: Computes correlation and overlap metrics
- `generate_comparison_report()`: Creates comprehensive comparison report

**Metrics Computed:**
- **Correlation**: Pearson correlation between linear coefficients and SHAP importance
- **Rank Correlation**: Spearman correlation (handles non-linear relationships)
- **Top-10 Overlap**: How many of the top-10 factors overlap between models
- **Alignment Score**: Weighted combination (0-1 scale, higher = better alignment)

**Usage:**
```bash
# Generate comparison report
python compare_models.py --date 2025-11-17

# Output: attribution_analysis/model_comparison_2025-11-17.json
```

**Example Output:**
```json
{
  "date": "2025-11-17",
  "num_tenors_compared": 4,
  "mean_alignment_score": 0.72,
  "mean_correlation": 0.65,
  "comparison_by_tenor": {
    "2y": {
      "tenor": "2Y",
      "alignment": {
        "correlation": 0.68,
        "rank_correlation": 0.71,
        "top_overlap": 7,
        "alignment_score": 0.75
      }
    }
  }
}
```

## Workflow

### Daily Pipeline Integration

The attribution analysis is integrated into the daily pipeline:

1. **Factor Extraction** → Factor scores computed
2. **Linear Model Training** → Coefficients updated, attribution computed
3. **XGBoost Training** → SHAP values computed, factor scores included as features
4. **Attribution Report** → Visualizations and comparisons generated

### Manual Analysis

For detailed analysis on a specific date:

```bash
# 1. Generate attribution visualizations
python visualize_attribution.py --date 2025-11-17

# 2. Compare models
python compare_models.py --date 2025-11-17

# 3. View results
# - Check attribution_analysis/ folder for PNG files
# - Check JSON files for detailed data
```

## Interpreting Results

### High Alignment Score (>0.7)
- Linear model and XGBoost agree on which factors are important
- Factor-based approach is validated by nonlinear model
- Both models are learning similar patterns

### Low Alignment Score (<0.5)
- Models disagree on feature importance
- XGBoost may be capturing interactions not in linear model
- Consider: Are there missing factors? Are interactions important?

### Factor Attribution Insights

**Example: "On 2025-11-17, what drove the 10Y yield change?"**

From linear model attribution:
- `FED_TONE`: +5.2 bps (hawkish tone)
- `CPI_CORE_SURP`: +3.8 bps (inflation surprise)
- `RISK_OFF`: -2.1 bps (risk-off flows)

From SHAP:
- `factor_FED_TONE`: High importance
- `factor_CPI_CORE_SURP`: High importance
- `monetary_policy_count`: Also important (news volume)

**Interpretation:**
- Both models identify FED_TONE and CPI_CORE_SURP as key drivers
- SHAP also shows news volume matters (interaction effect)
- Total attribution: ~7 bps from factors, matching actual move

## Dependencies

```bash
# Required
pip install matplotlib numpy

# Optional but recommended
pip install seaborn shap scipy
```

## Output Files

### Attribution Analysis
- `attribution_analysis/factor_attribution_{date}.png`: Bar charts by tenor
- `attribution_analysis/factor_heatmap_{date}.png`: Heatmap visualization
- `attribution_analysis/attribution_report_{date}.json`: Full report

### Model Comparison
- `attribution_analysis/model_comparison_{date}.json`: Comparison metrics

### SHAP Data
- `models/xgb_{target}_{date}_shap.json`: SHAP values per model

## Future Enhancements

1. **Interactive Dashboards**: Use Plotly for interactive exploration
2. **Time Series Attribution**: Track factor importance over time
3. **Factor Interaction Analysis**: Use SHAP interaction values
4. **Automated Reporting**: Daily email/PDF reports with key insights
5. **Factor Decomposition**: Break down yield changes by factor category (monetary, inflation, etc.)

## Example: Complete Analysis Workflow

```python
from train_linear_online import compute_factor_attribution, get_top_factors_by_tenor
from visualize_attribution import generate_attribution_report
from compare_models import generate_comparison_report

date = "2025-11-17"

# 1. Get linear model attribution
attribution = compute_factor_attribution(date)
top_factors = get_top_factors_by_tenor(attribution, top_n=5)

print("Top factors for 10Y:")
for factor, contrib in top_factors["10Y"]:
    print(f"  {factor}: {contrib:.2f} bps")

# 2. Generate visualizations
viz_report = generate_attribution_report(date)
print(f"Visualizations saved: {viz_report['visualizations']}")

# 3. Compare models
comparison = generate_comparison_report(date)
print(f"Alignment score: {comparison['mean_alignment_score']:.3f}")
```

## Questions Addressed

✅ **"Which factors really push more in the YC change that day?"**
→ Use `compute_factor_attribution()` to get ranked factors by contribution

✅ **"Attribution from the factor side"**
→ Linear model coefficients × factor scores = contribution per factor

✅ **"SHAP analysis for nonlinear models"**
→ Integrated into XGBoost training, shows feature importance

✅ **"Which feature is more important"**
→ SHAP ranking shows top features, including factor features

✅ **"The two steps should have connections"**
→ Factor scores are features in XGBoost; comparison analysis shows alignment

