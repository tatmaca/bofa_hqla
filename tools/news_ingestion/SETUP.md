# Setup Guide

Complete setup instructions for the News Ingestion & Yield Curve Prediction System.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git (for cloning repository)

## Step-by-Step Setup

### 1. Navigate to Directory

```bash
cd tools/news_ingestion
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If you encounter issues with XGBoost on macOS, see [QUICK_FIX.md](QUICK_FIX.md).

### 3. Initialize Database

```bash
python3 -c "from db import init_db; init_db()"
```

This creates the SQLite database (`news.db`) with all required tables.

### 4. Configure Settings (Optional)

Edit `news_config.yaml` to:
- Add/remove RSS feeds
- Configure paywall domains
- Set rate limits
- Add OpenAI API key (optional, for LLM features)

### 5. Set OpenAI API Key (Optional)

If you want to use LLM features:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or add it to `news_config.yaml`:
```yaml
openai_api_key: "your-api-key-here"
```

### 6. Test Installation

```bash
python3 test_system.py
```

This runs comprehensive tests to verify everything is working.

### 7. Run First Pipeline

```bash
python3 daily_pipeline.py
```

This will:
- Collect news from RSS feeds
- Bucket articles into categories
- Sync yield curve data (if available)
- Run LLM analysis (if API key set)
- Prepare training data
- Train models (if enough data)

## Verify Setup

Check system status:
```bash
python3 check_status.py
```

Expected output:
- Database initialized [OK]
- Articles table exists [OK]
- All components importable [OK]

## Next Steps

1. **Set up daily automation** - See [DAILY_AUTOMATION.md](DAILY_AUTOMATION.md)
2. **Build yield curve snapshots** - See `../ust_curve/README.md`
3. **Monitor daily runs** - Use `check_status.py`

## Troubleshooting

### Import Errors

```bash
pip install -r requirements.txt
```

### XGBoost Issues (macOS)

```bash
python3 fix_dependencies.py
```

Or manually:
```bash
brew install libomp
pip install "numpy<2.0" xgboost
```

### Database Errors

```bash
python3 -c "from db import init_db; init_db()"
```

### OpenAI API Issues

- Check API key is set: `echo $OPENAI_API_KEY`
- Verify quota: Check OpenAI dashboard
- System will use fallback if API unavailable

See [QUICK_FIX.md](QUICK_FIX.md) for more troubleshooting.

## File Structure After Setup

```
news_ingestion/
├── news.db                    # SQLite database (created)
├── models/                    # Model files (created when training)
├── analyses/                  # Analysis results (created)
└── logs/                      # Log files (created)
```

## Requirements Summary

### Required
- Python 3.7+
- feedparser
- trafilatura
- aiolimiter
- beautifulsoup4
- sqlite3 (usually included)

### Optional (for ML)
- numpy<2.0
- scikit-learn
- xgboost

### Optional (for LLM)
- openai

See `requirements.txt` for complete list.

