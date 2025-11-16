# News Ingestion Integration Guide for Scenario Generation

## Overview

The news ingestion system collects financial news, categorizes it into 8 buckets relevant to yield curve movements, and analyzes potential yield curve impacts. This data can enhance scenario generation by providing context about market events and news-driven risk factors.

---

## Quick Start: Export News Data

The easiest way to get news data for scenario generation is to export it to JSON:

```bash
cd tools/news_ingestion
python3 export_news_for_scenario_gen.py --start-date 2025-10-01 --end-date 2025-11-15
```

This creates `news_export_for_scenario_gen.json` with:
- Daily bucket counts (articles per category)
- Articles grouped by bucket (title, summary, source, URL)
- LLM yield impact predictions (if available)
- Yield curve snapshots (if available)

---

## Data Format

The exported JSON has this structure:

```json
{
  "metadata": {
    "export_date": "2025-11-15T...",
    "date_range": {"start": "2025-10-01", "end": "2025-11-15"},
    "total_dates": 30,
    "buckets": ["monetary_policy", "economic_data", ...]
  },
  "daily_data": [
    {
      "date": "2025-11-15",
      "bucket_counts": {
        "monetary_policy": 5,
        "economic_data": 3,
        ...
      },
      "articles_by_bucket": {
        "monetary_policy": [
          {
            "title": "Fed Signals Rate Cut...",
            "summary": "...",
            "source": "Reuters",
            "url": "https://...",
            "bucket_confidence": 0.95
          }
        ]
      },
      "llm_analysis": {
        "predictions": {
          "2y": {"direction": "down", "magnitude_bps": 3, "reasoning": "..."},
          "5y": {"direction": "down", "magnitude_bps": 2, "reasoning": "..."},
          ...
        }
      },
      "yield_curve_snapshot": {...}
    }
  ]
}
```

### News Buckets

1. **monetary_policy**: Fed decisions, interest rates, QE/QT
2. **economic_data**: GDP, employment, inflation (CPI/PCE), retail sales
3. **geopolitical_events**: Wars, conflicts, trade tensions, elections
4. **market_sentiment**: Risk-on/risk-off, volatility (VIX), equity movements
5. **fiscal_policy**: Government spending, deficits, debt ceiling, stimulus
6. **credit_events**: Corporate defaults, credit spreads, banking issues
7. **commodity_prices**: Oil, gold, commodity inflation, supply chains
8. **other_general**: Catch-all for other news

---

## Running the News Ingestion Pipeline

### Option 1: Run Full Daily Pipeline (Recommended)

The `daily_pipeline.py` script runs all steps automatically:

```bash
cd tools/news_ingestion
python3 daily_pipeline.py
```

**What it does:**
1. Collects news from RSS feeds and web crawlers
2. Categorizes articles into 8 buckets
3. Syncs yield curve data
4. Runs LLM analysis (if API key available)
5. Prepares training data
6. Updates ML models (if sufficient data)

**Output:**
- Articles stored in `news.db` SQLite database
- Bucketed articles with categories
- Analysis files in `analyses/yield_impact_YYYY-MM-DD.json`
- Logs in `logs/daily_pipeline_YYYY-MM-DD.log`

### Option 2: Run Individual Steps

If you need more control:

```bash
# Step 1: Collect news
python3 run_ingest.py

# Step 2: Categorize news into buckets
python3 bucket_news.py --hours 24 --batch-size 100

# Step 3: Analyze yield impact (optional, requires OpenAI API key)
export OPENAI_API_KEY="your-key-here"
python3 analyze_yield_impact.py --date 2025-11-15
```

### Option 3: Run for Specific Date

```bash
python3 daily_pipeline.py --date 2025-11-15
```

---

## Integration into Scenario Generation Pipeline

### Recommended Approach

1. **Export news data daily** (after news ingestion runs):
   ```bash
   python3 export_news_for_scenario_gen.py --start-date $(date -v-7d +%Y-%m-%d) --end-date $(date +%Y-%m-%d)
   ```

2. **Load JSON in your scenario generation script**:
   ```python
   import json
   from pathlib import Path
   
   news_data_path = Path("tools/news_ingestion/news_export_for_scenario_gen.json")
   with open(news_data_path) as f:
       news_data = json.load(f)
   
   # Get today's news
   today = "2025-11-15"
   today_news = next((d for d in news_data["daily_data"] if d["date"] == today), None)
   
   if today_news:
       # Use bucket counts as features
       monetary_policy_count = today_news["bucket_counts"].get("monetary_policy", 0)
       economic_data_count = today_news["bucket_counts"].get("economic_data", 0)
       
       # Use LLM predictions if available
       if today_news["llm_analysis"]:
           predictions = today_news["llm_analysis"]["predictions"]
           # Incorporate into scenario probabilities
   ```

3. **Incorporate into liquidity risk scenarios**:
   - High `monetary_policy` count → adjust Fed policy scenario probabilities
   - High `credit_events` count → increase credit stress scenario probability
   - High `geopolitical_events` count → increase risk-off scenario probability
   - Use LLM yield predictions to inform yield curve stress scenarios

### Example Integration

```python
# In scenario_gen/liquidity_risk/features.py or similar
def add_news_features(base_features, news_data_path):
    """Add news bucket counts as features for scenario generation."""
    with open(news_data_path) as f:
        news = json.load(f)
    
    # Get latest date
    latest = news["daily_data"][0] if news["daily_data"] else None
    if not latest:
        return base_features
    
    # Add news features
    base_features["news_monetary_policy"] = latest["bucket_counts"].get("monetary_policy", 0)
    base_features["news_credit_events"] = latest["bucket_counts"].get("credit_events", 0)
    base_features["news_geopolitical"] = latest["bucket_counts"].get("geopolitical_events", 0)
    
    return base_features
```

---

## Dependencies

### Required
```bash
cd tools/news_ingestion
pip install -r requirements.txt
```

### Optional (for LLM analysis)
- OpenAI API key (set `OPENAI_API_KEY` environment variable or add to `news_config.yaml`)
- Without API key, system still collects and buckets news, but won't generate yield predictions

### Database
The system uses SQLite (`news.db`). Initialize once:
```bash
python3 -c "from db import init_db; init_db()"
```

---

## Monitoring & Status

Check system status:
```bash
python3 check_status.py
```

Shows:
- Article counts
- Recent ingestion runs
- Missing data
- Health status

---

## File Locations

| File/Directory | Purpose |
|----------------|---------|
| `news.db` | SQLite database with all articles |
| `analyses/yield_impact_*.json` | LLM yield impact predictions |
| `logs/daily_pipeline_*.log` | Pipeline execution logs |
| `news_export_for_scenario_gen.json` | Exported data for scenario generation |

---

## Automation

The pipeline can run automatically via:
- **Cron** (Linux/macOS): See `DAILY_AUTOMATION.md`
- **Systemd timer** (Linux): See `DAILY_AUTOMATION.md`
- **LaunchAgent** (macOS): See `DAILY_AUTOMATION.md`

Recommended: Run daily at 6 AM (after market close) to capture previous day's news.

---

## Troubleshooting

### No articles collected
- Check internet connection
- Verify RSS feeds are accessible
- Check logs: `tail -f logs/daily_pipeline_*.log`

### Bucketing fails
- Check OpenAI API key (if using LLM bucketing)
- Verify database is initialized: `python3 -c "from db import init_db; init_db()"`

### Export returns empty data
- Verify date range has articles: `python3 check_status.py`
- Check database: `sqlite3 news.db "SELECT COUNT(*) FROM articles"`


