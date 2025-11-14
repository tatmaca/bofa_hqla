# Historical News Ingestion

## Overview

The `ingest_historical.py` script runs news ingestion for past dates with strict timestamp controls to prevent look-back bias.

## Key Features

### [OK] No Look-Back Bias
- **Published Date Filter**: Only collects articles with `published_at <= target_date`
- **Fetched Date Simulation**: Sets `fetched_at` to target date (end of day UTC)
- **Verification**: Automatically checks for any articles with `published_at > target_date` and warns if found

### [OK] Timestamp Controls
- Articles are filtered by `published_at` timestamp
- `fetched_at` is set to the end of the target date (not current time)
- Cutoff time is calculated relative to target date, not current time

## Usage

```bash
# Ingest news for last 30 business days
python3 ingest_historical.py --days 30

# Ingest for specific date range
python3 ingest_historical.py --start-date 2025-10-01 --end-date 2025-10-31

# Ingest for single date
python3 ingest_historical.py --date 2025-10-15

# Dry run (see what would be done)
python3 ingest_historical.py --days 30 --dry-run
```

## How It Works

1. **Date Calculation**: Calculates end of target date in configured timezone, converts to UTC
2. **Cutoff Time**: Sets cutoff to `window_hours` before end of target date
3. **Article Filtering**: Only processes articles where `published_at <= end_of_day_utc`
4. **Timestamp Setting**: Sets `fetched_at` to end of target date
5. **Verification**: After ingestion, checks database for any articles with `published_at > target_date`

## Limitations

[WARN] **RSS Feeds**: Most RSS feeds only contain recent articles (last few days/weeks). Historical ingestion from RSS may yield limited results.

**Solutions**:
- Use news archive APIs if available
- Use historical news databases
- Collect news daily going forward to build historical dataset

## Example Output

```
======================================================================
HISTORICAL NEWS INGESTION
======================================================================
Dates to process: 30
Date range: 2025-09-26 to 2025-11-06
======================================================================

[1/30] Processing 2025-09-26...
======================================================================
INGESTING NEWS FOR 2025-09-26
======================================================================
>> Starting ingestion run for 2025-09-26
[OK] Processed RSS feed: ...
>> Done. New articles: 15
[VERIFY] [OK] No look-back bias detected (all articles published <= 2025-09-26)
```

## Database Verification

After running, verify no look-back bias:

```python
from db import get_conn
c = get_conn()

# Check for articles with published_at > fetched_at date
future_articles = c.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE DATE(fetched_at) = '2025-10-15'
    AND published_at IS NOT NULL
    AND DATE(published_at) > '2025-10-15'
""").fetchone()[0]

if future_articles > 0:
    print("WARNING: Look-back bias detected!")
```

## Integration with Training Pipeline

After running historical ingestion:

```bash
# 1. Bucket the historical news
python3 bucket_news.py --hours 24

# 2. Generate LLM analyses (if quota available)
export OPENAI_API_KEY="your-key"
python3 analyze_yield_impact.py --date 2025-10-15

# 3. Collect training data
python3 collect_training_data.py --start-date 2025-09-26 --end-date 2025-11-06

# 4. Train models
python3 train_xgboost.py --data training_data_*.json
```

