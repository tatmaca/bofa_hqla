# News Ingestion & Yield Curve Analysis System

A comprehensive system for ingesting financial news, categorizing it into buckets, analyzing yield curve impacts, and training ML models to predict yield curve movements from news.

## Features

- **Optimized News Ingestion**: Parallel RSS feed processing and async web crawling
- **News Bucketing**: Categorizes news into 8 buckets relevant to yield curves (monetary policy, economic data, geopolitical events, etc.)
- **LLM-Powered Analysis**: Uses GPT models to analyze news impact on yield curve tenors
- **ML Model Training**: Trains regression models to map news buckets to yield curve changes
- **Daily Pipeline**: Automated end-to-end workflow for daily runs
- **Paywall Handling**: Gracefully handles paywalled sites with metadata-only mode

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
# Full pipeline (ingestion → bucketing → analysis → training)
python3 daily_pipeline.py

# Or run components individually:
python3 run_ingest.py          # News ingestion
python3 bucket_news.py         # Categorize news
python3 analyze_yield_impact.py # LLM analysis
python3 train_models.py        # Train ML models
```

## Components

### News Ingestion (`ingest_rss.py`, `crawl_web.py`)

- Parallel RSS feed parsing
- Async web crawling with rate limiting
- Paywall detection and metadata-only mode
- 24-hour window filtering

### News Bucketing (`bucket_news.py`)

8 news categories:
1. **monetary_policy**: Fed decisions, interest rates, QE/QT
2. **economic_data**: GDP, employment, inflation data
3. **geopolitical_events**: Wars, trade tensions, elections
4. **market_sentiment**: Risk-on/off, volatility
5. **fiscal_policy**: Government spending, deficits, debt
6. **credit_events**: Defaults, credit spreads, banking
7. **commodity_prices**: Oil, gold, commodity inflation
8. **other_general**: Catch-all category

Uses LLM (GPT-4o-mini) for bucketing with keyword fallback.

### Yield Impact Analysis (`analyze_yield_impact.py`)

LLM agent that:
- Analyzes bucketed news
- Predicts impact on 2y, 5y, 10y, 30y tenors
- Analyzes spread movements (2s10s, 2s30s)
- Provides reasoning for predictions

### ML Model Training (`train_models.py`)

Trains regression models (Ridge, Lasso, Random Forest, Gradient Boosting) to predict:
- Yield changes for each tenor
- Spread changes

Requires at least 7 days of aligned news + yield curve data.

### Daily Pipeline (`daily_pipeline.py`)

Orchestrates the complete workflow:
1. News ingestion (RSS + web crawl)
2. News bucketing
3. Yield curve data sync
4. LLM impact analysis
5. Training data preparation
6. Model training/retraining

## Configuration

Edit `news_config.yaml` to:
- Add/remove RSS feeds
- Configure paywall domains
- Set rate limits
- Add OpenAI API key (optional, for LLM features)

## Database Schema

- `articles`: News articles with buckets
- `ingestion_runs`: Daily run tracking
- `yield_curve_daily`: Yield curve snapshots
- `news_yield_training`: Training data (news buckets → yield changes)

## Usage Examples

### Bucket News from Last 24 Hours

```bash
python3 bucket_news.py --hours 24 --batch-size 50
```

### Analyze Yield Impact for Specific Date

```bash
python3 analyze_yield_impact.py --date 2025-11-03
```

### Train Models

```bash
python3 train_models.py --min-days 7
```

### Check Bucket Counts

```python
from bucket_news import get_bucket_counts
import json
print(json.dumps(get_bucket_counts(), indent=2))
```

## Requirements

- Python 3.7+
- See `requirements.txt` for full list
- OpenAI API key (optional, for LLM features)
- scikit-learn (optional, for ML training)

## Notes

- Database file (`news.db`) is gitignored - each user maintains their own
- LLM features require OpenAI API key (set via `OPENAI_API_KEY` env var or config)
- ML training requires at least 7 days of data
- Paywalled sites are handled gracefully with metadata-only mode

