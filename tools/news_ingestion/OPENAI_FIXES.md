# OpenAI Integration Fixes

## Summary
Fixed issues with OpenAI API integration in the yield curve impact analysis pipeline. The pipeline now properly loads and passes the API key, provides better error handling, and ensures daily model training with accumulated data.

## Changes Made

### 1. Fixed API Key Loading (`daily_pipeline.py`)
- Added `get_openai_api_key()` function that checks:
  1. Environment variable `OPENAI_API_KEY`
  2. Config file `news_config.yaml` → `openai_api_key` field
- API key is now explicitly passed to `analyze_yield_impact()` function
- Added clear warnings when API key is missing

### 2. Improved Error Handling (`analyze_yield_impact.py`)
- Enhanced `call_openai_with_retry()` to detect specific error types:
  - API key/authentication errors → immediate fallback (no retries)
  - Quota/billing errors → immediate fallback (no retries)
  - Rate limit errors → longer wait times with exponential backoff
  - Other errors → standard retry logic
- Better error messages to help diagnose issues
- Validates OpenAI client initialization

### 3. Enhanced Training Data Collection (`collect_training_data.py`)
- Improved fallback detection to skip invalid predictions:
  - Checks for "Fallback" in reasoning
  - Checks for "unavailable" or "not configured" in overall summary
- More robust filtering of incomplete training examples

### 4. Better Model Training Feedback (`update_models_rolling.py`)
- Clearer messages about what's needed for training
- Explains that valid LLM predictions are required (not fallback)
- Shows current data count vs. required minimum

### 5. Progressive Model Training (`daily_pipeline.py`)
- Model training now tries multiple window sizes: 30 days → 14 days → 7 days
- Provides detailed feedback about what's needed
- Continues to accumulate data even if training can't run yet

### 6. Yield Curve Data Sync Improvements
- Better tracking of snapshot generation success
- Clearer status messages about data availability
- Handles cases where today's data isn't available yet

## How to Set Up OpenAI API Key

### Option 1: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

For persistent setup, add to your `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Option 2: Config File
Edit `tools/news_ingestion/news_config.yaml`:
```yaml
openai_api_key: "sk-your-api-key-here"
```

**Note:** The config file approach is less secure if the file is committed to git. Consider using environment variables or adding `news_config.yaml` to `.gitignore`.

## Verification

After setting the API key, test it:
```bash
cd tools/news_ingestion
python3 analyze_yield_impact.py --date 2025-11-13
```

You should see:
- `[OK] LLM analysis completed successfully` (not fallback)
- Real predictions with reasoning (not "Fallback: no analysis available")

## Daily Pipeline Flow

1. **News Ingestion** - Collects articles from RSS feeds and web crawling
2. **News Bucketing** - Categorizes articles using LLM (if API key available) or keywords
3. **Yield Curve Data** - Generates/updates yield curve snapshots
4. **LLM Analysis** - Analyzes news impact on yield curve (requires API key)
5. **Training Data Prep** - Prepares features for model training
6. **Model Training** - Trains XGBoost models on accumulated data (needs 7+ days of complete data)

## Requirements for Model Training

Model training requires **complete training examples** which means:
-  News articles bucketed
-  Valid LLM predictions (not fallback)
-  Yield curve snapshots with actual changes

Minimum: 7 days of complete data
Recommended: 30 days for better model performance

## Troubleshooting

### "No OpenAI API key found"
- Set `OPENAI_API_KEY` environment variable or add to `news_config.yaml`
- Verify the key is valid by testing with `analyze_yield_impact.py`

### "Analysis used fallback predictions"
- API key may be invalid or expired
- Check API quota/billing status
- Verify the key has access to `gpt-4o` model

### "Insufficient training data"
- Need at least 7 days with complete data (news + LLM predictions + snapshots)
- Continue running daily pipeline to accumulate data
- Check that API key is set so LLM predictions are real (not fallback)

### "Model training skipped - dependencies not available"
- Install XGBoost: `pip install 'numpy<2.0' xgboost scikit-learn`
- On macOS, may need: `brew install libomp` first

## Next Steps

1. Set your OpenAI API key (see above)
2. Run the daily pipeline: `python3 daily_pipeline.py`
3. Verify LLM analysis is working (not using fallback)
4. After 7+ days of complete data, models will start training automatically
5. Models improve daily as more training data accumulates

