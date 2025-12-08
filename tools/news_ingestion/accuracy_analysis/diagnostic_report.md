# Prediction Accuracy Diagnostic Report

**Generated**: 2025-12-07T22:20:57.954309
**Dates Analyzed**: 2025-11-06, 2025-11-15, 2025-11-25, 2025-12-01

---

## Executive Summary

- ✓ Actual yield changes are in expected range
- ✓ Factor scores are in correct range [-2.5, +2.5]
- ✗ **CRITICAL**: Coefficients are too large (mean |value|: 3.45 bps, expected < 1.0 bps)
- ⚠ Found 1 potential training issues

---

## Detailed Findings

### 1. Data Quality

- Mean |actual yield change|: 4.8815 bps
- Max |actual yield change|: 9.8800 bps
- Expected range: 1-5 bps
- **Status**: ✓ Data quality is good

### 2. Factor Scores

- Max |factor score|: 2.5000
- Expected range: [-2.5, +2.5]
- Dates with out-of-range scores: 0
- **Status**: ✓ Factor scores are correct

### 3. Coefficients

- Mean |coefficient|: 3.4504 bps
- Max |coefficient|: 12.0000 bps
- Expected range: < 1.0 bps per unit factor
- Consistently large across dates: True
- **Status**: ✗ **CRITICAL ISSUE** - Coefficients are too large
  - This is the root cause of the 17.35x scale mismatch
  - Cold-start coefficients in `news_config.yaml` are 4-12 bps
  - Expected: 0.1-1.0 bps per unit factor

### 4. Training Process

- **Issues Found**:
  - Cold-start coefficients are too large (max: 12.0 bps, expected < 2.0 bps)

---

## Root Cause Analysis

Based on the diagnostic checks, the root cause of the low prediction accuracy is:

### Primary Issue: Coefficients Are Too Large

1. **Cold-Start Coefficients**: The initial coefficients in `news_config.yaml` are 4-12 bps per unit factor
   - Expected: 0.1-1.0 bps per unit factor
   - Actual: Up to 12 bps per unit factor
   - Ratio: 10-120x too large

2. **Impact**: When factor scores (typically 0-2.5) are multiplied by large coefficients (4-12 bps),
   predictions become 17.35x larger than actual yield changes

3. **Example Calculation**:
   - Factor: FED_TONE, score: 2.0, coefficient: 5.0 bps
   - Contribution: 2.0 × 5.0 = 10.0 bps
   - With multiple factors, total prediction can be 40+ bps
   - Actual yield changes are typically 1-6 bps

---

## Recommendations

### Immediate Actions

1. **Scale Down Cold-Start Coefficients**
   - Divide all coefficients in `news_config.yaml` by 10-15x
   - Target range: 0.1-1.0 bps per unit factor
   - Example: FED_TONE 10Y: 5.0 → 0.5 bps

2. **Reset Existing Coefficients**
   - Option A: Delete existing coefficients from database to force cold-start
   - Option B: Scale down existing coefficients in database

3. **Verify After Fix**
   - Run `trace_prediction_flow.py` to verify predictions are in reasonable range
   - Recalculate accuracy metrics

### Medium-Term Improvements

1. **Add Coefficient Validation**
   - Add sanity checks: coefficients should produce predictions in reasonable range
   - Flag when predictions exceed expected range

2. **Review Learning Rate**
   - Current: 0.05 (reasonable)
   - Monitor if coefficients drift over time

3. **Add Prediction Scale Checks**
   - Before saving predictions, check if they're in reasonable range
   - Warn if predictions are > 3 standard deviations from historical actuals

---

## Next Steps

1. Review and scale down coefficients in `news_config.yaml`
2. Reset or scale down existing coefficients in database
3. Re-run diagnostic checks to verify fixes
4. Regenerate predictions and recalculate accuracy
5. Monitor coefficient magnitudes over time
