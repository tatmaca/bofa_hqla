# Automated Yield Curve Snapshot Generator

## Overview

The `auto_snapshot.py` script automatically checks for new Treasury yield curve data and generates snapshots, summaries, and plots. It's designed to be run daily (e.g., after market close or in the morning) to keep yield curve data up-to-date.

## Features

- **Automatic Data Detection**: Checks for new Treasury data for the target date (or most recent available date)
- **Smart Snapshot Generation**: Only generates snapshots if new data is available
- **Complete Pipeline**: Generates snapshots, summaries, plots, and syncs to database
- **Integration Ready**: Integrated into the daily news ingestion pipeline

## Usage

### Basic Usage

Check for new data and generate snapshot for today:
```bash
cd /path/to/bofa_hqla
python3 tools/ust_curve/llm/auto_snapshot.py
```

### Command-Line Options

```bash
python3 tools/ust_curve/llm/auto_snapshot.py [OPTIONS]
```

**Options:**
- `--target-date YYYY-MM-DD`: Target date (defaults to today)
- `--lookback N`: Days to look back for data (default: 5)
- `--force`: Force regeneration even if snapshot exists
- `--skip-plot`: Skip plot generation
- `--skip-summary`: Skip summary generation
- `--skip-sync`: Skip database sync

### Examples

**Check for today's data:**
```bash
python3 tools/ust_curve/llm/auto_snapshot.py
```

**Check for specific date:**
```bash
python3 tools/ust_curve/llm/auto_snapshot.py --target-date 2025-11-06
```

**Force regeneration:**
```bash
python3 tools/ust_curve/llm/auto_snapshot.py --force
```

**Skip plots and summaries (faster, just snapshot):**
```bash
python3 tools/ust_curve/llm/auto_snapshot.py --skip-plot --skip-summary
```

## How It Works

1. **Check Latest Snapshot**: Determines the most recent snapshot in the database
2. **Check Treasury Data**: Fetches Treasury data for the target date (with lookback)
3. **Generate Snapshot**: If new data is available, generates snapshot JSON
4. **Generate Summary**: Creates Markdown and JSON summaries
5. **Generate Plots**: Creates yield curve visualization plots
6. **Sync to Database**: Syncs data to the news ingestion database

## Integration with Daily Pipeline

The script is automatically integrated into the daily news ingestion pipeline (`daily_pipeline.py`). When the daily pipeline runs:

1. It checks for new Treasury data using `auto_snapshot.py`
2. Generates snapshots if new data is available
3. Syncs yield curve data to the database
4. Uses the data for training and analysis

## Treasury Data Availability

**Important**: Treasury yield curve data is typically published **after market close** (around 5 PM ET). 

- If you run the script during market hours, it will use the most recent available data (typically yesterday)
- If you run it after market close, it will use today's data (if available)
- The script automatically handles this by looking back up to 5 days (configurable)

## Output Files

The script generates files in the following locations:

- **Snapshots**: `tools/ust_curve/llm/snapshots/curve_snapshot_YYYY-MM-DD.json`
- **Summaries**: `tools/ust_curve/llm/summaries/curve_summary_YYYY-MM-DD.md`
- **LLM JSON**: `tools/ust_curve/llm/summaries/curve_llm_YYYY-MM-DD.json`
- **Plots**: `tools/ust_curve/llm/plots/ust_curve_YYYY-MM-DD.png`

## Automation

### Manual Run

Run manually whenever you want to check for new data:
```bash
python3 tools/ust_curve/llm/auto_snapshot.py
```

### Daily Automation

The script is integrated into the daily pipeline, which runs automatically via LaunchAgent (macOS) or cron (Linux). The daily pipeline will:

1. Check for new Treasury data
2. Generate snapshots if available
3. Sync to database
4. Use for training and analysis

### Scheduled Run (Optional)

You can also schedule the script to run independently:

**Cron (Linux/macOS):**
```cron
0 18 * * 1-5 cd /path/to/bofa_hqla && python3 tools/ust_curve/llm/auto_snapshot.py
```
(Runs at 6 PM on weekdays)

**LaunchAgent (macOS):**
Create `~/Library/LaunchAgents/com.yield.curve.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yield.curve</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/bofa_hqla/tools/ust_curve/llm/auto_snapshot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/bofa_hqla</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

## Troubleshooting

### "No Treasury data available"

- Treasury data is published after market close
- Try running after 5 PM ET
- The script will use the most recent available data

### "Snapshot already exists"

- The snapshot for that date already exists
- Use `--force` to regenerate
- Or wait for new data (next business day)

### "Exception syncing to database"

- Database may not be initialized
- Run: `cd tools/news_ingestion && python3 -c "from db import init_db; init_db()"`
- Or the script will try to initialize automatically

## See Also

- `daily_pipeline.py`: Daily news ingestion pipeline (includes auto-snapshot)
- `build_snapshots.py`: Manual snapshot generation
- `DAILY_AUTOMATION.md`: Daily pipeline automation guide

