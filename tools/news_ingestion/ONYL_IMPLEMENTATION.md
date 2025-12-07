# ONYL (Online News→Yield Learner) Implementation

## Overview

This document describes the implementation of the linear online learning algorithm (ONYL) alongside the existing XGBoost model, as specified in the "YC Attribution Algo.pdf" and "Factors and Cold Start Coefficients.pdf" documents.

## Key Components

### 1. Factor Extraction (`extract_factors.py`)

Extracts specific economic factors from news articles using LLM analysis.

**Factors Extracted:**
- **Monetary Policy**: FED_TONE, FED_PATH_SURPRISE, POLICY_RATE_SURPRISE, BAL_SHEET_QT_QE
- **Inflation & Growth**: CPI_CORE_SURP, PCE_CORE_SURP, NFP_SURP, WAGE_SURP, ISM_SURP, INFL_EXP_SURP, etc.
- **Supply/Fiscal**: SUPPLY_LONG, SUPPLY_BILLS, FISCAL_DEFICIT_NEWS, TERM_PREMIUM_NEWS
- **Risk**: RISK_OFF, RISK_ON, MOVE_SHIFT
- **Energy/Housing**: OIL_SHOCK_UP, OIL_SHOCK_DOWN, MBS_CONVEXITY, HOUSING_TURN, FUNDING_STRESS
- **Global**: ECB_TONE, BOE_TONE, YCC_JGB_SHIFT, CHINA_GROWTH_NEWS, GEO_EVENT

**Output Format:**
- Per article: `{factor_name, intensity, confidence}`
- Intensity: s ∈ [-2.0, +2.0] (direction and strength)
- Confidence: c ∈ [0.0, 1.0] (certainty factor is present)
- Daily aggregation: factor_score = sum(c × s) clipped to [-2.5, +2.5]

### 2. Linear Online Learning (`train_linear_online.py`)

Implements the ONYL algorithm:

**Prediction:**
```
Δy_t,k = Σ(B_k,f × x_t,f) + b_k
```

**Update Rule:**
```
B_k,f ← B_k,f + η × w_t,f × e_t,k × x_t,f
```

**Hyperparameters:**
- Learning rate η = 0.05
- Forgetting factor λ = 0.98
- Max daily coef change ΔB_max = 0.8 bps/(unit factor)
- Smoothing γ = 0.2

**Features:**
- Sign guards (economic constraints)
- Smoothing across maturities
- Intercept (bias) terms
- Weighted updates based on factor magnitude

**Tenors:** [3M, 2Y, 5Y, 10Y, 30Y]

### 3. Cold-Start Coefficients

Stored in `news_config.yaml` under `linear_model_cold_start` section.

All factors from the PDFs are included with expert priors in bps per unit factor for each tenor.

### 4. Database Schema

New tables:
- `article_factors`: Article-level factor scores
- `daily_factor_scores`: Aggregated daily factor scores
- `linear_model_coefficients`: Updated coefficients per date/tenor/factor
- `linear_model_intercepts`: Bias terms per date/tenor
- `linear_model_predictions`: Predictions and errors for evaluation

### 5. Yield Curve 3M Support

Updated yield curve processing to include 3M tenor:
- `tools/ust_curve/run_curve.py`: Maps "3 Mo" from Treasury CSV to "0.25" years
- `tools/ust_curve/llm/build_snapshots.py`: Includes 0.25 (3M) in standard tenors, outputs as "3M"

## Daily Pipeline Integration

The daily pipeline now includes:

1. **News Ingestion**
2. **News Bucketing**
3. **Factor Extraction** (NEW)
4. **Yield Curve Data Sync** (now includes 3M)
5. **Linear Model Prediction & Update** (NEW)
6. **LLM Yield Impact Analysis**
7. **Expert Attribution Extraction**
8. **Training Data Preparation**
9. **XGBoost Model Training** (preserved)
10. **Lagged Training Data Collection**

## Usage

### Extract Factors for Historical Articles

```bash
cd tools/news_ingestion
python3 extract_factors_historical.py --start-date 2025-10-01 --end-date 2025-11-20 --resume
```

### Train Linear Model for a Date

```bash
python3 train_linear_online.py --date 2025-11-20
```

### Compare Models

```bash
python3 compare_models.py --date 2025-11-20
python3 compare_models.py --start-date 2025-11-01 --end-date 2025-11-20 --output comparison.json
```

## Implementation Status

✅ Database schema created
✅ Cold-start coefficients added to config
✅ Factor extraction module implemented
✅ Linear online learning module implemented
✅ Retroactive extraction script created
✅ Daily pipeline updated
✅ Yield curve 3M support added
✅ Model comparison utility created

## Next Steps

1. **Apply database schema**: Run `schema_factors.sql`
2. **Extract factors for historical articles**: Run `extract_factors_historical.py`
3. **Initialize linear model**: Run `train_linear_online.py` for recent dates
4. **Monitor both models**: Use `compare_models.py` to track performance

## Notes

- Linear model runs alongside XGBoost (both models are trained/predicted)
- XGBoost continues to use [2Y, 5Y, 10Y, 30Y] (no 3M)
- Linear model uses [3M, 2Y, 5Y, 10Y, 30Y] as specified in PDFs
- Factor extraction can be applied retroactively to all historical news
- Cold-start coefficients are expert priors that get updated daily via online learning

