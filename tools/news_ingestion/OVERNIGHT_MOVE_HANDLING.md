# Overnight Move Handling in Yield Curve Prediction

## Problem Statement

Yield curve delta for day `t` includes:
- **Overnight moves**: Changes from day `t-1` market close (4 PM ET) to day `t` market open
- **Intraday moves**: Changes from day `t` market open to day `t` market close (4 PM ET)

When using same-day news (from day `t`, before 4 PM ET) to predict the yield delta for day `t`, we have a mismatch:
- The delta includes overnight moves that occurred **before** day `t` news was published
- Same-day news cannot explain overnight moves that happened the previous night

## Solution

The pipeline now handles this by using different news dates for training vs. prediction:

### For Training (Model Learning)
- **Uses previous day's (t-1) news** to predict day `t` delta
- This accounts for overnight moves in the delta, which can be influenced by t-1 news
- Example: News from 2025-12-03 → predicts delta for 2025-12-04 (includes overnight moves)

### For Prediction (Forecasting)
- **Uses same day's (t) news** to predict day `t+1` delta
- This is correct for forecasting: we use today's news to predict tomorrow's yield change
- Example: News from 2025-12-04 → predicts delta for 2025-12-05

## Implementation

The `train_linear_model_for_date()` function in `train_linear_online.py`:

1. **Calculates previous business day** (skipping weekends)
2. **Gets factor scores for prediction** (same day - `factor_scores_pred`)
3. **Gets factor scores for training** (previous day - `factor_scores_train`)
4. **Generates predictions** using same-day news (for saving/forecasting)
5. **Updates coefficients** using previous-day news (for training)

```python
# For prediction (forecasting): use same-day news
predictions = predict_yield_changes(date, coefficients, factor_scores_pred, intercepts)

# For training: use previous-day news to account for overnight moves
training_predictions = predict_yield_changes(date, coefficients, factor_scores_train, intercepts)
errors = {tenor: actuals[tenor] - training_predictions[tenor] for tenor in TENORS}
updated_coefficients = update_coefficients(date, coefficients, factor_scores_train, actuals, training_predictions)
```

## Benefits

1. **Better Training**: Model learns from news that can actually explain the yield changes (including overnight moves)
2. **Correct Forecasting**: Predictions use same-day news to forecast next-day moves (realistic scenario)
3. **No Look-Ahead Bias**: All news used is from before market close, preventing information leakage

## Example

**Date: 2025-12-04**

- **Yield delta for 2025-12-04**: Includes overnight moves (from 2025-12-03 4 PM to 2025-12-04 9:30 AM) + intraday moves (2025-12-04 9:30 AM to 4 PM)

- **For Training**:
  - Uses news from 2025-12-03 (before 4 PM ET)
  - Predicts delta for 2025-12-04
  - Updates model coefficients based on this relationship

- **For Prediction**:
  - Uses news from 2025-12-04 (before 4 PM ET)
  - Predicts delta for 2025-12-05
  - This is the forecast that would be used in production

## Verification

The implementation:
- ✅ Uses previous day news for training (accounts for overnight moves)
- ✅ Uses same day news for prediction (correct for forecasting)
- ✅ Maintains look-ahead bias prevention (all news before market close)
- ✅ Handles weekends correctly (finds previous business day)

## Related Files

- `train_linear_online.py`: Main implementation
- `daily_pipeline.py`: Calls training function
- `lookahead_bias_utils.py`: Ensures no post-market-close news is used

