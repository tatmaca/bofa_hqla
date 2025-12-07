#!/usr/bin/env python3
"""
Attribution Analysis and Visualization
Creates visualizations for:
1. Linear model factor attribution (ranking factors by contribution)
2. SHAP values from XGBoost models
3. Comparison between linear coefficients and SHAP feature importance
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from train_linear_online import (
    compute_factor_attribution, 
    get_top_factors_by_tenor,
    initialize_coefficients,
    get_daily_factor_scores,
    TENORS
)
from train_xgboost import MODEL_DIR

try:
    import seaborn as sns
    sns.set_style("whitegrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    shap = None

OUTPUT_DIR = Path(__file__).parent / "attribution_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

def plot_factor_attribution_by_tenor(attribution: Dict[str, Dict[str, float]], 
                                     date: str,
                                     top_n: int = 10,
                                     save_path: Optional[Path] = None) -> Path:
    """
    Create bar chart showing top factors by absolute contribution for each tenor.
    
    Args:
        attribution: {tenor: {factor_name: contribution_bps}}
        date: Date string for title
        top_n: Number of top factors to show per tenor
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    # Adjust figure size based on number of tenors
    fig_width = max(20, len(TENORS) * 2.5)
    fig, axes = plt.subplots(1, len(TENORS), figsize=(fig_width, 6))
    if len(TENORS) == 1:
        axes = [axes]
    
    fig.suptitle(f'Factor Attribution by Tenor - {date}', fontsize=16, fontweight='bold')
    
    for idx, tenor in enumerate(TENORS):
        ax = axes[idx]
        factors = attribution.get(tenor, {})
        
        if not factors:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(tenor)
            continue
        
        # Get top N factors
        top_factors = list(factors.items())[:top_n]
        factor_names = [f[0] for f in top_factors]
        contributions = [f[1] for f in top_factors]
        
        # Color bars by positive/negative
        colors = ['#2ecc71' if c >= 0 else '#e74c3c' for c in contributions]
        
        # Create horizontal bar chart
        y_pos = np.arange(len(factor_names))
        bars = ax.barh(y_pos, contributions, color=colors, alpha=0.7)
        
        # Format factor names (truncate if too long)
        display_names = [name[:20] + '...' if len(name) > 20 else name for name in factor_names]
        ax.set_yticks(y_pos)
        ax.set_yticklabels(display_names, fontsize=8)
        ax.set_xlabel('Contribution (bps)', fontsize=10)
        ax.set_title(f'{tenor}', fontsize=12, fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, contributions)):
            width = bar.get_width()
            label_x = width + (0.1 if width >= 0 else -0.1)
            ax.text(label_x, bar.get_y() + bar.get_height()/2, 
                   f'{val:.2f}', ha='left' if width >= 0 else 'right', 
                   va='center', fontsize=7)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"factor_attribution_{date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[VIZ] Saved factor attribution plot to {save_path}")
    return save_path

def plot_factor_contribution_heatmap(attribution: Dict[str, Dict[str, float]], 
                                     date: str,
                                     top_n: int = 15,
                                     save_path: Optional[Path] = None) -> Path:
    """
    Create heatmap showing factor contributions across tenors.
    
    Args:
        attribution: {tenor: {factor_name: contribution_bps}}
        date: Date string for title
        top_n: Number of top factors to show
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    # Collect all factors and their contributions
    all_factors = set()
    for factors in attribution.values():
        all_factors.update(factors.keys())
    
    # Compute total absolute contribution per factor across all tenors
    factor_totals = {}
    for factor in all_factors:
        total = sum(abs(attribution.get(tenor, {}).get(factor, 0.0)) for tenor in TENORS)
        factor_totals[factor] = total
    
    # Get top N factors
    top_factors = sorted(factor_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_factor_names = [f[0] for f in top_factors]
    
    # Build matrix: rows = factors, columns = tenors
    matrix = []
    for factor in top_factor_names:
        row = [attribution.get(tenor, {}).get(factor, 0.0) for tenor in TENORS]
        matrix.append(row)
    
    matrix = np.array(matrix)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, max(8, len(top_factor_names) * 0.5)))
    
    # Truncate factor names for display
    display_names = [name[:30] + '...' if len(name) > 30 else name for name in top_factor_names]
    
    im = ax.imshow(matrix, cmap='RdBu_r', aspect='auto', vmin=-max(abs(matrix.min()), abs(matrix.max())), 
                   vmax=max(abs(matrix.min()), abs(matrix.max())))
    
    ax.set_xticks(np.arange(len(TENORS)))
    ax.set_xticklabels(TENORS)
    ax.set_yticks(np.arange(len(display_names)))
    ax.set_yticklabels(display_names, fontsize=9)
    ax.set_xlabel('Tenor', fontsize=12, fontweight='bold')
    ax.set_ylabel('Factor', fontsize=12, fontweight='bold')
    ax.set_title(f'Factor Contribution Heatmap - {date}', fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Contribution (bps)', fontsize=10)
    
    # Add text annotations
    for i in range(len(top_factor_names)):
        for j in range(len(TENORS)):
            text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                          ha="center", va="center", color="black" if abs(matrix[i, j]) < max(abs(matrix.min()), abs(matrix.max())) * 0.5 else "white",
                          fontsize=7)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"factor_heatmap_{date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[VIZ] Saved factor heatmap to {save_path}")
    return save_path

def plot_shap_summary(shap_values: np.ndarray, 
                     feature_names: List[str],
                     target_name: str,
                     date: str,
                     save_path: Optional[Path] = None) -> Path:
    """
    Create SHAP summary plot (bar chart of mean absolute SHAP values).
    
    Args:
        shap_values: Array of SHAP values (n_samples, n_features)
        feature_names: List of feature names
        target_name: Target variable name (e.g., '2y', '10y')
        date: Date string for title
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    if not HAS_SHAP or shap_values is None:
        print("[WARN] SHAP not available for plotting")
        return None
    
    # Compute mean absolute SHAP per feature
    mean_abs_shap = np.abs(shap_values).mean(0)
    
    # Sort by importance
    sorted_indices = np.argsort(mean_abs_shap)[::-1]
    top_n = min(20, len(feature_names))
    
    top_indices = sorted_indices[:top_n]
    top_features = [feature_names[i] for i in top_indices]
    top_values = mean_abs_shap[top_indices]
    
    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, max(6, top_n * 0.4)))
    
    colors = plt.cm.viridis(np.linspace(0, 1, top_n))
    bars = ax.barh(range(top_n), top_values, color=colors)
    
    # Format feature names
    display_names = [name[:40] + '...' if len(name) > 40 else name for name in top_features]
    
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(display_names, fontsize=9)
    ax.set_xlabel('Mean |SHAP Value|', fontsize=11, fontweight='bold')
    ax.set_title(f'SHAP Feature Importance - {target_name} ({date})', fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, top_values)):
        ax.text(bar.get_width() + max(top_values) * 0.01, bar.get_y() + bar.get_height()/2,
               f'{val:.4f}', va='center', fontsize=8)
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"shap_summary_{target_name}_{date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[VIZ] Saved SHAP summary plot to {save_path}")
    return save_path

def compare_linear_shap_importance(linear_coefficients: Dict[str, Dict[str, float]],
                                   shap_importance: Dict[str, float],
                                   tenor: str,
                                   date: str,
                                   top_n: int = 15,
                                   save_path: Optional[Path] = None) -> Path:
    """
    Compare linear model coefficients with SHAP feature importance.
    Shows alignment between the two models.
    
    Args:
        linear_coefficients: {factor_name: coefficient_bps} for a specific tenor
        shap_importance: {feature_name: mean_abs_shap_value}
        tenor: Tenor name (e.g., '2Y', '10Y')
        date: Date string
        top_n: Number of top features to compare
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    # Extract factor coefficients (absolute values)
    linear_abs = {name: abs(coef) for name, coef in linear_coefficients.items()}
    
    # Extract factor-related SHAP features (features starting with 'factor_')
    factor_shap = {}
    for feat_name, shap_val in shap_importance.items():
        if feat_name.startswith('factor_'):
            factor_name = feat_name.replace('factor_', '')
            factor_shap[factor_name] = shap_val
    
    # Find common factors
    common_factors = set(linear_abs.keys()) & set(factor_shap.keys())
    
    if not common_factors:
        print(f"[WARN] No common factors found between linear model and SHAP for {tenor}")
        return None
    
    # Get top factors from both
    linear_sorted = sorted(linear_abs.items(), key=lambda x: x[1], reverse=True)[:top_n]
    shap_sorted = sorted(factor_shap.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, max(8, len(common_factors) * 0.4)))
    
    # Linear model coefficients
    linear_names = [f[0] for f in linear_sorted]
    linear_vals = [f[1] for f in linear_sorted]
    
    ax1.barh(range(len(linear_names)), linear_vals, color='#3498db', alpha=0.7)
    display_names_1 = [name[:25] + '...' if len(name) > 25 else name for name in linear_names]
    ax1.set_yticks(range(len(linear_names)))
    ax1.set_yticklabels(display_names_1, fontsize=8)
    ax1.set_xlabel('|Coefficient| (bps)', fontsize=10, fontweight='bold')
    ax1.set_title(f'Linear Model Coefficients - {tenor}', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # SHAP importance
    shap_names = [f[0] for f in shap_sorted]
    shap_vals = [f[1] for f in shap_sorted]
    
    ax2.barh(range(len(shap_names)), shap_vals, color='#9b59b6', alpha=0.7)
    display_names_2 = [name[:25] + '...' if len(name) > 25 else name for name in shap_names]
    ax2.set_yticks(range(len(shap_names)))
    ax2.set_yticklabels(display_names_2, fontsize=8)
    ax2.set_xlabel('Mean |SHAP Value|', fontsize=10, fontweight='bold')
    ax2.set_title(f'SHAP Feature Importance - {tenor}', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    fig.suptitle(f'Linear vs SHAP Comparison - {tenor} ({date})', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"linear_shap_comparison_{tenor}_{date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[VIZ] Saved linear-SHAP comparison to {save_path}")
    return save_path

def generate_attribution_report(date: str, 
                               output_dir: Optional[Path] = None) -> Dict:
    """
    Generate comprehensive attribution report for a given date.
    
    Args:
        date: Date string (YYYY-MM-DD)
        output_dir: Optional output directory
    
    Returns:
        Dictionary with report data and paths to generated visualizations
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    output_dir.mkdir(exist_ok=True)
    
    print(f"[REPORT] Generating attribution report for {date}")
    
    # Get linear model attribution
    coefficients = initialize_coefficients(date)
    factor_scores = get_daily_factor_scores(date)
    
    if not factor_scores:
        print(f"[WARN] No factor scores found for {date}")
        return {}
    
    attribution = compute_factor_attribution(date, coefficients, factor_scores)
    top_factors = get_top_factors_by_tenor(attribution, top_n=10)
    
    # Generate visualizations
    report = {
        "date": date,
        "attribution": {tenor: dict(factors) for tenor, factors in top_factors.items()},
        "visualizations": {}
    }
    
    # Factor attribution by tenor
    viz_path = plot_factor_attribution_by_tenor(attribution, date, top_n=10)
    report["visualizations"]["factor_attribution"] = str(viz_path)
    
    # Factor heatmap
    viz_path = plot_factor_contribution_heatmap(attribution, date, top_n=15)
    report["visualizations"]["factor_heatmap"] = str(viz_path)
    
    # Try to load XGBoost models and generate SHAP plots
    try:
        metadata_files = sorted(MODEL_DIR.glob("xgb_metadata_*.json"), reverse=True)
        if metadata_files:
            with open(metadata_files[0]) as f:
                xgb_metadata = json.load(f)
            
            # For each target, try to get SHAP info from saved models
                for target in xgb_metadata.get("targets", []):
                    model_info = xgb_metadata.get("model_info", {}).get(target, {})
                    shap_ranking = model_info.get("top_features_shap", [])
                    
                    if shap_ranking:
                        # Create a simple SHAP importance dict from ranking
                        shap_importance = {feat: len(shap_ranking) - i for i, feat in enumerate(shap_ranking)}
                        
                        # Compare with linear model for matching tenor
                        tenor_map = {
                            "1m": "1M", "3m": "3M", "6m": "6M",
                            "1y": "1Y", "2y": "2Y", "3y": "3Y",
                            "5y": "5Y", "7y": "7Y", "10y": "10Y", "20y": "20Y", "30y": "30Y"
                        }
                        linear_tenor = tenor_map.get(target.lower(), target.upper())
                        
                        if linear_tenor in attribution:
                            linear_coefs = {name: coefficients.get(linear_tenor, {}).get(name, 0.0) 
                                          for name in factor_scores.keys()}
                            
                            viz_path = compare_linear_shap_importance(
                                linear_coefs, shap_importance, linear_tenor, date
                            )
                            if viz_path:
                                report["visualizations"][f"linear_shap_comparison_{target}"] = str(viz_path)
    except Exception as e:
        print(f"[WARN] Could not generate SHAP comparisons: {e}")
    
    # Save report JSON
    report_path = output_dir / f"attribution_report_{date}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"[REPORT] Saved attribution report to {report_path}")
    report["report_path"] = str(report_path)
    
    return report

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate attribution analysis and visualizations")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--output-dir", type=str, help="Output directory for visualizations")
    args = ap.parse_args()
    
    date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    report = generate_attribution_report(date, output_dir)
    
    if report:
        print(f"\n[SUCCESS] Attribution report generated:")
        print(f"  Date: {report['date']}")
        print(f"  Visualizations: {len(report.get('visualizations', {}))}")
        print(f"  Report path: {report.get('report_path', 'N/A')}")

if __name__ == "__main__":
    main()

