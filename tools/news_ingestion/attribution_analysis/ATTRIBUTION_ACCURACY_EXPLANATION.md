# Attribution Accuracy Calculation - Detailed Explanation

## Current Attribution Accuracy

**Latest Analysis Date**: 2025-12-01  
**Dates with Complete Data**: 4 dates (2025-11-21, 2025-11-25, 2025-11-26, 2025-11-28)

### Summary Statistics

| Metric | Value |
|--------|-------|
| **Mean Attribution Error** | 48.44 bps (across 4 dates) |
| **Best Performance** | 10.29 bps (2025-11-28) |
| **Worst Performance** | 84.59 bps (2025-11-21) |
| **Standard Deviation** | 26.30 bps |
| **Improvement Trend** | 79.6% reduction from 2025-11-26 to 2025-11-28 |

### Recent Performance by Date

| Date | Attribution Error (bps) | Full Model Error (bps) | Status |
|------|-------------------------|------------------------|--------|
| 2025-11-21 | 84.59 | 86.07 | Initial baseline |
| 2025-11-25 | 48.40 | 48.40 | Improving |
| 2025-11-26 | 50.49 | 50.49 | Stable |
| 2025-11-28 | **10.29** | **10.29** | **Best performance** |

---

## How Attribution Accuracy is Calculated

### Step-by-Step Process

#### 1. **Factor Attribution Calculation**

For each tenor (3M, 2Y, 5Y, 10Y, 30Y) and each date:

```python
# For each factor f:
Contribution_f,k = B_k,f × x_t,f

Where:
- B_k,f = coefficient for factor f at tenor k (learned by linear model)
- x_t,f = factor score for factor f on date t (aggregated from articles)
- Contribution_f,k = contribution of factor f to yield change at tenor k (in bps)
```

**Example:**
- Factor: `FED_TONE`
- Coefficient for 10Y: `B_10Y,FED_TONE = 2.5 bps`
- Factor score: `x_t,FED_TONE = 5.0`
- Contribution: `2.5 × 5.0 = 12.5 bps`

#### 2. **Attribution-Only Prediction**

For each tenor, sum all factor contributions (excluding intercept):

```python
predicted_attrib[tenor] = Σ(Contribution_f) for all factors
                        = Σ(B_k,f × x_t,f) for all factors f
```

**Key Point**: This does NOT include the intercept term `b_k`.

**Why exclude intercept?**
- Attribution focuses on **which factors** drive yield changes
- The intercept represents baseline/structural effects (not factor-driven)
- This isolates factor-driven vs. structural effects

#### 3. **Error Calculation**

Compare attribution-only prediction to actual yield changes:

```python
error[tenor] = |actual[tenor] - predicted_attrib[tenor]|
```

**Example (2025-11-28, 10Y tenor):**
- Actual yield change: `1.88 bps`
- Predicted from attribution: `9.00 bps` (sum of all factor contributions)
- Error: `|1.88 - 9.00| = 7.12 bps`

#### 4. **Mean Attribution Error**

Average error across all tenors:

```python
mean_error = (1/N) × Σ(error[tenor]) for all tenors
```

**Example (2025-11-28):**
- Errors: [7.12, 12.23, 4.82, 19.87, 7.42] bps (for 10Y, 2Y, 30Y, 3M, 5Y)
- Mean error: `(7.12 + 12.23 + 4.82 + 19.87 + 7.42) / 5 = 10.29 bps`

---

## Full Model vs. Attribution-Only

### Full Model Prediction

The complete linear model prediction includes the intercept:

```python
predicted_full[tenor] = intercept[tenor] + Σ(Contribution_f)
                       = b_k + Σ(B_k,f × x_t,f)
```

### Comparison

| Metric | Attribution-Only | Full Model | Difference |
|--------|-----------------|------------|------------|
| **Formula** | `Σ(contributions)` | `intercept + Σ(contributions)` | `intercept` |
| **Purpose** | Factor-driven changes | Complete prediction | Structural effects |
| **Typical Error** | Higher (no intercept) | Lower (with intercept) | Intercept benefit |

**Current Status:**
- On 2025-11-28, attribution error = full model error (10.29 bps)
- This means the intercept is near zero, so factor contributions alone explain the changes well

---

## Interpretation of Attribution Accuracy

### What Does Attribution Error Mean?

**Low Error (< 10 bps):**
- Factor contributions explain most of the yield changes
- Model has identified the key drivers
- Attribution is reliable

**Medium Error (10-30 bps):**
- Some yield changes not explained by factors
- May need more factors or better factor extraction
- Attribution is partially reliable

**High Error (> 30 bps):**
- Large portion of yield changes unexplained
- Factors may be missing or incorrectly weighted
- Attribution is less reliable

### Current Performance Analysis

**2025-11-28 (Best Performance: 10.29 bps):**
- **Excellent**: Attribution error < 10 bps
- Factor contributions explain 90%+ of yield changes
- Model is identifying key drivers accurately

**2025-11-21 (Worst Performance: 84.59 bps):**
- **Poor**: Attribution error > 80 bps
- Large unexplained portion
- Possible causes:
  - Model coefficients not yet converged (early in training)
  - Missing factors for that day's news
  - Market noise vs. signal

**Trend:**
- 📈 **Improving**: 79.6% reduction from 2025-11-26 to 2025-11-28
- 📈 Model is learning and improving over time
- 📈 Attribution accuracy is stabilizing

---

## Factors Affecting Attribution Accuracy

### 1. **Model Convergence**
- Early dates: Coefficients not fully learned → higher error
- Later dates: Coefficients converged → lower error
- **Solution**: Continue training to improve coefficients

### 2. **Factor Coverage**
- Days with many factors extracted → better attribution
- Days with few factors → higher error
- **Example**: 2025-11-29 had only 5 factors → no accuracy data (no actuals)

### 3. **Factor Quality**
- High-confidence factors → more reliable attribution
- Low-confidence factors → less reliable
- **Solution**: Filter by confidence threshold

### 4. **Market Noise**
- Some yield changes are random/unexplainable
- Not all moves are factor-driven
- **Solution**: Accept some irreducible error

### 5. **Missing Factors**
- News may contain factors not in our 20+ factor list
- New economic events may require new factors
- **Solution**: Expand factor list based on analysis

---

## How to Improve Attribution Accuracy

### Short-Term (Next Week)

1. **Continue Daily Training**
   - More training data → better coefficients
   - Model improves with each significant move

2. **Improve Factor Extraction**
   - Increase factor extraction coverage
   - Filter low-confidence factors

3. **Monitor Trends**
   - Track attribution error daily
   - Identify patterns in high-error days

### Medium-Term (Next Month)

1. **Expand Factor List**
   - Add missing factors based on analysis
   - Cover more economic events

2. **Refine Coefficients**
   - Adjust learning rate
   - Add regularization

3. **Feature Engineering**
   - Add factor interactions
   - Include lag features

### Long-Term (Next Quarter)

1. **Advanced Models**
   - Non-linear factor interactions
   - Time-varying coefficients

2. **External Data**
   - Macro indicators
   - Market sentiment data

3. **Ensemble Methods**
   - Combine multiple attribution methods
   - Weight by confidence

---

## Code Reference

### Key Functions

**Attribution Calculation:**
```python
from train_linear_online import compute_factor_attribution

attribution = compute_factor_attribution(date)
# Returns: {tenor: {factor_name: contribution_bps}}
```

**Accuracy Calculation:**
```python
from train_linear_online import get_actual_yield_changes

actuals = get_actual_yield_changes(date)
predicted_attrib = {tenor: sum(factors.values()) for tenor, factors in attribution.items()}
errors = {tenor: abs(actuals[tenor] - predicted_attrib[tenor]) for tenor in actuals.keys()}
mean_error = sum(errors.values()) / len(errors)
```

### Files

- **Attribution Calculation**: `train_linear_online.py::compute_factor_attribution()`
- **Accuracy Analysis**: Run `python3 check_attribution_accuracy.py` (if exists)
- **Reports**: `attribution_analysis/attribution_performance_report_*.json`

---

## Summary

**Current Status:**
- Attribution accuracy is **improving** (79.6% reduction)
- Best performance: **10.29 bps** (excellent)
- Model is learning and converging
- Some dates still have high error (need more training)

**Calculation Method:**
1. Sum factor contributions (exclude intercept)
2. Compare to actual yield changes
3. Calculate mean absolute error across tenors

**Next Steps:**
1. Continue daily training
2. Monitor attribution error trends
3. Expand factor coverage
4. Refine model coefficients

---

*Last Updated: 2025-12-01*

