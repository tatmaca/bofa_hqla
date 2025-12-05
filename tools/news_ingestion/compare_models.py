#!/usr/bin/env python3
"""
Model Comparison and Alignment Analysis
Compares linear model coefficients with XGBoost SHAP values to understand
connections and differences between the two approaches.
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys
from collections import defaultdict

try:
    from scipy.stats import spearmanr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARN] scipy not available. Rank correlation will not be computed.")

sys.path.insert(0, str(Path(__file__).parent))

from train_linear_online import (
    initialize_coefficients,
    get_daily_factor_scores,
    TENORS
)
from train_xgboost import MODEL_DIR

# Map XGBoost targets (lowercase) to linear model tenors (uppercase)
TENOR_MAP = {
    "1m": "1M", "1M": "1M",
    "3m": "3M", "3M": "3M",
    "6m": "6M", "6M": "6M",
    "1y": "1Y", "1Y": "1Y",
    "2y": "2Y", "2Y": "2Y",
    "3y": "3Y", "3Y": "3Y",
    "5y": "5Y", "5Y": "5Y",
    "7y": "7Y", "7Y": "7Y",
    "10y": "10Y", "10Y": "10Y",
    "20y": "20Y", "20Y": "20Y",
    "30y": "30Y", "30Y": "30Y",
}

def load_xgb_metadata() -> Optional[Dict]:
    """Load latest XGBoost model metadata."""
    metadata_files = sorted(MODEL_DIR.glob("xgb_metadata_*.json"), reverse=True)
    if not metadata_files:
        return None

    with open(metadata_files[0]) as f:
        return json.load(f)

def extract_factor_shap_importance(shap_importance: Dict[str, float]) -> Dict[str, float]:
    """
    Extract factor-related features from SHAP importance.
    Returns {factor_name: mean_abs_shap_value} for features starting with 'factor_'
    """
    factor_shap = {}
    for feat_name, shap_val in shap_importance.items():
        if feat_name.startswith('factor_'):
            factor_name = feat_name.replace('factor_', '')
            factor_shap[factor_name] = shap_val
    return factor_shap

def compute_alignment_metrics(linear_coefs: Dict[str, float],
                             shap_importance: Dict[str, float]) -> Dict:
    """
    Compute alignment metrics between linear coefficients and SHAP importance.
    
    Returns:
        Dictionary with alignment metrics:
        - common_factors: List of factors present in both
        - correlation: Pearson correlation of absolute values
        - rank_correlation: Spearman rank correlation
        - top_overlap: Number of top-10 factors that overlap
    """
    # Get absolute values for comparison
    linear_abs = {name: abs(coef) for name, coef in linear_coefs.items()}
    shap_abs = {name: abs(val) for name, val in shap_importance.items()}
    
    # Find common factors
    common_factors = set(linear_abs.keys()) & set(shap_abs.keys())
    
    if len(common_factors) < 2:
        return {
            "common_factors": list(common_factors),
            "correlation": None,
            "rank_correlation": None,
            "top_overlap": 0,
            "alignment_score": 0.0
        }
    
    # Get values for common factors
    linear_vals = [linear_abs[f] for f in common_factors]
    shap_vals = [shap_abs[f] for f in common_factors]
    
    # Compute correlation
    if len(linear_vals) > 1:
        correlation = np.corrcoef(linear_vals, shap_vals)[0, 1]
    else:
        correlation = None
    
    # Compute rank correlation
    rank_corr = None
    if HAS_SCIPY:
        try:
            rank_corr, _ = spearmanr(linear_vals, shap_vals)
        except:
            rank_corr = None
    
    # Top overlap: check how many of top-10 factors overlap
    linear_top10 = sorted(linear_abs.items(), key=lambda x: x[1], reverse=True)[:10]
    shap_top10 = sorted(shap_abs.items(), key=lambda x: x[1], reverse=True)[:10]
    
    linear_top10_set = set(f[0] for f in linear_top10)
    shap_top10_set = set(f[0] for f in shap_top10)
    top_overlap = len(linear_top10_set & shap_top10_set)
    
    # Alignment score: weighted combination
    alignment_score = 0.0
    if correlation is not None:
        alignment_score += 0.4 * max(0, correlation)  # Positive correlation
    if rank_corr is not None:
        alignment_score += 0.4 * max(0, rank_corr)  # Positive rank correlation
    alignment_score += 0.2 * (top_overlap / 10.0)  # Top overlap
    
    return {
        "common_factors": sorted(common_factors),
        "num_common": len(common_factors),
        "correlation": float(correlation) if correlation is not None else None,
        "rank_correlation": float(rank_corr) if rank_corr is not None else None,
        "top_overlap": top_overlap,
        "alignment_score": float(alignment_score),
        "linear_top10": [f[0] for f in linear_top10],
        "shap_top10": [f[0] for f in shap_top10]
    }

def compare_all_tenors(date: str) -> Dict:
    """
    Compare linear model and XGBoost SHAP for all tenors.
    
    Args:
        date: Date string for linear model coefficients
    
    Returns:
        Dictionary with comparison results for each tenor
    """
    print(f"[COMPARE] Comparing models for date {date}")
    
    # Load linear model
    coefficients = initialize_coefficients(date)
    factor_scores = get_daily_factor_scores(date)
    
    if not factor_scores:
        print(f"[WARN] No factor scores found for {date}")
        return {}
    
    # Load XGBoost metadata
    xgb_metadata = load_xgb_metadata()
    if not xgb_metadata:
        print("[WARN] No XGBoost metadata found")
        return {}
    
    results = {}
    
    # For each target in XGBoost, find matching tenor in linear model
    for target in xgb_metadata.get("targets", []):
        model_info = xgb_metadata.get("model_info", {}).get(target, {})
        
        # Get SHAP importance ranking
        shap_top_features = model_info.get("top_features_shap", [])
        
        if not shap_top_features:
            continue
        
        # Map target to tenor
        tenor = TENOR_MAP.get(target, target.upper())
        
        if tenor not in coefficients:
            continue
        
        # Get linear coefficients for this tenor
        linear_coefs = coefficients[tenor]
        
        # Extract factor-related SHAP features
        # Create a simple importance dict from ranking (higher rank = more important)
        shap_importance = {}
        for i, feat_name in enumerate(shap_top_features):
            if feat_name.startswith('factor_'):
                factor_name = feat_name.replace('factor_', '')
                # Inverse rank (first = highest importance)
                shap_importance[factor_name] = len(shap_top_features) - i
        
        # Compute alignment
        alignment = compute_alignment_metrics(linear_coefs, shap_importance)
        
        results[target] = {
            "tenor": tenor,
            "alignment": alignment,
            "linear_coefficients": {name: float(coef) for name, coef in linear_coefs.items()},
            "shap_importance": shap_importance
        }
    
    return results

def generate_comparison_report(date: str, output_path: Optional[Path] = None) -> Dict:
    """
    Generate comprehensive comparison report.
    
    Args:
        date: Date string
        output_path: Optional path to save report
    
    Returns:
        Dictionary with comparison results
    """
    if output_path is None:
        output_path = Path(__file__).parent / "attribution_analysis" / f"model_comparison_{date}.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    comparison = compare_all_tenors(date)
    
    # Add summary statistics
    alignment_scores = [r["alignment"]["alignment_score"] for r in comparison.values() 
                       if r["alignment"]["alignment_score"] is not None]
    correlations = [r["alignment"]["correlation"] for r in comparison.values() 
                   if r["alignment"].get("correlation") is not None]
    
    summary = {
        "date": date,
        "num_tenors_compared": len(comparison),
        "mean_alignment_score": float(np.mean(alignment_scores)) if alignment_scores else None,
        "mean_correlation": float(np.mean(correlations)) if correlations else None,
        "comparison_by_tenor": comparison
    }
    
    # Save report
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"[COMPARE] Saved comparison report to {output_path}")
    
    # Print summary
    print(f"\n[COMPARE] Summary:")
    print(f"  Tenors compared: {summary['num_tenors_compared']}")
    if summary['mean_alignment_score'] is not None:
        print(f"  Mean alignment score: {summary['mean_alignment_score']:.3f}")
    if summary['mean_correlation'] is not None:
        print(f"  Mean correlation: {summary['mean_correlation']:.3f}")
    
    for target, result in comparison.items():
        align = result["alignment"]
        print(f"\n  {target} ({result['tenor']}):")
        print(f"    Alignment score: {align['alignment_score']:.3f}")
        if align.get('correlation') is not None:
            print(f"    Correlation: {align['correlation']:.3f}")
        print(f"    Top-10 overlap: {align['top_overlap']}/10")
        print(f"    Common factors: {align.get('num_common', 0)}")
    
    return summary

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Compare linear model and XGBoost SHAP importance")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD) for linear model, defaults to today")
    ap.add_argument("--output", type=str, help="Output file path")
    args = ap.parse_args()
    
    from datetime import datetime
    date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    
    output_path = Path(args.output) if args.output else None
    
    report = generate_comparison_report(date, output_path)
    
    if report:
        print(f"\n[SUCCESS] Comparison report generated")

if __name__ == "__main__":
    main()
