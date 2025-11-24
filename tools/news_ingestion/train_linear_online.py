#!/usr/bin/env python3
"""
Linear Online Learning Model (ONYL - Online News→Yield Learner)
Implements the linear online learning algorithm from the PDFs.

Algorithm:
- Prediction: Δy_t,k = Σ(B_k,f × x_t,f) + b_k
- Error: e_t,k = Δy_obs - Δy_pred
- Update: B_k,f ← B_k,f + η × w_t,f × e_t,k × x_t,f
- Weight: w_t,f = 0.3 if |x_t,f| < 0.3, else scale so Σ|w_t,f × x_t,f| ≤ 3.0
- Clip: |ΔB_k,f| ≤ ΔB_max (0.8 bps)
- Sign guards: Enforce economic constraints
- Smoothing: B_k,f ← (1-γ)×B_k,f + (γ/2)×(B_k-1,f + B_k+1,f) where γ=0.2
"""

import os
import sys
import json
import yaml
import datetime as dt
from datetime import timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

# Tenors: [3M, 2Y, 5Y, 10Y, 30Y]
TENORS = ["3M", "2Y", "5Y", "10Y", "30Y"]
TENOR_ORDER = {"3M": 0, "2Y": 1, "5Y": 2, "10Y": 3, "30Y": 4}

CONFIG_PATH = Path(__file__).parent / "news_config.yaml"

def load_config() -> Dict:
    """Load configuration from YAML file."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def initialize_coefficients(date: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """
    Initialize coefficients from cold-start config or load from database.
    Returns {tenor: {factor_name: coefficient_bps}}
    """
    config = load_config()
    cold_start = config.get("linear_model_cold_start", {})
    
    # Extract hyperparameters
    learning_rate = cold_start.get("learning_rate", 0.05)
    forgetting_factor = cold_start.get("forgetting_factor", 0.98)
    max_daily_coef_change = cold_start.get("max_daily_coef_change", 0.8)
    smoothing_gamma = cold_start.get("smoothing_gamma", 0.2)
    
    # Initialize coefficients structure
    coefficients = {tenor: {} for tenor in TENORS}
    
    # Try to load from database first (if date provided and exists)
    if date:
        conn = get_conn()
        c = conn.cursor()
        
        rows = c.execute("""
            SELECT tenor, factor_name, coefficient_bps
            FROM linear_model_coefficients
            WHERE date = ?
        """, (date,)).fetchall()
        
        conn.close()
        
        if rows:
            # Load from database
            for row in rows:
                tenor = row["tenor"]
                factor_name = row["factor_name"]
                coefficient_bps = row["coefficient_bps"]
                if tenor in coefficients:
                    coefficients[tenor][factor_name] = coefficient_bps
            return coefficients
    
    # Otherwise, use cold-start coefficients
    for factor_name, tenor_coefs in cold_start.items():
        if factor_name in ["learning_rate", "forgetting_factor", "max_daily_coef_change", "smoothing_gamma"]:
            continue
        
        if isinstance(tenor_coefs, dict):
            for tenor, bps_value in tenor_coefs.items():
                if tenor in coefficients:
                    coefficients[tenor][factor_name] = float(bps_value)
    
    return coefficients

def get_daily_factor_scores(date: str) -> Dict[str, float]:
    """Get daily factor scores for a given date."""
    conn = get_conn()
    c = conn.cursor()
    
    rows = c.execute("""
        SELECT factor_name, factor_score
        FROM daily_factor_scores
        WHERE date = ?
    """, (date,)).fetchall()
    
    conn.close()
    
    return {row["factor_name"]: row["factor_score"] for row in rows}

def predict_yield_changes(date: str, coefficients: Dict[str, Dict[str, float]], 
                          factor_scores: Optional[Dict[str, float]] = None,
                          intercepts: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Predict yield changes using linear model: Δy_t,k = Σ(B_k,f × x_t,f) + b_k
    
    Args:
        date: Date string
        coefficients: {tenor: {factor_name: coefficient_bps}}
        factor_scores: {factor_name: factor_score} (if None, loads from DB)
        intercepts: {tenor: intercept_bps} (if None, loads from DB)
    
    Returns:
        {tenor: predicted_delta_bps}
    """
    if factor_scores is None:
        factor_scores = get_daily_factor_scores(date)
    
    if intercepts is None:
        intercepts = get_intercepts(date)
    
    predictions = {}
    
    for tenor in TENORS:
        pred = intercepts.get(tenor, 0.0)  # Start with intercept
        
        for factor_name, factor_score in factor_scores.items():
            if factor_name in coefficients.get(tenor, {}):
                coef = coefficients[tenor][factor_name]
                pred += coef * factor_score
        
        predictions[tenor] = pred
    
    return predictions

def get_actual_yield_changes(date: str) -> Optional[Dict[str, float]]:
    """Get actual yield changes from database."""
    conn = get_conn()
    c = conn.cursor()
    
    row = c.execute("""
        SELECT delta_zeros_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (date,)).fetchone()
    
    conn.close()
    
    if not row:
        return None
    
    try:
        delta_zeros = json.loads(row["delta_zeros_pct"])
        # Convert to our tenor format
        # Note: delta_zeros_pct is in percentage points (0.01 = 1 bp), so multiply by 100 to get bps
        actuals = {}
        for key, value in delta_zeros.items():
            # Handle different key formats
            key_upper = key.upper()
            
            # Map to our tenor format
            if key_upper == "3M":
                actuals["3M"] = float(value) * 100  # Convert % points to bps
            elif key_upper == "2Y" or (key_upper == "2Y" and "2y" in key.lower()):
                actuals["2Y"] = float(value) * 100
            elif key_upper == "5Y" or (key_upper == "5Y" and "5y" in key.lower()):
                actuals["5Y"] = float(value) * 100
            elif key_upper == "10Y" or (key_upper == "10Y" and "10y" in key.lower()):
                actuals["10Y"] = float(value) * 100
            elif key_upper == "30Y" or (key_upper == "30Y" and "30y" in key.lower()):
                actuals["30Y"] = float(value) * 100
            elif key.lower() == "2y":
                actuals["2Y"] = float(value) * 100
            elif key.lower() == "5y":
                actuals["5Y"] = float(value) * 100
            elif key.lower() == "10y":
                actuals["10Y"] = float(value) * 100
            elif key.lower() == "30y":
                actuals["30Y"] = float(value) * 100
        
        # Note: 3M may not be in old snapshots - that's OK, model will use available tenors
        return actuals
    except:
        return None

def get_intercepts(date: Optional[str] = None) -> Dict[str, float]:
    """Get intercepts (bias terms) from database or initialize to 0."""
    intercepts = {tenor: 0.0 for tenor in TENORS}
    
    if date:
        conn = get_conn()
        c = conn.cursor()
        
        rows = c.execute("""
            SELECT tenor, intercept_bps
            FROM linear_model_intercepts
            WHERE date = ?
        """, (date,)).fetchall()
        
        conn.close()
        
        for row in rows:
            tenor = row["tenor"]
            if tenor in intercepts:
                intercepts[tenor] = row["intercept_bps"]
    
    return intercepts

def compute_update_weights(factor_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Compute update weights w_t,f.
    - If |x_t,f| < 0.3, set w_t,f = 0.3
    - Otherwise, scale so Σ|w_t,f × x_t,f| ≤ 3.0
    """
    weights = {}
    
    # First pass: set weights for small factors
    large_factors = {}
    small_sum = 0.0
    
    for factor_name, factor_score in factor_scores.items():
        abs_score = abs(factor_score)
        if abs_score < 0.3:
            weights[factor_name] = 0.3
            small_sum += 0.3 * abs_score
        else:
            large_factors[factor_name] = abs_score
    
    # Second pass: scale large factors
    remaining_budget = max(0.0, 3.0 - small_sum)
    
    if large_factors:
        large_sum = sum(large_factors.values())
        if large_sum > 0:
            scale = remaining_budget / large_sum if large_sum > 0 else 0.0
            for factor_name, abs_score in large_factors.items():
                weights[factor_name] = scale
        else:
            for factor_name in large_factors:
                weights[factor_name] = 1.0
    else:
        # All factors are small
        for factor_name in factor_scores:
            if factor_name not in weights:
                weights[factor_name] = 0.3
    
    return weights

def apply_sign_guards(coefficients: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Apply sign guards based on economic constraints.
    Projects coefficients back to 0 if they violate constraints.
    """
    config = load_config()
    sign_guards = config.get("linear_model_sign_guards", {})
    
    for factor_name, guard in sign_guards.items():
        if guard == "non_negative":
            # All tenors must be ≥ 0
            for tenor in TENORS:
                if factor_name in coefficients.get(tenor, {}):
                    if coefficients[tenor][factor_name] < 0:
                        coefficients[tenor][factor_name] = 0.0
        elif guard == "non_positive":
            # All tenors must be ≤ 0
            for tenor in TENORS:
                if factor_name in coefficients.get(tenor, {}):
                    if coefficients[tenor][factor_name] > 0:
                        coefficients[tenor][factor_name] = 0.0
        elif isinstance(guard, dict):
            # Per-tenor constraints
            for tenor, constraint in guard.items():
                if tenor in coefficients and factor_name in coefficients[tenor]:
                    if "min" in constraint:
                        min_val = constraint["min"]
                        if coefficients[tenor][factor_name] < min_val:
                            coefficients[tenor][factor_name] = min_val
                    if "max" in constraint:
                        max_val = constraint["max"]
                        if coefficients[tenor][factor_name] > max_val:
                            coefficients[tenor][factor_name] = max_val
    
    return coefficients

def smooth_across_maturities(coefficients: Dict[str, Dict[str, float]], 
                            gamma: float = 0.2) -> Dict[str, Dict[str, float]]:
    """
    Smooth coefficients across maturities: B_k,f ← (1-γ)×B_k,f + (γ/2)×(B_k-1,f + B_k+1,f)
    Skips ends (3M, 30Y).
    """
    smoothed = {tenor: {} for tenor in TENORS}
    
    # Get all factor names
    all_factors = set()
    for tenor_coefs in coefficients.values():
        all_factors.update(tenor_coefs.keys())
    
    for factor_name in all_factors:
        for i, tenor in enumerate(TENORS):
            if i == 0 or i == len(TENORS) - 1:
                # End points: no smoothing
                smoothed[tenor][factor_name] = coefficients.get(tenor, {}).get(factor_name, 0.0)
            else:
                # Middle points: smooth with neighbors
                current = coefficients.get(tenor, {}).get(factor_name, 0.0)
                prev_tenor = TENORS[i - 1]
                next_tenor = TENORS[i + 1]
                prev_val = coefficients.get(prev_tenor, {}).get(factor_name, 0.0)
                next_val = coefficients.get(next_tenor, {}).get(factor_name, 0.0)
                
                smoothed[tenor][factor_name] = (1 - gamma) * current + (gamma / 2) * (prev_val + next_val)
    
    return smoothed

def update_coefficients(date: str, 
                       coefficients: Dict[str, Dict[str, float]],
                       factor_scores: Dict[str, float],
                       actual_changes: Dict[str, float],
                       predictions: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Update coefficients using online learning rule:
    B_k,f ← B_k,f + η × w_t,f × e_t,k × x_t,f
    
    Args:
        date: Date string
        coefficients: Current coefficients {tenor: {factor_name: coefficient_bps}}
        factor_scores: Factor scores {factor_name: factor_score}
        actual_changes: Actual yield changes {tenor: delta_bps}
        predictions: Predicted yield changes {tenor: delta_bps}
    
    Returns:
        Updated coefficients
    """
    config = load_config()
    cold_start = config.get("linear_model_cold_start", {})
    learning_rate = cold_start.get("learning_rate", 0.05)
    max_daily_coef_change = cold_start.get("max_daily_coef_change", 0.8)
    smoothing_gamma = cold_start.get("smoothing_gamma", 0.2)
    
    # Compute errors
    errors = {}
    for tenor in TENORS:
        if tenor in actual_changes and tenor in predictions:
            errors[tenor] = actual_changes[tenor] - predictions[tenor]
        else:
            errors[tenor] = 0.0
    
    # Compute update weights
    weights = compute_update_weights(factor_scores)
    
    # Update coefficients
    updated_coefficients = {tenor: {} for tenor in TENORS}
    
    for tenor in TENORS:
        error = errors[tenor]
        
        for factor_name, factor_score in factor_scores.items():
            current_coef = coefficients.get(tenor, {}).get(factor_name, 0.0)
            weight = weights.get(factor_name, 0.3)
            
            # Compute update: η × w_t,f × e_t,k × x_t,f
            update = learning_rate * weight * error * factor_score
            
            # Clip update: |ΔB_k,f| ≤ ΔB_max
            update = max(-max_daily_coef_change, min(max_daily_coef_change, update))
            
            new_coef = current_coef + update
            updated_coefficients[tenor][factor_name] = new_coef
    
    # Apply sign guards
    updated_coefficients = apply_sign_guards(updated_coefficients)
    
    # Smooth across maturities
    updated_coefficients = smooth_across_maturities(updated_coefficients, smoothing_gamma)
    
    return updated_coefficients

def update_intercepts(date: str,
                     intercepts: Dict[str, float],
                     errors: Dict[str, float],
                     learning_rate: float = 0.05) -> Dict[str, float]:
    """
    Update intercepts (bias terms): b_k ← b_k + η × e_t,k
    """
    updated_intercepts = {}
    
    for tenor in TENORS:
        error = errors.get(tenor, 0.0)
        current_intercept = intercepts.get(tenor, 0.0)
        updated_intercepts[tenor] = current_intercept + learning_rate * error
    
    return updated_intercepts

def save_coefficients(date: str, coefficients: Dict[str, Dict[str, float]]):
    """Save coefficients to database."""
    conn = get_conn()
    c = conn.cursor()
    
    for tenor, factor_coefs in coefficients.items():
        for factor_name, coef_bps in factor_coefs.items():
            c.execute("""
                INSERT OR REPLACE INTO linear_model_coefficients
                (date, tenor, factor_name, coefficient_bps, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                date,
                tenor,
                factor_name,
                coef_bps,
                dt.datetime.now(timezone.utc).isoformat()
            ))
    
    conn.commit()
    conn.close()

def save_intercepts(date: str, intercepts: Dict[str, float]):
    """Save intercepts to database."""
    conn = get_conn()
    c = conn.cursor()
    
    for tenor, intercept_bps in intercepts.items():
        c.execute("""
            INSERT OR REPLACE INTO linear_model_intercepts
            (date, tenor, intercept_bps, updated_at)
            VALUES (?, ?, ?, ?)
        """, (
            date,
            tenor,
            intercept_bps,
            dt.datetime.now(timezone.utc).isoformat()
        ))
    
    conn.commit()
    conn.close()

def save_predictions(date: str, predictions: Dict[str, float], 
                    actuals: Dict[str, float]):
    """Save predictions and errors to database."""
    conn = get_conn()
    c = conn.cursor()
    
    for tenor in TENORS:
        pred = predictions.get(tenor, 0.0)
        actual = actuals.get(tenor, 0.0)
        error = actual - pred
        
        c.execute("""
            INSERT INTO linear_model_predictions
            (date, tenor, predicted_delta_bps, actual_delta_bps, error_bps, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            date,
            tenor,
            pred,
            actual,
            error,
            dt.datetime.now(timezone.utc).isoformat()
        ))
    
    conn.commit()
    conn.close()

def compute_factor_attribution(date: str, 
                                coefficients: Optional[Dict[str, Dict[str, float]]] = None,
                                factor_scores: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, float]]:
    """
    Compute attribution: which factors contribute most to yield changes.
    
    For each tenor, computes: Contribution_f,k = B_k,f × x_t,f
    
    Args:
        date: Date string
        coefficients: {tenor: {factor_name: coefficient_bps}} (if None, loads from DB)
        factor_scores: {factor_name: factor_score} (if None, loads from DB)
    
    Returns:
        {tenor: {factor_name: contribution_bps}} - sorted by absolute contribution
    """
    if coefficients is None:
        coefficients = initialize_coefficients(date)
    
    if factor_scores is None:
        factor_scores = get_daily_factor_scores(date)
    
    attribution = {tenor: {} for tenor in TENORS}
    
    for tenor in TENORS:
        for factor_name, factor_score in factor_scores.items():
            if factor_name in coefficients.get(tenor, {}):
                coef = coefficients[tenor][factor_name]
                contribution = coef * factor_score
                attribution[tenor][factor_name] = contribution
    
    # Sort by absolute contribution for each tenor
    sorted_attribution = {}
    for tenor in TENORS:
        factors = attribution[tenor]
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        sorted_attribution[tenor] = dict(sorted_factors)
    
    return sorted_attribution

def get_top_factors_by_tenor(attribution: Dict[str, Dict[str, float]], 
                             top_n: int = 5) -> Dict[str, List[Tuple[str, float]]]:
    """
    Get top N factors by absolute contribution for each tenor.
    
    Returns:
        {tenor: [(factor_name, contribution_bps), ...]}
    """
    top_factors = {}
    for tenor, factors in attribution.items():
        top_factors[tenor] = list(factors.items())[:top_n]
    return top_factors

def train_linear_model_for_date(date: str, check_significance: bool = True, 
                                threshold_std: float = 2.0) -> bool:
    """
    Train linear model for a single date:
    1. Check if move is significant (optional)
    2. Load coefficients (or initialize from cold-start)
    3. Get factor scores
    4. Predict yield changes
    5. Get actual yield changes
    6. Update coefficients
    7. Save everything
    
    Args:
        date: Date to train on
        check_significance: If True, only train on significant moves
        threshold_std: Standard deviation threshold for significance (default: 2.0)
    """
    print(f"[LINEAR] Training linear model for {date}")
    
    # Check significance if enabled
    if check_significance:
        try:
            from yield_movement_thresholds import should_train_on_date
            should_train, sig_info = should_train_on_date(date, threshold_std, min_significant_tenors=1)
            
            if not should_train:
                print(f"[SKIP] Date {date} has no significant moves (threshold: {threshold_std}σ)")
                print(f"[SKIP] Significant tenors: {len(sig_info.get('significant_tenors', []))}")
                return False
            
            sig_tenors = sig_info.get("significant_tenors", [])
            print(f"[INFO] Significant moves detected: {', '.join(sig_tenors)}")
        except ImportError:
            print("[WARN] yield_movement_thresholds not available, training without significance check")
        except Exception as e:
            print(f"[WARN] Significance check failed: {e}, continuing with training")
    
    # Load or initialize coefficients
    coefficients = initialize_coefficients(date)
    
    # Get factor scores
    factor_scores = get_daily_factor_scores(date)
    if not factor_scores:
        print(f"[WARN] No factor scores for {date}")
        return False
    
    # Get intercepts
    intercepts = get_intercepts(date)
    
    # Predict
    predictions = predict_yield_changes(date, coefficients, factor_scores, intercepts)
    
    # Get actuals
    actuals = get_actual_yield_changes(date)
    if not actuals:
        print(f"[WARN] No actual yield changes for {date}")
        return False
    
    # Compute errors
    errors = {tenor: actuals.get(tenor, 0.0) - predictions.get(tenor, 0.0) for tenor in TENORS}
    
    # Update coefficients
    updated_coefficients = update_coefficients(
        date, coefficients, factor_scores, actuals, predictions
    )
    
    # Update intercepts
    config = load_config()
    cold_start = config.get("linear_model_cold_start", {})
    learning_rate = cold_start.get("learning_rate", 0.05)
    updated_intercepts = update_intercepts(date, intercepts, errors, learning_rate)
    
    # Save everything
    save_coefficients(date, updated_coefficients)
    save_intercepts(date, updated_intercepts)
    save_predictions(date, predictions, actuals)
    
    # Print summary
    print(f"[LINEAR] Updated coefficients for {date}")
    print(f"[LINEAR] Predictions: {predictions}")
    print(f"[LINEAR] Actuals: {actuals}")
    print(f"[LINEAR] Errors: {errors}")
    
    return True

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Train linear online learning model")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    args = ap.parse_args()
    
    target_date = args.date if args.date else dt.date.today().isoformat()
    train_linear_model_for_date(target_date)

if __name__ == "__main__":
    main()

