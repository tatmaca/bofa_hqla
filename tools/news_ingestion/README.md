# News Ingestion & Yield Curve Prediction System

A comprehensive system for ingesting financial news, categorizing it into buckets, analyzing yield curve impacts, and training ML models to predict yield curve movements from news.

## Table of Contents

- [Quick Start](#quick-start)
- [System Overview](#system-overview)
- [Components](#components)
- [Daily Automation](#daily-automation)
- [Training Models](#training-models)
- [Configuration](#configuration)
- [Documentation](#documentation)

## Quick Start

### 1. Install Dependencies

```bash
cd tools/news_ingestion
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python3 -c "from db import init_db; init_db()"
```

### 3. Run Daily Pipeline

```bash
# Full automated pipeline
python3 daily_pipeline.py

# Or check status
python3 check_status.py
```

### 4. Set Up Daily Automation (Optional)

See [DAILY_AUTOMATION.md](DAILY_AUTOMATION.md) for cron/systemd/launchd setup.

For detailed setup instructions, see [SETUP.md](SETUP.md).

## System Overview

The system performs these steps daily:

1. **News Ingestion** - Collects news from RSS feeds and web crawlers
2. **News Bucketing** - Categorizes articles into 8 buckets
3. **Yield Curve Sync** - Syncs yield curve snapshot data
4. **LLM Analysis** - Analyzes news impact on yield curve (optional)
5. **Training Data Prep** - Prepares training records
6. **Model Training** - Retrains models with rolling 30-day window

## Components

### Core Scripts

| Script | Purpose |
|--------|---------|
| `daily_pipeline.py` | Main orchestration script - runs all steps |
| `run_ingest.py` | News ingestion (RSS + web crawl) |
| `bucket_news.py` | Categorize news into 8 buckets |
| `analyze_yield_impact.py` | LLM analysis of news impact |
| `train_linear_online.py` | Linear online learning model (ONYL) |
| `train_xgboost.py` | Train XGBoost models |
| `update_models_rolling.py` | Rolling window model updates |
| `check_status.py` | Monitor system health |

### Prediction & Accuracy Tracking

| Script | Purpose |
|--------|---------|
| `generate_scenario_curves.py` | Generate baseline + scenario yield curve predictions |
| `calculate_prediction_accuracy.py` | Calculate accuracy metrics (MAE, RMSE, R², etc.) |
| `batch_calculate_accuracy.py` | Batch calculate accuracy for date ranges |
| `generate_accuracy_report.py` | Generate comprehensive accuracy reports with visualizations |
| `visualize_accuracy.py` | Create accuracy visualizations (time series, heatmaps, etc.) |

### Data Collection

| Script | Purpose |
|--------|---------|
| `ingest_rss.py` | RSS feed ingestion |
| `crawl_web.py` | Web crawling with rate limiting |
| `sync_snapshots_to_db.py` | Sync yield curve snapshots to DB |
| `collect_training_data.py` | Collect training data with LLM features |
| `collect_training_data_simple.py` | Collect training data without LLM |

### Scenario-Based Predictions

The system generates 10 yield curve predictions daily:
- **1 baseline prediction** from the day's news
- **9 scenario-based predictions** using predefined economic scenarios

See [SCENARIO_CURVES_GUIDE.md](SCENARIO_CURVES_GUIDE.md) for details.

### Accuracy Tracking

The system tracks prediction accuracy over time with:
- **Metrics**: MAE, RMSE, R², directional accuracy, correlation
- **Visualizations**: Time series, heatmaps, per-tenor comparisons
- **Reports**: Comprehensive markdown and JSON reports

See accuracy reports in `accuracy_analysis/` directory.

### Utilities

| Script | Purpose |
|--------|---------|
| `test_system.py` | Comprehensive system tests |
| `fix_dependencies.py` | Fix NumPy/XGBoost compatibility |
| `run_daily.sh` | Daily runner script for automation |
| `visualize_attribution.py` | Generate attribution analysis visualizations |
| `compare_models.py` | Compare linear and XGBoost model alignment |

## News Buckets

The system categorizes news into 8 buckets:

1. **monetary_policy** - Fed decisions, interest rates, QE/QT
2. **economic_data** - GDP, employment, inflation data
3. **geopolitical_events** - Wars, trade tensions, elections
4. **market_sentiment** - Risk-on/off, volatility
5. **fiscal_policy** - Government spending, deficits, debt
6. **credit_events** - Defaults, credit spreads, banking
7. **commodity_prices** - Oil, gold, commodity inflation
8. **other_general** - Catch-all category

Uses LLM (GPT-4o-mini) for bucketing with keyword fallback.

## ML Models

The system trains 6 XGBoost models:
- **2y, 5y, 10y, 30y** - Yield predictions
- **2s10s, 2s30s** - Spread predictions

Models are retrained daily using a rolling 30-day window.

## Configuration

Edit `news_config.yaml` to:
- Add/remove RSS feeds
- Configure paywall domains
- Set rate limits
- Add OpenAI API key (optional)

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[DAILY_AUTOMATION.md](DAILY_AUTOMATION.md)** - Automation setup guide
- **[TESTING.md](TESTING.md)** - Testing guide
- **[TRAINING_STATUS.md](TRAINING_STATUS.md)** - Training status and next steps
- **[HISTORICAL_INGESTION.md](HISTORICAL_INGESTION.md)** - Historical data collection
- **[XGBOOST_TRAINING.md](XGBOOST_TRAINING.md)** - XGBoost training details
- **[QUICK_FIX.md](QUICK_FIX.md)** - Common issues and fixes

## File Structure

```
news_ingestion/
 README.md                    # This file
 SETUP.md                     # Setup guide
 DAILY_AUTOMATION.md          # Automation guide
 requirements.txt             # Python dependencies
 news_config.yaml            # Configuration
 schema.sql                   # Database schema

 Core Scripts
 daily_pipeline.py           # Main pipeline
 run_ingest.py               # Ingestion orchestrator
 bucket_news.py              # News bucketing
 analyze_yield_impact.py    # LLM analysis
 train_xgboost.py            # Model training
 update_models_rolling.py    # Rolling updates
 check_status.py             # Status monitoring

 Data Collection
 ingest_rss.py               # RSS ingestion
 crawl_web.py                # Web crawling
 sync_snapshots_to_db.py     # Sync yield data
 collect_training_data.py    # Training data (with LLM)
 collect_training_data_simple.py  # Training data (simple)

 Utilities
 test_system.py              # System tests
 fix_dependencies.py         # Dependency fixes
 run_daily.sh                # Daily runner

 Database
 db.py                       # Database functions
 schema.sql                  # Schema definition

 Output Directories
     analyses/               # LLM analysis results
     models/                 # Trained model files
     logs/                   # Daily run logs
```

## Monitoring

Check system status:
```bash
python3 check_status.py
```

**Comprehensive health check:**
```bash
python3 health_check.py
```

This checks:
- Database health and data counts
- Recent pipeline runs
- Recent data collection
- Log files
- Model file updates
- Automation setup
- Dependency availability

View recent logs:
```bash
ls -t logs/daily_pipeline_*.log | head -1 | xargs cat
```

##  Testing

Run comprehensive tests:
```bash
python3 test_system.py
```

See [TESTING.md](TESTING.md) for detailed testing guide.

## [LOG] Notes

- Database file (`news.db`) is gitignored - each user maintains their own
- LLM features require OpenAI API key (set via `OPENAI_API_KEY` env var)
- ML training requires at least 7 days of data
- Models improve automatically as more data accumulates

