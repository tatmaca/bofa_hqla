# Training Status

## Current Status

[OK] **Yield Curve Data**: 29 snapshots synced to database (2025-09-26 to 2025-11-06)
[OK] **Database Schema**: All tables created and ready
[WARN] **News Data**: Limited - only 1 date with bucketed news (2025-11-06)
[WARN] **Training Examples**: 1 example (need at least 7 for training)

## What's Ready

1. **Yield Curve Snapshots**: 29 business days of historical data
   - Location: `tools/ust_curve/llm/snapshots/`
   - Synced to: `yield_curve_daily` table

2. **Database**: All tables initialized
   - `yield_curve_daily`: 29 dates
   - `articles`: 305 articles
   - `news_yield_training`: Ready for data

3. **Scripts Created**:
   - `sync_snapshots_to_db.py`: Sync snapshots to database
   - `collect_training_data_simple.py`: Collect training data without LLM predictions
   - `generate_historical_snapshots.py`: Generate snapshots for past N days
   - `generate_summaries_plots.py`: Generate summaries and plots

## Next Steps to Train Models

### Option 1: Collect More Historical News (Recommended)
Run news ingestion for historical dates:
```bash
# Run daily pipeline for past dates (if you have historical news sources)
python3 daily_pipeline.py --date 2025-10-29
python3 daily_pipeline.py --date 2025-10-30
# ... etc
```

### Option 2: Use Current Data (Limited)
With only 1 training example, you can:
1. Wait for more news data to accumulate
2. Run the daily pipeline going forward to build up training data
3. Once you have 7+ examples, run:
   ```bash
   python3 collect_training_data_simple.py --start-date 2025-09-26 --end-date 2025-11-06
   python3 train_xgboost.py --data training_data_simple_*.json
   ```

### Option 3: Generate LLM Predictions (When Quota Restored)
Once OpenAI quota is restored:
```bash
export OPENAI_API_KEY="your-key"
# Generate analyses for dates with news
python3 analyze_yield_impact.py --date 2025-11-06
# Then collect training data with LLM features
python3 collect_training_data.py --start-date 2025-11-06 --end-date 2025-11-06
```

## Training Pipeline (When Ready)

Once you have 7+ training examples:

```bash
# 1. Collect training data
python3 collect_training_data_simple.py --start-date 2025-09-26 --end-date 2025-11-06

# 2. Train XGBoost models
python3 train_xgboost.py --data training_data_simple_*.json --threshold-mae 3.0

# 3. Or use rolling update
python3 update_models_rolling.py --days 30
```

## Files Generated

- **Snapshots**: 29 JSON files in `tools/ust_curve/llm/snapshots/`
- **Summaries**: 58 files (29 MD + 29 JSON) in `tools/ust_curve/llm/summaries/`
- **Plots**: 87 PNG files in `tools/ust_curve/llm/plots/`
- **Database**: All yield curve data synced

The system is ready - it just needs more historical news data to train on!

