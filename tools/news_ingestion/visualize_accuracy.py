#!/usr/bin/env python3
"""
Accuracy Visualization Module
Creates visualizations for prediction accuracy tracking over time.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from calculate_prediction_accuracy import load_accuracy_history, load_tenor_accuracy_history
from train_linear_online import TENORS

try:
    import seaborn as sns
    sns.set_style("whitegrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

OUTPUT_DIR = Path(__file__).parent / "accuracy_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Metric labels for plots
METRIC_LABELS = {
    "mae_bps": "MAE (bps)",
    "rmse_bps": "RMSE (bps)",
    "r2": "R²",
    "directional_accuracy": "Directional Accuracy (%)",
    "correlation": "Correlation"
}


def plot_accuracy_over_time(start_date: str,
                            end_date: str,
                            metric: str = "mae_bps",
                            scenarios: Optional[List[str]] = None,
                            rolling_window: Optional[int] = None,
                            save_path: Optional[Path] = None) -> Path:
    """
    Plot accuracy metric over time for multiple scenarios.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metric: Metric to plot ('mae_bps', 'rmse_bps', 'r2', 'directional_accuracy', 'correlation')
        scenarios: List of scenario names (if None, plots all)
        rolling_window: Optional rolling average window (days)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    history = load_accuracy_history(start_date, end_date)
    
    if not history:
        print(f"[WARN] No accuracy data found for {start_date} to {end_date}")
        return None
    
    # Group by scenario
    scenario_data = {}
    for record in history:
        scenario = record["scenario_name"]
        if scenarios and scenario not in scenarios:
            continue
        
        if scenario not in scenario_data:
            scenario_data[scenario] = {"dates": [], "values": []}
        
        date_str = record["date"]
        value = record.get(metric)
        
        if value is not None:
            scenario_data[scenario]["dates"].append(date_str)
            scenario_data[scenario]["values"].append(value)
    
    if not scenario_data:
        print(f"[WARN] No data for specified scenarios")
        return None
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Color palette
    colors = plt.cm.tab10(np.linspace(0, 1, len(scenario_data)))
    
    for idx, (scenario, data) in enumerate(scenario_data.items()):
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in data["dates"]]
        values = data["values"]
        
        # Apply rolling average if requested
        if rolling_window and len(values) > rolling_window:
            values_series = np.array(values)
            rolling_values = []
            for i in range(len(values_series)):
                start_idx = max(0, i - rolling_window + 1)
                rolling_values.append(np.mean(values_series[start_idx:i+1]))
            values = rolling_values
        
        ax.plot(dates, values, label=scenario, color=colors[idx], linewidth=2, marker='o', markersize=4)
    
    # Formatting
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(METRIC_LABELS.get(metric, metric), fontsize=12)
    ax.set_title(f"{METRIC_LABELS.get(metric, metric)} Over Time", fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"accuracy_over_time_{metric}_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def plot_scenario_accuracy_heatmap(start_date: str,
                                  end_date: str,
                                  metric: str = "mae_bps",
                                  save_path: Optional[Path] = None) -> Path:
    """
    Create heatmap showing accuracy by scenario and date.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metric: Metric to plot
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    history = load_accuracy_history(start_date, end_date)
    
    if not history:
        print(f"[WARN] No accuracy data found")
        return None
    
    # Build matrix: scenarios (rows) × dates (columns)
    scenarios = sorted(set(r["scenario_name"] for r in history))
    dates = sorted(set(r["date"] for r in history))
    
    matrix = np.full((len(scenarios), len(dates)), np.nan)
    
    for record in history:
        scenario_idx = scenarios.index(record["scenario_name"])
        date_idx = dates.index(record["date"])
        value = record.get(metric)
        if value is not None:
            matrix[scenario_idx, date_idx] = value
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(max(14, len(dates) * 0.5), max(8, len(scenarios) * 0.6)))
    
    if HAS_SEABORN:
        sns.heatmap(matrix, 
                   xticklabels=[d[5:] for d in dates],  # Show MM-DD
                   yticklabels=scenarios,
                   annot=True,
                   fmt='.1f',
                   cmap='RdYlGn_r',  # Red-Yellow-Green reversed (green = low error)
                   cbar_kws={'label': METRIC_LABELS.get(metric, metric)},
                   ax=ax)
    else:
        im = ax.imshow(matrix, aspect='auto', cmap='RdYlGn_r')
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([d[5:] for d in dates], rotation=45)
        ax.set_yticks(range(len(scenarios)))
        ax.set_yticklabels(scenarios)
        plt.colorbar(im, ax=ax, label=METRIC_LABELS.get(metric, metric))
        
        # Add text annotations
        for i in range(len(scenarios)):
            for j in range(len(dates)):
                if not np.isnan(matrix[i, j]):
                    ax.text(j, i, f'{matrix[i, j]:.1f}', 
                           ha='center', va='center', fontsize=8)
    
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Scenario", fontsize=12)
    ax.set_title(f"{METRIC_LABELS.get(metric, metric)} Heatmap", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"accuracy_heatmap_{metric}_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def plot_tenor_accuracy(start_date: str,
                       end_date: str,
                       metric: str = "mae_bps",
                       scenarios: Optional[List[str]] = None,
                       save_path: Optional[Path] = None) -> Path:
    """
    Plot accuracy by tenor for different scenarios.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metric: Metric to plot
        scenarios: List of scenario names (if None, plots all)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    # Load per-tenor data
    tenor_history = load_tenor_accuracy_history(start_date, end_date)
    
    if not tenor_history:
        print(f"[WARN] No per-tenor accuracy data found")
        return None
    
    # Aggregate by tenor and scenario
    tenor_metrics = {}
    for record in tenor_history:
        scenario = record["scenario_name"]
        if scenarios and scenario not in scenarios:
            continue
        
        tenor = record["tenor"]
        if scenario not in tenor_metrics:
            tenor_metrics[scenario] = {}
        if tenor not in tenor_metrics[scenario]:
            tenor_metrics[scenario][tenor] = []
        
        # Calculate metric from error
        if metric == "mae_bps":
            tenor_metrics[scenario][tenor].append(abs(record["error_bps"]))
        elif metric == "rmse_bps":
            tenor_metrics[scenario][tenor].append(record["error_bps"] ** 2)
        else:
            continue
    
    # Calculate means
    scenario_tenor_means = {}
    for scenario, tenors in tenor_metrics.items():
        scenario_tenor_means[scenario] = {}
        for tenor, values in tenors.items():
            if metric == "mae_bps":
                scenario_tenor_means[scenario][tenor] = np.mean(values)
            elif metric == "rmse_bps":
                scenario_tenor_means[scenario][tenor] = np.sqrt(np.mean(values))
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(TENORS))
    width = 0.8 / len(scenario_tenor_means) if scenario_tenor_means else 0.8
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(scenario_tenor_means)))
    
    for idx, (scenario, tenor_means) in enumerate(scenario_tenor_means.items()):
        values = [tenor_means.get(tenor, 0) for tenor in TENORS]
        offset = (idx - len(scenario_tenor_means) / 2 + 0.5) * width
        ax.bar(x + offset, values, width, label=scenario, color=colors[idx], alpha=0.7)
    
    ax.set_xlabel("Tenor", fontsize=12)
    ax.set_ylabel(METRIC_LABELS.get(metric, metric), fontsize=12)
    ax.set_title(f"{METRIC_LABELS.get(metric, metric)} by Tenor", fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(TENORS)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"tenor_accuracy_{metric}_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def plot_r2_over_time(start_date: str,
                      end_date: str,
                      scenarios: Optional[List[str]] = None,
                      save_path: Optional[Path] = None) -> Path:
    """
    Plot R² over time for each scenario.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenarios: List of scenario names (if None, plots all)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    return plot_accuracy_over_time(start_date, end_date, "r2", scenarios, save_path=save_path)


def plot_directional_accuracy(start_date: str,
                            end_date: str,
                            scenarios: Optional[List[str]] = None,
                            save_path: Optional[Path] = None) -> Path:
    """
    Plot directional accuracy over time.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenarios: List of scenario names (if None, plots all)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    return plot_accuracy_over_time(start_date, end_date, "directional_accuracy", scenarios, save_path=save_path)


def plot_error_distribution(start_date: str,
                           end_date: str,
                           scenario_name: Optional[str] = None,
                           save_path: Optional[Path] = None) -> Path:
    """
    Plot error distribution (histogram or box plot).
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenario_name: Optional scenario name (if None, plots all scenarios)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    tenor_history = load_tenor_accuracy_history(start_date, end_date, scenario_name=scenario_name)
    
    if not tenor_history:
        print(f"[WARN] No error data found")
        return None
    
    errors = [abs(r["error_bps"]) for r in tenor_history if r.get("error_bps") is not None]
    
    if not errors:
        print(f"[WARN] No valid errors found")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(errors, bins=30, edgecolor='black', alpha=0.7)
    ax.set_xlabel("Absolute Error (bps)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    title = f"Error Distribution"
    if scenario_name:
        title += f" - {scenario_name}"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if save_path is None:
        scenario_suffix = f"_{scenario_name}" if scenario_name else "_all"
        save_path = OUTPUT_DIR / f"error_distribution{scenario_suffix}_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def plot_prediction_vs_actual(start_date: str,
                             end_date: str,
                             scenario_name: str,
                             save_path: Optional[Path] = None) -> Path:
    """
    Scatter plot of predicted vs actual yield changes.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        scenario_name: Scenario name
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    tenor_history = load_tenor_accuracy_history(start_date, end_date, scenario_name=scenario_name)
    
    if not tenor_history:
        print(f"[WARN] No data found for {scenario_name}")
        return None
    
    predicted = [r["predicted_delta_bps"] for r in tenor_history if r.get("predicted_delta_bps") is not None]
    actual = [r["actual_delta_bps"] for r in tenor_history if r.get("actual_delta_bps") is not None]
    
    if not predicted or not actual:
        print(f"[WARN] No valid data points")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    ax.scatter(predicted, actual, alpha=0.6, s=50)
    
    # Add diagonal line (perfect prediction)
    min_val = min(min(predicted), min(actual))
    max_val = max(max(predicted), max(actual))
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    
    ax.set_xlabel("Predicted Δ (bps)", fontsize=12)
    ax.set_ylabel("Actual Δ (bps)", fontsize=12)
    ax.set_title(f"Predicted vs Actual - {scenario_name}", fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"pred_vs_actual_{scenario_name}_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def generate_accuracy_dashboard(start_date: str,
                               end_date: str,
                               save_path: Optional[Path] = None) -> Path:
    """
    Generate comprehensive accuracy dashboard with multiple visualizations.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        save_path: Optional path to save figure
    
    Returns:
        Path to saved figure
    """
    history = load_accuracy_history(start_date, end_date)
    
    if not history:
        print(f"[WARN] No accuracy data found")
        return None
    
    # Create multi-panel figure
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. MAE over time (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    _plot_metric_subplot(ax1, history, "mae_bps", "MAE Over Time")
    
    # 2. RMSE over time (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    _plot_metric_subplot(ax2, history, "rmse_bps", "RMSE Over Time")
    
    # 3. R² over time (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    _plot_metric_subplot(ax3, history, "r2", "R² Over Time")
    
    # 4. Directional accuracy (middle left)
    ax4 = fig.add_subplot(gs[1, 0])
    _plot_metric_subplot(ax4, history, "directional_accuracy", "Directional Accuracy Over Time")
    
    # 5. Correlation (middle middle)
    ax5 = fig.add_subplot(gs[1, 1])
    _plot_metric_subplot(ax5, history, "correlation", "Correlation Over Time")
    
    # 6. Summary statistics table (middle right)
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')
    _plot_summary_table(ax6, history)
    
    # 7. Error distribution (bottom left)
    ax7 = fig.add_subplot(gs[2, 0])
    _plot_error_dist_subplot(ax7, start_date, end_date)
    
    # 8. Scenario comparison (bottom middle)
    ax8 = fig.add_subplot(gs[2, 1])
    _plot_scenario_comparison(ax8, history)
    
    # 9. Improvement trend (bottom right)
    ax9 = fig.add_subplot(gs[2, 2])
    _plot_improvement_trend(ax9, history)
    
    fig.suptitle(f"Accuracy Dashboard - {start_date} to {end_date}", fontsize=16, fontweight='bold', y=0.98)
    
    if save_path is None:
        save_path = OUTPUT_DIR / f"accuracy_dashboard_{start_date}_{end_date}.png"
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return save_path


def _plot_metric_subplot(ax, history, metric, title):
    """Helper to plot a metric subplot."""
    scenario_data = {}
    for record in history:
        scenario = record["scenario_name"]
        if scenario not in scenario_data:
            scenario_data[scenario] = {"dates": [], "values": []}
        
        date_str = record["date"]
        value = record.get(metric)
        if value is not None:
            scenario_data[scenario]["dates"].append(date_str)
            scenario_data[scenario]["values"].append(value)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(scenario_data)))
    for idx, (scenario, data) in enumerate(scenario_data.items()):
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in data["dates"]]
        ax.plot(dates, data["values"], label=scenario, color=colors[idx], linewidth=1.5, marker='o', markersize=3)
    
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=8)
    if len(scenario_data) <= 5:
        ax.legend(fontsize=7)


def _plot_summary_table(ax, history):
    """Helper to plot summary statistics table."""
    scenarios = sorted(set(r["scenario_name"] for r in history))
    
    # Calculate summary stats
    table_data = []
    for scenario in scenarios:
        scenario_records = [r for r in history if r["scenario_name"] == scenario]
        mae_values = [r["mae_bps"] for r in scenario_records if r.get("mae_bps") is not None]
        r2_values = [r["r2"] for r in scenario_records if r.get("r2") is not None]
        
        if mae_values:
            avg_mae = np.mean(mae_values)
            avg_r2 = np.mean(r2_values) if r2_values else None
            table_data.append([scenario, f"{avg_mae:.2f}", f"{avg_r2:.3f}" if avg_r2 else "N/A"])
    
    if table_data:
        table = ax.table(cellText=table_data,
                        colLabels=["Scenario", "Avg MAE", "Avg R²"],
                        cellLoc='center',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        ax.set_title("Summary Statistics", fontsize=10, fontweight='bold', pad=20)


def _plot_error_dist_subplot(ax, start_date, end_date):
    """Helper to plot error distribution subplot."""
    from calculate_prediction_accuracy import load_tenor_accuracy_history
    tenor_history = load_tenor_accuracy_history(start_date, end_date)
    if tenor_history:
        errors = [abs(r["error_bps"]) for r in tenor_history if r.get("error_bps") is not None]
        if errors:
            ax.hist(errors, bins=20, edgecolor='black', alpha=0.7)
            ax.set_title("Error Distribution", fontsize=10, fontweight='bold')
            ax.set_xlabel("|Error| (bps)", fontsize=9)
            ax.set_ylabel("Frequency", fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
    else:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)


def _plot_scenario_comparison(ax, history):
    """Helper to plot scenario comparison."""
    scenarios = sorted(set(r["scenario_name"] for r in history))
    avg_mae = []
    for scenario in scenarios:
        scenario_records = [r for r in history if r["scenario_name"] == scenario]
        mae_values = [r["mae_bps"] for r in scenario_records if r.get("mae_bps") is not None]
        if mae_values:
            avg_mae.append(np.mean(mae_values))
        else:
            avg_mae.append(0)
    
    if avg_mae:
        colors = ['#2ecc71' if m == min(avg_mae) else '#e74c3c' if m == max(avg_mae) else '#3498db' 
                 for m in avg_mae]
        ax.barh(scenarios, avg_mae, color=colors, alpha=0.7)
        ax.set_title("Average MAE by Scenario", fontsize=10, fontweight='bold')
        ax.set_xlabel("MAE (bps)", fontsize=9)
        ax.grid(True, alpha=0.3, axis='x')


def _plot_improvement_trend(ax, history):
    """Helper to plot improvement trend."""
    dates = sorted(set(r["date"] for r in history))
    baseline_mae = []
    for date in dates:
        baseline_records = [r for r in history if r["date"] == date and r["scenario_name"] == "baseline"]
        if baseline_records and baseline_records[0].get("mae_bps") is not None:
            baseline_mae.append(baseline_records[0]["mae_bps"])
        else:
            baseline_mae.append(None)
    
    valid_mae = [(d, m) for d, m in zip(dates, baseline_mae) if m is not None]
    if valid_mae:
        dates_only = [datetime.strptime(d, "%Y-%m-%d") for d, _ in valid_mae]
        mae_only = [m for _, m in valid_mae]
        ax.plot(dates_only, mae_only, 'o-', linewidth=2, markersize=4, color='#3498db')
        ax.set_title("Baseline MAE Trend", fontsize=10, fontweight='bold')
        ax.set_xlabel("Date", fontsize=9)
        ax.set_ylabel("MAE (bps)", fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)



