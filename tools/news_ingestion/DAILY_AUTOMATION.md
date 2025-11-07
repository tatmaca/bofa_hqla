# Daily Pipeline Automation Guide

## Overview

Since historical news collection isn't feasible (RSS feeds only contain recent articles), the system is designed to run daily going forward, collecting news and building up a historical dataset over time.

## Quick Start

### Manual Run

Run the daily pipeline manually:

```bash
cd tools/news_ingestion
python3 daily_pipeline.py
```

### Automated Daily Run

#### Option 1: Cron Job (Linux/macOS)

1. Make the runner script executable:
```bash
chmod +x tools/news_ingestion/run_daily.sh
```

2. Edit crontab:
```bash
crontab -e
```

3. Add a daily run (e.g., 6 AM every day):
```cron
0 6 * * * cd /path/to/bofa_hqla && /usr/bin/python3 tools/news_ingestion/run_daily.sh >> /path/to/bofa_hqla/tools/news_ingestion/logs/cron.log 2>&1
```

Or using the Python runner directly:
```cron
0 6 * * * cd /path/to/bofa_hqla/tools/news_ingestion && /usr/bin/python3 run_daily.sh
```

#### Option 2: Systemd Timer (Linux)

Create `/etc/systemd/system/news-ingestion.service`:
```ini
[Unit]
Description=Daily News Ingestion Pipeline
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/bofa_hqla/tools/news_ingestion
ExecStart=/usr/bin/python3 /path/to/bofa_hqla/tools/news_ingestion/run_daily.sh
```

Create `/etc/systemd/system/news-ingestion.timer`:
```ini
[Unit]
Description=Run news ingestion daily at 6 AM
Requires=news-ingestion.service

[Timer]
OnCalendar=daily
OnCalendar=06:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable news-ingestion.timer
sudo systemctl start news-ingestion.timer
```

#### Option 3: LaunchAgent (macOS)

Create `~/Library/LaunchAgents/com.news.ingestion.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.news.ingestion</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/bofa_hqla/tools/news_ingestion/run_daily.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/bofa_hqla/tools/news_ingestion</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/bofa_hqla/tools/news_ingestion/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/bofa_hqla/tools/news_ingestion/logs/launchd.error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.news.ingestion.plist
```

## What Gets Run Daily

The daily pipeline (`daily_pipeline.py`) runs 6 steps:

1. **News Ingestion** - Collects news from RSS feeds and web crawlers
2. **News Bucketing** - Categorizes articles into 8 buckets
3. **Yield Curve Sync** - Syncs yield curve snapshot data
4. **LLM Analysis** - Analyzes news impact on yield curve (if OpenAI API key available)
5. **Training Data Prep** - Prepares training records
6. **Model Training** - Retrains models with rolling 30-day window

## Monitoring

### Check Status

```bash
python3 check_status.py
```

Shows:
- Data counts (articles, yield dates, training records)
- Recent runs and their status
- Recent log files
- Health check

### View Logs

```bash
# Latest log
ls -t logs/daily_pipeline_*.log | head -1 | xargs cat

# All logs
ls -lh logs/
```

## Timestamp Handling

The system ensures **no look-back bias**:

- Articles are filtered by `published_at` timestamp
- `fetched_at` is set to the actual fetch time (not simulated)
- Only articles published in the last 24 hours are collected
- Each day's data is stored with proper timestamps

## Building Historical Dataset

As you run the pipeline daily:

1. **Week 1**: Collect 7 days of news + yield data → Can start training
2. **Week 2-4**: Build up to 30 days → Rolling window training begins
3. **Month 2+**: Models improve as more data accumulates

## Troubleshooting

### Pipeline Fails

1. Check logs: `cat logs/daily_pipeline_YYYY-MM-DD.log`
2. Check status: `python3 check_status.py`
3. Run manually: `python3 daily_pipeline.py`

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Database Issues

```bash
python3 -c "from db import init_db; init_db()"
```

### OpenAI Quota Issues

The pipeline will continue with fallback predictions if quota is exceeded. Check status:
```bash
python3 check_status.py
```

## Best Practices

1. **Run at consistent time**: Choose a time when markets are closed (e.g., 6 AM)
2. **Monitor daily**: Check status once a day to catch issues early
3. **Keep logs**: Logs are automatically saved to `logs/` directory
4. **Backup database**: Periodically backup `news.db` file
5. **Review failures**: Check logs if status shows failures

## Integration with Yield Curve Pipeline

The daily pipeline expects yield curve snapshots to be built separately. To automate both:

1. Run yield curve snapshot builder daily (before news ingestion)
2. Then run news ingestion pipeline

Or integrate both in a single cron job:
```cron
0 5 * * * cd /path/to/bofa_hqla && python3 tools/ust_curve/llm/daily.sh
0 6 * * * cd /path/to/bofa_hqla/tools/news_ingestion && python3 run_daily.sh
```

