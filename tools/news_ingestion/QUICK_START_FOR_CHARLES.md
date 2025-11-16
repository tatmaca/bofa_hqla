# Quick Start: News Data for Scenario Generation

**For:** Charles (Scenario Generation Team)  
**From:** Josh Li (News Ingestion)

---

## 🚀 Get News Data (30 seconds)

```bash
cd tools/news_ingestion
python3 export_news_for_scenario_gen.py
```

This creates `news_export_for_scenario_gen.json` with all collected news data.

---

## 📊 What You Get

The JSON file contains:
- **Daily bucket counts**: Articles per category (monetary_policy, credit_events, etc.)
- **Articles by bucket**: Title, summary, source, URL for each article
- **LLM yield predictions**: Yield curve impact predictions (if available)
- **Yield curve snapshots**: Current yield curve data (if available)

**8 News Buckets:**
1. `monetary_policy` - Fed decisions, rates
2. `economic_data` - GDP, employment, inflation
3. `geopolitical_events` - Wars, conflicts, elections
4. `market_sentiment` - Risk-on/off, volatility
5. `fiscal_policy` - Government spending, deficits
6. `credit_events` - Defaults, credit spreads
7. `commodity_prices` - Oil, gold, commodities
8. `other_general` - Other news

---

## 🔄 Run News Pipeline (if needed)

If you need to collect fresh news:

```bash
cd tools/news_ingestion
python3 daily_pipeline.py
```

**What it does:**
1. Collects news from RSS feeds
2. Categorizes into 8 buckets
3. Analyzes yield impact (optional)
4. Updates database

**Takes:** ~2-5 minutes

---

## 💡 Integration Example

```python
import json
from pathlib import Path

# Load news data
news_path = Path("tools/news_ingestion/news_export_for_scenario_gen.json")
with open(news_path) as f:
    news = json.load(f)

# Get today's news
today = "2025-11-15"
today_data = next((d for d in news["daily_data"] if d["date"] == today), None)

if today_data:
    # Use bucket counts as features
    monetary_count = today_data["bucket_counts"].get("monetary_policy", 0)
    credit_count = today_data["bucket_counts"].get("credit_events", 0)
    
    # Adjust scenario probabilities based on news
    if credit_count > 5:
        # Increase credit stress scenario probability
        pass
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `news_export_for_scenario_gen.json` | **Main export file** - use this |
| `INTEGRATION_GUIDE_FOR_CHARLES.md` | Detailed integration guide |
| `daily_pipeline.py` | Run to collect fresh news |

---

## ❓ Questions?

See `INTEGRATION_GUIDE_FOR_CHARLES.md` for detailed documentation.

