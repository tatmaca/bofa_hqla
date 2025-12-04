# Catch-Up Feature for Missing Data

## Overview

The catch-up feature automatically detects and fills in missing news/yield curve data when automation scripts fail or are not run. It checks up to 7 days back (configurable) and generates any missing snapshots or analyses.

## Usage

### Basic Usage

Check for missing data and fill it in:
```bash
cd tools/news_ingestion
python3 catch_up_missing_data.py
```

### Options

```bash
python3 catch_up_missing_data.py [OPTIONS]
```

**Options:**
- `--days-back N`: Number of days to look back (default: 7)
- `--skip-snapshots`: Skip generating missing snapshots
- `--skip-analyses`: Skip generating missing analyses
- `--skip-sync`: Skip syncing to database

### Examples

**Check last 3 days:**
```bash
python3 catch_up_missing_data.py --days-back 3
```

**Only generate snapshots (skip analyses):**
```bash
python3 catch_up_missing_data.py --skip-analyses
```

**Only generate analyses (skip snapshots):**
```bash
python3 catch_up_missing_data.py --skip-snapshots
```

## Integration with Status Check

The `check_status.py` script now automatically checks for missing data:

```bash
python3 check_status.py
```

This will show:
- Missing yield curve snapshots
- Missing news analyses
- Suggestion to run catch-up script

Example output:
```
[CHECK] MISSING DATA CHECK (last 7 days)
----------------------------------------------------------------------
  [WARN] Missing 2 yield curve snapshots:
     - 2025-11-09
     - 2025-11-10

  [WARN] Missing 1 news analyses:
     - 2025-11-10

  [TIP] Run catch-up script to fill missing data:
     python3 catch_up_missing_data.py --days-back 7
```

## How It Works

### 1. Detection Phase

The script:
1. Gets list of business days going back N days (default: 7)
2. Checks which yield curve snapshots are missing
3. Checks which news analyses are missing

### 2. Generation Phase

For each missing item:

**Yield Curve Snapshots:**
- Tries `auto_snapshot.py` first (handles data availability checks)
- Falls back to `build_snapshots.py` if auto_snapshot fails
- Syncs to database after generation

**News Analyses:**
- Requires yield curve snapshot to exist first
- Gets bucketed news for the date
- Generates LLM analysis
- Saves to `analyses/` directory

### 3. Summary

Reports:
- Number of missing items found
- Number successfully generated
- Number failed
- Number skipped (e.g., analysis skipped if no snapshot)

## Workflow

```
1. Check for missing data (up to 7 days back)
   ↓
2. Generate missing yield curve snapshots
   ↓
3. Sync snapshots to database
   ↓
4. Generate missing news analyses (if snapshots exist)
   ↓
5. Report summary
```

## When to Use

**Automated:**
- Can be added to daily pipeline as a safety check
- Can be scheduled to run periodically (e.g., weekly)

**Manual:**
- After fixing automation issues
- After system downtime
- When checking for data gaps
- Before training models (ensure complete data)

## Error Handling

- **Missing Treasury Data:** Script will skip dates where Treasury data is not available
- **Missing News:** Analysis will be skipped if no bucketed news exists
- **API Failures:** LLM analysis failures are logged but don't stop the script
- **Database Issues:** Warnings are shown but script continues

## Best Practices

1. **Run regularly:** Check for missing data weekly or after any automation failures
2. **Check status first:** Use `check_status.py` to see what's missing before running catch-up
3. **Review logs:** Check output to see which items were generated vs skipped
4. **Verify data:** After catch-up, verify generated files exist and are valid

## Integration with Daily Pipeline

The catch-up script can be integrated into the daily pipeline:

```python
# In daily_pipeline.py, add at the end:
from catch_up_missing_data import check_missing_data, generate_snapshot, generate_analysis

# Check for missing data from last 3 days
missing = check_missing_data(days_back=3)
if missing["missing_snapshots"] or missing["missing_analyses"]:
    print("[INFO] Found missing data, running catch-up...")
    # Run catch-up logic
```

## Troubleshooting

**Issue: "No Treasury data available"**
- Treasury data is typically published after market close (5 PM ET)
- Weekend dates won't have data
- Use `--skip-snapshots` if you only want analyses

**Issue: "No bucketed news found"**
- News needs to be ingested and bucketed first
- Run news ingestion for the date before generating analysis
- Use `--skip-analyses` if you only want snapshots

**Issue: "Database sync failed"**
- Database schema may not be initialized
- Run: `python3 -c "from db import init_db; init_db()"`
- Check database file exists and is writable

## Files

- **Script:** `tools/news_ingestion/catch_up_missing_data.py`
- **Status Check:** `tools/news_ingestion/check_status.py` (updated with missing data check)
- **Output:** 
  - Snapshots: `tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json`
  - Analyses: `tools/news_ingestion/analyses/yield_impact_YYYY-MM-DD.json`

