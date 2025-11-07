# Testing Guide

Complete guide for testing the news ingestion and yield curve prediction system.

## Quick Test

Run the comprehensive test script:

```bash
cd tools/news_ingestion
python3 test_system.py
```

This tests all components and shows what's working and what needs attention.

## Step-by-Step Testing

### 1. Test Basic Components

```bash
cd tools/news_ingestion

# Test database
python3 -c "from db import init_db, get_conn; init_db(); c = get_conn(); print(f'Articles: {c.execute(\"SELECT COUNT(*) FROM articles\").fetchone()[0]}')"

# Test bucketing
python3 -c "from bucket_news import get_bucket_counts; import json; print(json.dumps(get_bucket_counts(), indent=2))"

# Test LLM analysis (if OpenAI configured)
python3 analyze_yield_impact.py --date 2025-11-06
```

### 2. Test News Ingestion

```bash
# Test RSS ingestion (fast)
python3 ingest_rss.py

# Test full ingestion
python3 run_ingest.py

# Check results
python3 -c "from db import get_conn; c = get_conn(); print(f'Total articles: {c.execute(\"SELECT COUNT(*) FROM articles\").fetchone()[0]}')"
```

### 3. Test News Bucketing

```bash
# Bucket articles (uses keyword fallback if no OpenAI)
python3 bucket_news.py --hours 24 --batch-size 10

# Check buckets
python3 -c "from bucket_news import get_bucket_counts; import json; print(json.dumps(get_bucket_counts(), indent=2))"
```

### 4. Test LLM Analysis (Requires OpenAI API Key)

```bash
# Set API key
export OPENAI_API_KEY="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"

# Run analysis
python3 analyze_yield_impact.py --date 2025-11-06

# Check output
cat analyses/yield_impact_2025-11-06.json
```

### 5. Test Training Data Collection

**Prerequisites**: Need historical analyses and snapshots

```bash
# First, generate some historical data
# Build yield curve snapshots
cd ../ust_curve/llm
for date in 2025-10-29 2025-10-30 2025-10-31 2025-11-03; do
    python3 build_snapshots.py --core-module tools.ust_curve.curves $date
done

# Run daily pipeline for those dates (generates analyses)
cd ../../news_ingestion
for date in 2025-10-29 2025-10-30 2025-10-31 2025-11-03; do
    python3 daily_pipeline.py --date $date
done

# Now collect training data
python3 collect_training_data.py --start-date 2025-10-29 --end-date 2025-11-06
```

### 6. Test XGBoost Training (Requires OpenMP on macOS)

**First, fix dependencies:**

```bash
# Install OpenMP (macOS)
brew install libomp

# Fix NumPy version
python3 fix_dependencies.py

# Verify
python3 -c "import numpy, xgboost; print('✓ OK')"
```

**Then test training:**

```bash
# Collect training data first (see step 5)
python3 collect_training_data.py --start-date 2025-10-29 --end-date 2025-11-06

# Train models
python3 train_xgboost.py --data training_data_2025-10-29_2025-11-06.json --threshold-mae 3.0

# Check results
ls -la models/
cat models/xgb_metadata_*.json
```

### 7. Test Rolling 30-Day Updates

```bash
# Update models with rolling window
python3 update_models_rolling.py --days 30

# Check evaluation
cat models/rolling_evaluation_*.json
```

### 8. Test Enhanced Predictions

```bash
# Get enhanced prediction (uses XGBoost if available)
python3 enhance_predictions.py --date 2025-11-06

# Check output
cat analyses/enhanced_yield_impact_2025-11-06.json
```

### 9. Test Full Daily Pipeline

```bash
# Run complete pipeline
python3 daily_pipeline.py

# Or for specific date
python3 daily_pipeline.py --date 2025-11-07
```

## Expected Test Results

### ✅ Passing Tests

- **Imports**: All core modules load
- **Database**: Tables exist, articles stored
- **Bucketing**: Articles categorized
- **LLM Analysis**: Predictions generated (or fallback)
- **Training Data**: Collection works (may return 0 if no historical data)
- **Daily Pipeline**: All steps execute

### ⚠️ Optional/Warnings

- **XGBoost**: Requires OpenMP on macOS (`brew install libomp`)
- **OpenAI**: Optional for LLM features (uses fallback if missing)
- **Training Data**: Need historical data to train models

## Troubleshooting Tests

### "XGBoost requires OpenMP"

**Fix:**
```bash
brew install libomp
python3 fix_dependencies.py
```

### "No training data collected"

**Reason**: Need historical analyses + snapshots

**Fix:**
1. Build yield curve snapshots for past dates
2. Run daily pipeline for those dates
3. Then collect training data

### "NumPy version incompatible"

**Fix:**
```bash
pip install "numpy>=1.24.0,<2.0.0" --upgrade
```

### "No LLM predictions found"

**Reason**: Analyses contain fallback predictions (no OpenAI API key)

**Fix:**
```bash
export OPENAI_API_KEY="your-key"
# Re-run analysis
python3 analyze_yield_impact.py --date 2025-11-06
```

## Integration Test

Test the complete workflow:

```bash
# 1. Fix dependencies
python3 fix_dependencies.py

# 2. Run comprehensive test
python3 test_system.py

# 3. Generate test data (if needed)
python3 daily_pipeline.py --date 2025-11-06

# 4. Test rolling update (if you have 7+ days of data)
python3 update_models_rolling.py --days 30

# 5. Test enhanced predictions
python3 enhance_predictions.py
```

## Performance Testing

```bash
# Time RSS ingestion
time python3 ingest_rss.py

# Time bucketing (100 articles)
time python3 bucket_news.py --hours 24 --batch-size 100

# Time full pipeline
time python3 daily_pipeline.py
```

## Validation Tests

```bash
# Check data quality
python3 -c "
from db import get_conn
c = get_conn()
print('Articles with buckets:', c.execute('SELECT COUNT(*) FROM articles WHERE bucket IS NOT NULL').fetchone()[0])
print('Articles with text:', c.execute('SELECT COUNT(*) FROM articles WHERE text IS NOT NULL').fetchone()[0])
print('Recent runs:', c.execute('SELECT COUNT(*) FROM ingestion_runs').fetchone()[0])
"

# Check model files
ls -lh models/*.pkl 2>/dev/null || echo "No models yet"

# Check analyses
ls -lh analyses/*.json 2>/dev/null || echo "No analyses yet"
```

