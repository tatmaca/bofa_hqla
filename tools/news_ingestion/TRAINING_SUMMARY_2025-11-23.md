# XGBoost Training and Comparison Summary - 2025-11-23

## Training Results

### Models Trained
- **Date**: 2025-11-23
- **Training Data**: `training_data_rolling_30d.json` (9 samples)
- **Features**: 34 features (LLM predictions + news buckets)
- **Note**: Training data does not include factor features (collected before factor integration)

### Model Performance
- **All 6 targets trained**: 2y, 5y, 10y, 30y, 2s10s, 2s30s
- **Mean MAE**: 0.019 bps (excellent, but dataset is very small)
- **Threshold Met**: Yes (5.0 bps threshold)
- **Training Time**: Completed within timeout (300s)

### SHAP Analysis
- **SHAP values computed** for all models
- **Top features** (consistent across all models):
  1. `10y_pred_direction`
  2. `10y_pred_magnitude`
  3. `10y_pred_signed`
  4. `2s10s_pred_direction`
  5. `2s10s_pred_magnitude`

### Files Generated
- Models: `models/xgb_{target}_2025-11-23.pkl` (6 files)
- SHAP data: `models/xgb_{target}_2025-11-23_shap.json` (6 files)
- Metadata: `models/xgb_metadata_2025-11-23.json`
- Evaluation: `models/evaluation_2025-11-23.json`

## Comparison Results

### Linear vs XGBoost SHAP
- **Date**: 2025-11-23
- **Tenors Compared**: 4 (2Y, 5Y, 10Y, 30Y)
- **Alignment Score**: 0.000 (no overlap - training data lacks factor features)
- **Common Factors**: 0

**Note**: The training data used doesn't include factor features (`factor_*`), so comparison shows no alignment. To get proper comparison:
1. Collect new training data with factor scores included
2. Retrain models with factor features
3. Run comparison again

## Visualizations Generated

### Factor Attribution (Linear Model)
- `factor_attribution_2025-11-23.png` - Bar charts by tenor
- `factor_heatmap_2025-11-23.png` - Heatmap across tenors
- `attribution_report_2025-11-23.json` - Detailed data

### Comparison Report
- `model_comparison_2025-11-23.json` - Alignment metrics

## Key Insights

1. **XGBoost Models**: Successfully trained with SHAP integration
2. **SHAP Features**: LLM prediction features are most important
3. **Factor Features**: Not in current training data (need to collect new data)
4. **Timeout Handling**: Implemented and working (300s training, 60-120s SHAP)

## Next Steps

1. **Collect Training Data with Factors**:
   ```bash
   python3 collect_training_data.py --start-date 2025-11-06 --end-date 2025-11-23 --output training_data_with_factors.json
   ```

2. **Retrain with Factor Features**:
   ```bash
   python3 train_xgboost_incremental.py --data training_data_with_factors.json
   ```

3. **Run Comparison Again**:
   ```bash
   python3 compare_models.py --date 2025-11-23
   ```

## Timeout Handling

- **Training Timeout**: 300 seconds (5 minutes)
- **SHAP Timeout**: 60-120 seconds (adaptive based on dataset size)
- **Graceful Handling**: Timeouts are caught and reported without crashing

