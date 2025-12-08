#!/usr/bin/env python3
"""
Accuracy Report Generation
Generates comprehensive accuracy reports with statistics and visualizations.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from calculate_prediction_accuracy import load_accuracy_history, load_tenor_accuracy_history
from visualize_accuracy import (
    plot_accuracy_over_time,
    plot_scenario_accuracy_heatmap,
    plot_tenor_accuracy,
    plot_r2_over_time,
    plot_directional_accuracy,
    plot_error_distribution,
    plot_prediction_vs_actual,
    generate_accuracy_dashboard,
    OUTPUT_DIR
)
import numpy as np


def calculate_summary_statistics(start_date: str, end_date: str) -> Dict:
    """
    Calculate summary statistics for accuracy metrics.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dictionary with summary statistics
    """
    history = load_accuracy_history(start_date, end_date)
    
    if not history:
        return {
            "total_dates": 0,
            "scenarios": [],
            "overall": {},
            "per_scenario": {},
            "per_tenor": {},
            "best_worst": {}
        }
    
    scenarios = sorted(set(r["scenario_name"] for r in history))
    dates = sorted(set(r["date"] for r in history))
    
    # Overall statistics (across all scenarios)
    all_mae = [r["mae_bps"] for r in history if r.get("mae_bps") is not None]
    all_rmse = [r["rmse_bps"] for r in history if r.get("rmse_bps") is not None]
    all_r2 = [r["r2"] for r in history if r.get("r2") is not None]
    all_dir_acc = [r["directional_accuracy"] for r in history if r.get("directional_accuracy") is not None]
    all_corr = [r["correlation"] for r in history if r.get("correlation") is not None]
    
    overall = {
        "mean_mae": float(np.mean(all_mae)) if all_mae else None,
        "mean_rmse": float(np.mean(all_rmse)) if all_rmse else None,
        "mean_r2": float(np.mean(all_r2)) if all_r2 else None,
        "mean_directional_accuracy": float(np.mean(all_dir_acc)) if all_dir_acc else None,
        "mean_correlation": float(np.mean(all_corr)) if all_corr else None,
    }
    
    # Per-scenario statistics
    per_scenario = {}
    for scenario in scenarios:
        scenario_records = [r for r in history if r["scenario_name"] == scenario]
        scenario_mae = [r["mae_bps"] for r in scenario_records if r.get("mae_bps") is not None]
        scenario_rmse = [r["rmse_bps"] for r in scenario_records if r.get("rmse_bps") is not None]
        scenario_r2 = [r["r2"] for r in scenario_records if r.get("r2") is not None]
        scenario_dir_acc = [r["directional_accuracy"] for r in scenario_records if r.get("directional_accuracy") is not None]
        
        per_scenario[scenario] = {
            "mean_mae": float(np.mean(scenario_mae)) if scenario_mae else None,
            "mean_rmse": float(np.mean(scenario_rmse)) if scenario_rmse else None,
            "mean_r2": float(np.mean(scenario_r2)) if scenario_r2 else None,
            "mean_directional_accuracy": float(np.mean(scenario_dir_acc)) if scenario_dir_acc else None,
            "num_dates": len(scenario_records)
        }
    
    # Per-tenor statistics
    tenor_history = load_tenor_accuracy_history(start_date, end_date)
    per_tenor = {}
    from train_linear_online import TENORS
    for tenor in TENORS:
        tenor_records = [r for r in tenor_history if r["tenor"] == tenor]
        tenor_errors = [abs(r["error_bps"]) for r in tenor_records if r.get("error_bps") is not None]
        if tenor_errors:
            per_tenor[tenor] = {
                "mean_abs_error": float(np.mean(tenor_errors)),
                "rmse": float(np.sqrt(np.mean([e**2 for e in tenor_errors]))),
                "num_predictions": len(tenor_errors)
            }
    
    # Best/worst performing scenarios
    best_worst = {}
    if per_scenario:
        # Best MAE
        best_mae_scenario = min(per_scenario.items(), 
                               key=lambda x: x[1]["mean_mae"] if x[1]["mean_mae"] is not None else float('inf'))
        worst_mae_scenario = max(per_scenario.items(),
                                key=lambda x: x[1]["mean_mae"] if x[1]["mean_mae"] is not None else 0)
        
        # Best R²
        best_r2_scenario = max(per_scenario.items(),
                              key=lambda x: x[1]["mean_r2"] if x[1]["mean_r2"] is not None else -1)
        
        best_worst = {
            "best_mae": {
                "scenario": best_mae_scenario[0],
                "mae": best_mae_scenario[1]["mean_mae"]
            },
            "worst_mae": {
                "scenario": worst_mae_scenario[0],
                "mae": worst_mae_scenario[1]["mean_mae"]
            },
            "best_r2": {
                "scenario": best_r2_scenario[0],
                "r2": best_r2_scenario[1]["mean_r2"]
            }
        }
    
    return {
        "total_dates": len(dates),
        "scenarios": scenarios,
        "overall": overall,
        "per_scenario": per_scenario,
        "per_tenor": per_tenor,
        "best_worst": best_worst
    }


def generate_markdown_report(start_date: str, end_date: str, stats: Dict) -> str:
    """
    Generate markdown report from statistics.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        stats: Summary statistics dictionary
    
    Returns:
        Markdown report string
    """
    report = f"""# Prediction Accuracy Report

**Date Range**: {start_date} to {end_date}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Dates**: {stats['total_dates']}
- **Scenarios Analyzed**: {len(stats['scenarios'])}

## Overall Performance

"""
    
    overall = stats.get("overall", {})
    if overall.get("mean_mae") is not None:
        report += f"- **Mean MAE**: {overall['mean_mae']:.2f} bps\n"
    if overall.get("mean_rmse") is not None:
        report += f"- **Mean RMSE**: {overall['mean_rmse']:.2f} bps\n"
    if overall.get("mean_r2") is not None:
        report += f"- **Mean R²**: {overall['mean_r2']:.3f}\n"
    if overall.get("mean_directional_accuracy") is not None:
        report += f"- **Mean Directional Accuracy**: {overall['mean_directional_accuracy']:.1f}%\n"
    if overall.get("mean_correlation") is not None:
        report += f"- **Mean Correlation**: {overall['mean_correlation']:.3f}\n"
    
    report += "\n## Performance by Scenario\n\n"
    report += "| Scenario | Mean MAE (bps) | Mean RMSE (bps) | Mean R² | Directional Accuracy (%) | Dates |\n"
    report += "|----------|----------------|-----------------|---------|------------------------|-------|\n"
    
    per_scenario = stats.get("per_scenario", {})
    for scenario in sorted(per_scenario.keys()):
        s = per_scenario[scenario]
        mae = f"{s['mean_mae']:.2f}" if s['mean_mae'] is not None else "N/A"
        rmse = f"{s['mean_rmse']:.2f}" if s['mean_rmse'] is not None else "N/A"
        r2 = f"{s['mean_r2']:.3f}" if s['mean_r2'] is not None else "N/A"
        dir_acc = f"{s['mean_directional_accuracy']:.1f}" if s['mean_directional_accuracy'] is not None else "N/A"
        num_dates = s.get("num_dates", 0)
        report += f"| {scenario} | {mae} | {rmse} | {r2} | {dir_acc} | {num_dates} |\n"
    
    report += "\n## Performance by Tenor\n\n"
    report += "| Tenor | Mean |Error| (bps) | RMSE (bps) | Predictions |\n"
    report += "|-------|-------------------|-------------|------------|\n"
    
    per_tenor = stats.get("per_tenor", {})
    for tenor in sorted(per_tenor.keys()):
        t = per_tenor[tenor]
        report += f"| {tenor} | {t['mean_abs_error']:.2f} | {t['rmse']:.2f} | {t['num_predictions']} |\n"
    
    best_worst = stats.get("best_worst", {})
    if best_worst:
        report += "\n## Best/Worst Performers\n\n"
        if "best_mae" in best_worst:
            report += f"- **Best MAE**: {best_worst['best_mae']['scenario']} ({best_worst['best_mae']['mae']:.2f} bps)\n"
        if "worst_mae" in best_worst:
            report += f"- **Worst MAE**: {best_worst['worst_mae']['scenario']} ({best_worst['worst_mae']['mae']:.2f} bps)\n"
        if "best_r2" in best_worst:
            report += f"- **Best R²**: {best_worst['best_r2']['scenario']} ({best_worst['best_r2']['r2']:.3f})\n"
    
    report += "\n## Visualizations\n\n"
    report += "Generated visualizations are available in the `accuracy_analysis/` directory:\n\n"
    report += "- `accuracy_over_time_*.png` - Accuracy metrics over time\n"
    report += "- `accuracy_heatmap_*.png` - Accuracy heatmap by scenario and date\n"
    report += "- `tenor_accuracy_*.png` - Accuracy by tenor\n"
    report += "- `accuracy_dashboard_*.png` - Comprehensive dashboard\n"
    
    return report


def generate_report(start_date: str, end_date: str) -> Dict:
    """
    Generate comprehensive accuracy report.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dictionary with report data and file paths
    """
    print(f"\n{'='*60}")
    print(f"GENERATING ACCURACY REPORT")
    print(f"{'='*60}")
    print(f"Date range: {start_date} to {end_date}\n")
    
    # Calculate statistics
    print("Calculating summary statistics...")
    stats = calculate_summary_statistics(start_date, end_date)
    
    # Generate visualizations
    print("Generating visualizations...")
    viz_files = {}
    
    try:
        viz_files["mae_over_time"] = plot_accuracy_over_time(start_date, end_date, "mae_bps")
        print("  ✓ MAE over time")
    except Exception as e:
        print(f"  ✗ MAE over time: {e}")
    
    try:
        viz_files["rmse_over_time"] = plot_accuracy_over_time(start_date, end_date, "rmse_bps")
        print("  ✓ RMSE over time")
    except Exception as e:
        print(f"  ✗ RMSE over time: {e}")
    
    try:
        viz_files["r2_over_time"] = plot_r2_over_time(start_date, end_date)
        print("  ✓ R² over time")
    except Exception as e:
        print(f"  ✗ R² over time: {e}")
    
    try:
        viz_files["directional_accuracy"] = plot_directional_accuracy(start_date, end_date)
        print("  ✓ Directional accuracy")
    except Exception as e:
        print(f"  ✗ Directional accuracy: {e}")
    
    try:
        viz_files["accuracy_heatmap"] = plot_scenario_accuracy_heatmap(start_date, end_date, "mae_bps")
        print("  ✓ Accuracy heatmap")
    except Exception as e:
        print(f"  ✗ Accuracy heatmap: {e}")
    
    try:
        viz_files["tenor_accuracy"] = plot_tenor_accuracy(start_date, end_date, "mae_bps")
        print("  ✓ Tenor accuracy")
    except Exception as e:
        print(f"  ✗ Tenor accuracy: {e}")
    
    try:
        viz_files["error_distribution"] = plot_error_distribution(start_date, end_date)
        print("  ✓ Error distribution")
    except Exception as e:
        print(f"  ✗ Error distribution: {e}")
    
    try:
        viz_files["dashboard"] = generate_accuracy_dashboard(start_date, end_date)
        print("  ✓ Accuracy dashboard")
    except Exception as e:
        print(f"  ✗ Accuracy dashboard: {e}")
    
    # Generate markdown report
    print("\nGenerating markdown report...")
    markdown_report = generate_markdown_report(start_date, end_date, stats)
    
    # Save files
    report_date_str = f"{start_date}_{end_date}"
    md_path = OUTPUT_DIR / f"accuracy_report_{report_date_str}.md"
    json_path = OUTPUT_DIR / f"accuracy_report_{report_date_str}.json"
    
    with open(md_path, 'w') as f:
        f.write(markdown_report)
    print(f"  ✓ Markdown report: {md_path}")
    
    report_data = {
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": datetime.now().isoformat(),
        "statistics": stats,
        "visualizations": {k: str(v) if v else None for k, v in viz_files.items()}
    }
    
    with open(json_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    print(f"  ✓ JSON report: {json_path}")
    
    print(f"\n{'='*60}")
    print("REPORT GENERATION COMPLETE")
    print(f"{'='*60}\n")
    
    return report_data


def main():
    """Main entry point for report generation."""
    ap = argparse.ArgumentParser(
        description="Generate accuracy report with statistics and visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for date range
  python3 generate_accuracy_report.py --start-date 2025-11-06 --end-date 2025-12-04
        """
    )
    
    ap.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)"
    )
    
    ap.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)"
    )
    
    args = ap.parse_args()
    
    # Validate dates
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"[ERROR] Invalid date format: {e}")
        print("Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    if args.start_date > args.end_date:
        print("[ERROR] Start date must be before or equal to end date")
        sys.exit(1)
    
    # Generate report
    generate_report(args.start_date, args.end_date)


if __name__ == "__main__":
    import numpy as np
    main()

