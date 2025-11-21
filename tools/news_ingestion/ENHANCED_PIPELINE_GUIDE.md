# Enhanced Yield Curve Prediction Pipeline - Complete Guide

## Meeting Requirements Implementation

Based on the meeting update, the pipeline now focuses on **attributing daily news to daily changes in the yield curve** with the following enhancements:

---

## ✅ 1. Expert Attribution System

### Purpose
Collect expert opinions on which news contributed to yield curve changes as **additional ground truth** alongside actual yield changes.

### Implementation
- **Database Table**: `expert_attributions` stores expert quotes/statements
- **Script**: `extract_expert_attributions.py` uses LLM to extract attribution statements
- **Sources**: Analyst reports, strategist quotes, trader statements in news articles

### How It Works
1. LLM analyzes articles for expert attribution statements
2. Extracts quotes like "yields moved due to Fed signals" or "curve steepened because of inflation data"
3. Links attributions to specific articles and yield changes
4. Stores with confidence scores (0.0-1.0)

### Usage
```bash
# Extract for specific date
python3 extract_expert_attributions.py --date 2025-11-17

# Extract for historical dates
python3 extract_expert_attributions.py --days-back 30
```

### Ground Truth Hierarchy
1. **Primary**: Next day's actual yield curve changes (most reliable)
2. **Secondary**: Expert attributions (provides interpretability)

**Note**: Daily expert attribution data may be limited. The system extracts what's available from news articles and can be enhanced with:
- Direct analyst report APIs
- Structured financial data sources
- Manual curation

---

## ✅ 2. Time Series Lag Analysis (t+n Impact)

### Purpose
Model how news from previous days (t-1, t-2, t-3) affects current yields, since news may have delayed impact.

### Implementation
- **Script**: `collect_training_data_lagged.py` creates training data with lag features
- **Features**: For each lag (0, 1, 2, 3 days):
  - `bucket_{bucket}_count_lag{n}` - Article count
  - `bucket_{bucket}_weight_lag{n}` - Normalized weight
  - `total_articles_lag{n}` - Total articles

### Example
For yield change date **2025-11-17**:
- **Lag 0**: News from 2025-11-17 (before market close) → affects 2025-11-17 yields
- **Lag 1**: News from 2025-11-16 → affects 2025-11-17 yields
- **Lag 2**: News from 2025-11-15 → affects 2025-11-17 yields
- **Lag 3**: News from 2025-11-14 → affects 2025-11-17 yields

### Why This Matters
- **Overnight news**: News after market close affects next day
- **Weekend news**: Weekend events affect Monday yields
- **Delayed reactions**: Some news takes time to be priced in
- **Multi-day impact**: Major events have sustained effects

### Usage
```bash
python3 collect_training_data_lagged.py \
    --start-date 2025-10-01 \
    --end-date 2025-11-17 \
    --max-lag 3
```

### Future Enhancements
- **Variable lags**: Different lags for different news buckets
- **Weekend handling**: Special handling for Friday→Monday transitions
- **Event-specific lags**: Major events may have longer impact windows

---

## ✅ 3. Enhanced Model Selection

### Purpose
Train multiple models and learn article-level weights to identify which articles matter most.

### Implementation
- **Script**: `train_models_enhanced.py` trains ensemble of models
- **Models**:
  1. **XGBoost** (existing) - Gradient boosting, handles non-linear patterns
  2. **Random Forest** (new) - Ensemble trees, robust to overfitting
  3. **Attention Model** (framework) - For sequence learning (future)

### Model Selection
- Trains all available models
- Compares validation MAE
- Selects best model per target (2y, 5y, 10y, 30y, 2s10s, 2s30s)
- Stores all models for comparison

### Feature Importance
Both XGBoost and Random Forest provide:
- Feature importance scores
- Identifies which news buckets matter most
- Shows which lag periods are most predictive

### Article-Level Weights
**Future Enhancement**: The `article_yield_impact_weights` table is ready to store learned weights per article. This can be implemented using:
- Attention mechanisms in neural networks
- Feature importance from tree models
- Regression coefficients from linear models

### Usage
```bash
python3 train_models_enhanced.py \
    --data training_data_lagged_2025-10-01_2025-11-17.json \
    --test-size 0.2
```

### Alternative Models to Consider
1. **Transformer Models**: For sequence learning (news over time)
2. **LSTM/GRU**: For time series patterns
3. **Ensemble Voting**: Combine multiple models
4. **Attention Mechanisms**: Learn which articles to focus on

---

## ✅ 4. Look-Ahead Bias Prevention (CRITICAL)

### Purpose
**Ensure no future information leaks into predictions** - any news published AFTER market close on a day should NOT be used to predict that day's yields.

### Implementation
- **Module**: `lookahead_bias_utils.py` - Comprehensive timestamp validation
- **Market Close**: 4:00 PM ET (16:00 ET) = 9:00 PM UTC (EST) or 8:00 PM UTC (EDT)
- **All Queries**: Now filter `published_at < market_close_time`

### Key Functions
```python
from lookahead_bias_utils import (
    get_market_close_time,           # Get market close for a date
    is_article_before_market_close,  # Validate single article
    get_valid_news_for_date,         # Get valid time window
    validate_no_lookahead_bias       # Comprehensive validation
)
```

### Validation
**Automatic**: Daily pipeline validates automatically
**Manual**: Run validation script
```bash
python3 validate_lookahead_bias.py --start-date 2025-11-01 --end-date 2025-11-17
```

### Updated Functions
All these functions now prevent look-ahead bias:
- `get_bucketed_news()` - Filters by market close
- `get_bucket_counts()` - Only counts pre-market-close articles
- `prepare_training_record()` - Excludes post-market-close articles
- All training data collection - Validates timestamps

### Example
For **2025-11-17**:
- ✅ **Valid**: Article published at 2:00 PM ET on 2025-11-17 (before 4 PM close)
- ❌ **Invalid**: Article published at 5:00 PM ET on 2025-11-17 (after 4 PM close)
- ✅ **Valid**: Article published at 10:00 PM ET on 2025-11-16 (affects next day)

---

## Updated Pipeline Flow

```
1. NEWS INGESTION
   → Collect articles with published_at timestamps
   → Store fetched_at (when we collected it)

2. NEWS BUCKETING
   → Categorize articles (only pre-market-close for target date)
   → Filter: published_at < market_close_time

3. YIELD CURVE DATA SYNC
   → Load yield curve snapshots
   → Store market_close_time for validation

4. LLM YIELD IMPACT ANALYSIS
   → Analyze news (only pre-market-close)
   → Generate predictions with reasoning
   → Validate no look-ahead bias

5. EXPERT ATTRIBUTION EXTRACTION (NEW)
   → Extract expert opinions from articles
   → Link attributions to yield changes
   → Store as additional ground truth

6. TRAINING DATA PREPARATION
   → Create examples with lag features (t-0, t-1, t-2, t-3)
   → Include expert attributions
   → Validate no look-ahead bias

7. LAGGED TRAINING DATA COLLECTION (NEW)
   → Collect training data with time series lags
   → Save for enhanced model training

8. MODEL TRAINING (ENHANCED)
   → Train XGBoost, Random Forest
   → Compare performance
   → Select best model per target
   → Learn feature importance
```

---

## Database Schema Updates

### Apply Updates
```bash
cd tools/news_ingestion
python3 -c "from db import get_conn; conn = get_conn(); exec(open('schema_updates.sql').read()); conn.commit()"
```

### New Tables
1. **expert_attributions**: Expert opinions on news attribution
2. **article_yield_impact_weights**: Learned weights per article (future)
3. **news_yield_training_lagged**: Training data with lag features

### Updated Tables
- **yield_curve_daily**: Added `market_close_time`, `snapshot_time`

---

## Testing & Validation

### 1. Look-Ahead Bias Validation
```bash
# Validate all dates
python3 validate_lookahead_bias.py --start-date 2025-11-01 --end-date 2025-11-17

# Check timestamp quality
python3 validate_lookahead_bias.py --check-timestamps
```

### 2. Expert Attribution Extraction
```bash
# Test extraction
python3 extract_expert_attributions.py --date 2025-11-17
```

### 3. Lagged Training Data
```bash
# Collect with lags
python3 collect_training_data_lagged.py \
    --start-date 2025-11-01 \
    --end-date 2025-11-17 \
    --max-lag 3
```

### 4. Enhanced Model Training
```bash
# Train ensemble models
python3 train_models_enhanced.py \
    --data training_data_lagged_2025-11-01_2025-11-17.json
```

---

## Key Design Decisions

### 1. Market Close Time
- **Fixed at 4 PM ET**: Standard US Treasury market close
- **UTC Conversion**: Automatically handles EST/EDT
- **Conservative Approach**: Only articles published before close are used

### 2. Lag Window
- **Default: 3 days**: Captures most delayed impacts
- **Configurable**: Can adjust `--max-lag` parameter
- **Future**: Could use different lags per bucket

### 3. Expert Attribution
- **LLM Extraction**: Uses GPT-4o to find expert quotes
- **Confidence Scoring**: 0.0-1.0 based on clarity of attribution
- **Fallback**: If no expert attributions found, still use actual yield changes

### 4. Model Selection
- **Validation MAE**: Primary selection criterion
- **Feature Importance**: For interpretability
- **Ensemble Ready**: Can combine models in future

---

## Next Steps

1. **Apply Schema Updates**: Run `schema_updates.sql`
2. **Validate Existing Data**: Check for look-ahead bias violations
3. **Extract Expert Attributions**: Run on historical dates
4. **Collect Lagged Training Data**: Generate training data with lags
5. **Train Enhanced Models**: Compare XGBoost vs Random Forest
6. **Evaluate Performance**: Check if lag features improve accuracy
7. **Implement Article Weights**: Add attention mechanisms for article-level weighting

---

## Files Created

### Core Implementation
- `schema_updates.sql` - Database schema updates
- `lookahead_bias_utils.py` - Look-ahead bias prevention
- `extract_expert_attributions.py` - Expert attribution extraction
- `collect_training_data_lagged.py` - Lagged training data collection
- `train_models_enhanced.py` - Enhanced model training
- `validate_lookahead_bias.py` - Validation script

### Documentation
- `IMPLEMENTATION_SUMMARY.md` - Detailed implementation guide
- `QUICK_REFERENCE_ENHANCED.md` - Quick reference
- `ENHANCED_PIPELINE_GUIDE.md` - This file

### Modified Files
- `daily_pipeline.py` - Integrated all new features
- `analyze_yield_impact.py` - Added look-ahead prevention
- `bucket_news.py` - Added look-ahead prevention
- `prepare_training_record()` - Added look-ahead prevention

---

## Summary

The enhanced pipeline now:
✅ **Prevents look-ahead bias** with market close time validation
✅ **Extracts expert attributions** as additional ground truth
✅ **Models time series lags** (t+n impact)
✅ **Trains multiple models** and selects best
✅ **Validates all data** for timestamp correctness

All changes maintain backward compatibility while adding new capabilities for more accurate yield curve attribution.

