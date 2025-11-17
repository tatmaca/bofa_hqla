# Quick Start Guide

## For New Users

1. **Read the main README**: Start with `tools/README.md` for overview
2. **Follow setup guide**: See `tools/news_ingestion/SETUP.md` for detailed setup
3. **Run tests**: Use `python3 test_system.py` to verify installation
4. **Set up automation**: See `DAILY_AUTOMATION.md` for daily runs

## File Organization

### Documentation (Start Here)
- `README.md` - Main documentation
- `SETUP.md` - Setup instructions
- `DAILY_AUTOMATION.md` - Automation guide
- `TESTING.md` - Testing guide

### Core Scripts (Daily Use)
- `daily_pipeline.py` - Run this daily
- `check_status.py` - Monitor system health

### Configuration
- `news_config.yaml` - Edit this to customize feeds/settings
- `schema.sql` - Database schema (reference)

### Generated Files (Gitignored)
- `news.db` - Your local database
- `models/*.pkl` - Trained models
- `logs/` - Daily run logs
- `analyses/*.json` - Analysis results

## Common Tasks

### First Time Setup
```bash
cd tools/news_ingestion
pip install -r requirements.txt
python3 -c "from db import init_db; init_db()"
python3 test_system.py
```

### Daily Run
```bash
python3 daily_pipeline.py
```

### Check Status
```bash
python3 check_status.py
```

### Troubleshooting
See `QUICK_FIX.md` for common issues.

