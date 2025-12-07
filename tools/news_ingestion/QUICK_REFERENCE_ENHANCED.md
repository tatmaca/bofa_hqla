# Quick Reference: Enhanced Yield Curve Prediction

## Key Enhancements

### 1. Look-Ahead Bias Prevention ✅
**Critical**: All queries now filter articles by market close time (4 PM ET).

**Usage**:
```python
from lookahead_bias_utils import validate_no_lookahead_bias

is_valid, violations = validate_no_lookahead_bias("2025-11-17")
```

**Validation Script**:
```bash
python3 validate_lookahead_bias.py --start-date 2025-11-01 --end-date 2025-11-17
```

### 2. Expert Attribution Extraction ✅
Extract expert opinions on which news drove yield changes.

**Usage**:
```bash
# Extract for specific date
python3 extract_expert_attributions.py --date 2025-11-17

# Extract for last 7 days
python3 extract_expert_attributions.py --days-back 7
```

**Output**: Stored in `expert_attributions` table with:
- Attribution text (expert quote)
- Attributed yields (which tenors mentioned)
- Confidence score
- Source article

### 3. Time Series Lag Features ✅
Model news from t-n affecting yields at t.

**Usage**:
```bash
python3 collect_training_data_lagged.py \
    --start-date 2025-10-01 \
    --end-date 2025-11-17 \
    --max-lag 3
```

**Features Created**:
- `bucket_{bucket}_count_lag0` - Same day
- `bucket_{bucket}_count_lag1` - t-1 day
- `bucket_{bucket}_count_lag2` - t-2 days
- `bucket_{bucket}_count_lag3` - t-3 days

### 4. Enhanced Model Training ✅
Train multiple models and select best.

**Usage**:
```bash
python3 train_models_enhanced.py \
    --data training_data_lagged_2025-10-01_2025-11-17.json
```

**Models**:
- XGBoost (gradient boosting)
- Random Forest (ensemble trees)
- Best model selected per target based on validation MAE

---

## Database Updates

**Apply schema updates**:
```bash
cd tools/news_ingestion
python3 -c "from db import get_conn; conn = get_conn(); exec(open('schema_updates.sql').read()); conn.commit()"
```

**New Tables**:
- `expert_attributions` - Expert opinions
- `article_yield_impact_weights` - Learned article weights
- `news_yield_training_lagged` - Lagged training data

---

## Updated Pipeline Flow

The daily pipeline now runs 7 steps (was 6):

1. News Ingestion (with timestamp validation)
2. News Bucketing (filters by market close)
3. Yield Curve Data Sync
4. LLM Yield Impact Analysis (look-ahead prevention)
5. **Expert Attribution Extraction** (NEW)
6. Training Data Prep (look-ahead prevention)
7. **Lagged Training Data Collection** (NEW)

---

## Look-Ahead Bias Prevention

**Market Close**: 4:00 PM ET (16:00 ET) = 9:00 PM UTC (EST) or 8:00 PM UTC (EDT)

**All queries now filter**:
```sql
WHERE published_at < market_close_time
```

**Validation**:
- Automatic validation in daily pipeline
- Manual validation: `validate_lookahead_bias.py`
- All training data excludes post-market-close articles

---

## Next Steps

1. **Apply schema updates** to database
2. **Run validation** to check for existing violations
3. **Extract expert attributions** for historical dates
4. **Collect lagged training data** for model training
5. **Train enhanced models** and compare performance

---

## Files Created

- `schema_updates.sql` - Database updates
- `lookahead_bias_utils.py` - Look-ahead prevention utilities
- `extract_expert_attributions.py` - Expert attribution extraction
- `collect_training_data_lagged.py` - Lagged training data
- `train_models_enhanced.py` - Enhanced model training
- `validate_lookahead_bias.py` - Validation script
- `IMPLEMENTATION_SUMMARY.md` - Detailed documentation
- `QUICK_REFERENCE_ENHANCED.md` - This file

