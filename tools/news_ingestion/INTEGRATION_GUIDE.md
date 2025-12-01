# Integration Guide: News-to-Yield Curve Prediction System

This guide explains how to integrate the news-to-yield curve prediction system into the broader project pipeline.

## Overview

The news ingestion and yield curve prediction system provides:
1. **Daily news collection and categorization** (8 buckets)
2. **Economic factor extraction** (20+ factors from articles)
3. **Linear online learning model** (ONYL algorithm) for yield curve prediction
4. **XGBoost nonlinear model** with SHAP interpretability
5. **Attribution analysis** (factor contribution ranking)
6. **Web dashboard** for visualization

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Pipeline                           │
│  (tools/news_ingestion/daily_pipeline.py)                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ News         │   │ Factor       │   │ Yield Curve  │
│ Ingestion    │   │ Extraction   │   │ Sync        │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     Linear Model (ONYL)                │
        │  - Factor scores → Yield predictions  │
        │  - Attribution analysis                │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     XGBoost Model                     │
        │  - Nonlinear predictions              │
        │  - SHAP feature importance             │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     Outputs                            │
        │  - Predictions (database)              │
        │  - Attribution reports (JSON/PNG)      │
        │  - Model metadata (JSON)               │
        └───────────────────────────────────────┘
```

## Integration Points

### 1. Database Integration

**Shared Tables:**
- `yield_curve_daily` - Yield curve snapshots (synced from `tools/ust_curve/`)
- `articles` - News articles (ingested daily)
- `linear_model_predictions` - Daily predictions
- `linear_model_coefficients` - Model coefficients
- `daily_factor_scores` - Aggregated factor scores

**Database Location:**
- `tools/news_ingestion/news.db` (SQLite)

**Schema Files:**
- `tools/news_ingestion/schema.sql` - Core schema
- `tools/news_ingestion/schema_factors.sql` - Factor extraction schema

### 2. File-Based Integration

**Yield Curve Snapshots:**
- **Source**: `tools/ust_curve/llm/snapshots/curve_snapshot_{date}.json`
- **Sync**: Automatic via `daily_pipeline.py` Step 4
- **Format**: JSON with `delta_zeros_pct` and `delta_spreads_pct`

**Attribution Reports:**
- **Location**: `tools/news_ingestion/attribution_analysis/`
- **Files**:
  - `attribution_report_{date}.json` - Full attribution data
  - `factor_attribution_{date}.png` - Visualization
  - `factor_heatmap_{date}.png` - Heatmap visualization

**Model Files:**
- **Location**: `tools/news_ingestion/models/`
- **Files**:
  - `xgb_{target}_{date}.pkl` - Trained XGBoost models
  - `xgb_{target}_{date}_shap.json` - SHAP values
  - `xgb_metadata_{date}.json` - Model metadata

### 3. API Integration

**Web Dashboard API:**
- **Location**: `web_dashboard/app.py`
- **Endpoints**:
  - `/api/attribution/<date>` - Get linear factor attribution
  - `/api/xgboost/<date>` - Get XGBoost predictions
  - `/api/linear-prediction/<date>` - Get linear model predictions
  - `/api/predictions/<date>` - Get all predictions

**Usage Example:**
```python
import requests

# Get attribution for a date
response = requests.get('http://localhost:5000/api/attribution/2025-11-28')
attribution = response.json()

# Get XGBoost predictions
response = requests.get('http://localhost:5000/api/xgboost/2025-11-28')
xgboost_pred = response.json()
```

### 4. Data Export Integration

**Scenario Generation Export:**
- **Script**: `tools/news_ingestion/export_news_for_scenario_gen.py`
- **Output**: `tools/news_ingestion/news_export_for_scenario_gen.json`
- **Format**: JSON with daily news buckets, articles, LLM predictions, yield snapshots

**Usage:**
```bash
cd tools/news_ingestion
python3 export_news_for_scenario_gen.py --start-date 2025-10-01 --end-date 2025-11-15
```

## Integration Steps

### Step 1: Database Setup

1. **Initialize Database:**
```bash
cd tools/news_ingestion
python3 -c "from db import init_db; init_db()"
```

2. **Apply Factor Schema:**
```bash
python3 -c "from db import get_conn; conn = get_conn(); exec(open('schema_factors.sql').read()); conn.commit()"
```

3. **Verify Tables:**
```python
from db import get_conn
conn = get_conn()
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print([t[0] for t in tables])
```

### Step 2: Daily Pipeline Setup

1. **Configure API Keys:**
   - Set `OPENAI_API_KEY` environment variable, OR
   - Add to `tools/news_ingestion/news_config.yaml`:
   ```yaml
   openai_api_key: "your-key-here"
   ```

2. **Run Daily Pipeline:**
```bash
cd tools/news_ingestion
python3 daily_pipeline.py
```

3. **Automate (Optional):**
   - See `DAILY_AUTOMATION.md` for cron/systemd/launchd setup
   - Recommended: Run after market close (4 PM ET)

### Step 3: Access Predictions

**From Database:**
```python
from train_linear_online import get_linear_model_predictions

predictions = get_linear_model_predictions("2025-11-28")
# Returns: {tenor: {predicted_delta_bps, actual_delta_bps, error_bps}}
```

**From Attribution:**
```python
from train_linear_online import compute_factor_attribution

attribution = compute_factor_attribution("2025-11-28")
# Returns: {tenor: {factor_name: contribution_bps}}
```

**From XGBoost:**
```python
from enhance_predictions import predict_with_enhancement

enhanced = predict_with_enhancement("2025-11-28")
# Returns: {predictions: {...}, spreads: {...}, model_date: "..."}
```

### Step 4: Web Dashboard (Optional)

1. **Start Dashboard:**
```bash
cd web_dashboard
python3 app.py
```

2. **Access:**
   - URL: `http://localhost:5000`
   - View predictions, attribution, and XGBoost results

## Data Flow

### Daily Workflow

```
1. News Ingestion (Step 1)
   → Collect articles from RSS feeds
   → Store in `articles` table

2. News Bucketing (Step 2)
   → Categorize articles into 8 buckets
   → Update `articles.bucket` column

3. Factor Extraction (Step 3)
   → Extract economic factors from articles
   → Store in `article_factors` table
   → Aggregate to `daily_factor_scores` table

4. Yield Curve Sync (Step 4)
   → Read from `tools/ust_curve/llm/snapshots/`
   → Store in `yield_curve_daily` table

5. Linear Model Training (Step 5)
   → Load coefficients and factor scores
   → Predict yield changes
   → Update coefficients based on actuals
   → Save predictions to `linear_model_predictions`

6. Attribution Analysis (Step 5b)
   → Compute factor contributions
   → Generate visualizations
   → Save reports to `attribution_analysis/`

7. LLM Analysis (Step 6)
   → Analyze news impact (optional)
   → Store in `analyses/` directory

8. XGBoost Training (Step 8b)
   → Collect training data with factor features
   → Train models with rolling window
   → Save models and SHAP values
```

## Integration with Other Components

### Scenario Generation System

**Location**: `scenario_gen/`

**Integration Method:**
1. Export news data:
```bash
cd tools/news_ingestion
python3 export_news_for_scenario_gen.py --start-date 2025-10-01 --end-date 2025-11-15
```

2. Import in scenario generation:
```python
import json

with open('tools/news_ingestion/news_export_for_scenario_gen.json') as f:
    news_data = json.load(f)

# Use news_data['daily_data'] for scenario generation
```

### Risk Metrics System

**Location**: `hqla_risk_metrics/`

**Integration Method:**
1. Access attribution data:
```python
from train_linear_online import compute_factor_attribution

attribution = compute_factor_attribution(date)
# Use for factor-based risk attribution
```

2. Access predictions:
```python
from train_linear_online import get_linear_model_predictions

predictions = get_linear_model_predictions(date)
# Use for risk calculations
```

### Mobile App

**Location**: `mobile_app/`

**Integration Method:**
1. Use API endpoints:
```javascript
// Fetch attribution
fetch('http://your-server:5000/api/attribution/2025-11-28')
  .then(res => res.json())
  .then(data => {
    // Display attribution data
  });
```

2. Push notifications:
   - Monitor `linear_model_predictions` for significant moves
   - Trigger alerts based on thresholds

## Configuration

### Required Configuration

**File**: `tools/news_ingestion/news_config.yaml`

```yaml
openai_api_key: "your-key-here"  # Required for LLM analysis

linear_model_cold_start:
  learning_rate: 0.05
  coefficients:
    # Initial coefficients per factor/tenor
    # (see ONYL_IMPLEMENTATION.md for details)
```

### Optional Configuration

**Look-Ahead Bias Prevention:**
- Market close time: 4:00 PM ET (configured in `lookahead_bias_utils.py`)
- All queries automatically filter by market close

**Model Training:**
- Rolling window: 30 days (configurable in `update_models_rolling.py`)
- Minimum training examples: 5 (configurable)

## Dependencies

### Python Packages

**Required:**
```bash
pip install numpy pandas sqlite3 openai
```

**Optional (for full functionality):**
```bash
pip install xgboost scikit-learn shap matplotlib seaborn flask
```

**Note**: Use `numpy<2.0` for XGBoost compatibility

### External Services

- **OpenAI API**: Required for LLM analysis and factor extraction
- **RSS Feeds**: For news ingestion (see `ingest_rss.py`)

## Testing Integration

### 1. Test Database Connection

```python
from db import get_conn
conn = get_conn()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM articles").fetchone()
```

### 2. Test Daily Pipeline

```bash
cd tools/news_ingestion
python3 daily_pipeline.py --date 2025-11-28
```

### 3. Test Attribution

```python
from train_linear_online import compute_factor_attribution

attribution = compute_factor_attribution("2025-11-28")
print(f"Attribution computed: {len(attribution)} tenors")
```

### 4. Test API

```bash
curl http://localhost:5000/api/attribution/2025-11-28
```

## Troubleshooting

### Common Issues

1. **No Factor Scores:**
   - Check: `SELECT COUNT(*) FROM daily_factor_scores WHERE date = '2025-11-28'`
   - Solution: Run factor extraction: `python3 extract_factors.py --date 2025-11-28`

2. **No Yield Curve Data:**
   - Check: `SELECT COUNT(*) FROM yield_curve_daily WHERE date = '2025-11-28'`
   - Solution: Ensure snapshots exist in `tools/ust_curve/llm/snapshots/`

3. **XGBoost Training Fails:**
   - Check: Minimum 5 days of complete training data
   - Solution: Continue running daily pipeline to accumulate data

4. **Attribution Error High:**
   - Normal for early dates (model learning)
   - Improves over time as coefficients converge
   - Check: `attribution_analysis/ATTRIBUTION_ACCURACY_EXPLANATION.md`

## Performance Considerations

### Daily Pipeline Runtime

- **News Ingestion**: 2-5 minutes
- **Factor Extraction**: 5-10 minutes (depends on article count)
- **Model Training**: 1-3 minutes
- **Total**: ~10-20 minutes

### Database Size

- **Articles**: ~100-500 per day
- **Factor Scores**: ~20-50 factors per day
- **Predictions**: 5 tenors per day
- **Estimated Growth**: ~50 MB per month

### API Response Time

- **Attribution API**: < 100ms
- **XGBoost API**: < 200ms
- **Predictions API**: < 50ms

## Maintenance

### Daily Tasks

1. **Run Daily Pipeline**: After market close (4 PM ET)
2. **Monitor Errors**: Check logs in `tools/news_ingestion/logs/`
3. **Verify Data**: Check `check_status.py` output

### Weekly Tasks

1. **Review Attribution Accuracy**: Check `attribution_analysis/ATTRIBUTION_PERFORMANCE_REPORT_*.md`
2. **Check Model Performance**: Review `models/xgb_metadata_*.json`
3. **Update Documentation**: As needed

### Monthly Tasks

1. **Archive Old Data**: Move old reports to archive
2. **Database Maintenance**: Vacuum database if needed
3. **Review Configuration**: Update as needed

## Support

### Documentation

- **Main README**: `tools/news_ingestion/README.md`
- **Attribution Analysis**: `tools/news_ingestion/ATTRIBUTION_ANALYSIS.md`
- **ONYL Implementation**: `tools/news_ingestion/ONYL_IMPLEMENTATION.md`
- **Pipeline Guide**: `tools/news_ingestion/ENHANCED_PIPELINE_GUIDE.md`

### Key Files

- **Daily Pipeline**: `tools/news_ingestion/daily_pipeline.py`
- **Linear Model**: `tools/news_ingestion/train_linear_online.py`
- **XGBoost Model**: `tools/news_ingestion/train_xgboost.py`
- **Attribution**: `tools/news_ingestion/visualize_attribution.py`

## Next Steps

1. **Review Integration Points**: Identify which components need integration
2. **Test Integration**: Run test scripts and verify data flow
3. **Configure Automation**: Set up daily pipeline automation
4. **Monitor Performance**: Track attribution accuracy and model performance
5. **Iterate**: Refine based on feedback and requirements

---

*Last Updated: 2025-12-01*

