#!/usr/bin/env python3
"""
Complete Training Pipeline
Orchestrates the full feedback loop: collect data → train models → evaluate → improve
"""

import os
import sys
import subprocess
import datetime as dt
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from collect_training_data import collect_training_data, save_training_data
from train_xgboost import train_models, load_training_data, evaluate_accuracy, save_models
from enhance_predictions import load_latest_xgb_models

def build_historical_snapshots(start_date: str, end_date: str):
    """Build yield curve snapshots for historical dates."""
    print(f"\n[STEP 1] Building yield curve snapshots from {start_date} to {end_date}...")
    
    repo_root = Path(__file__).parent.parent.parent
    snapshot_script = repo_root / "tools" / "ust_curve" / "llm" / "build_snapshots.py"
    
    if not snapshot_script.exists():
        print(f"[WARN] Snapshot script not found at {snapshot_script}")
        return
    
    start = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    current = start
    built = 0
    while current <= end:
        if current.weekday() < 5:  # Business days only
            date_str = current.isoformat()
            snapshot_path = repo_root / "tools" / "ust_curve" / "llm" / "snapshots" / f"curve_snapshot_{date_str}.json"
            
            if not snapshot_path.exists():
                print(f"  Building snapshot for {date_str}...")
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(snapshot_script),
                            "--core-module", "tools.ust_curve.curves",
                            date_str
                        ],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        built += 1
                    else:
                        print(f"    Failed: {result.stderr[:200]}")
                except Exception as e:
                    print(f"    Error: {e}")
        
        current += dt.timedelta(days=1)
    
    print(f"[STEP 1] Built {built} new snapshots")

def run_training_pipeline(start_date: str, end_date: str, threshold_mae: float = 3.0, 
                         max_iterations: int = 5):
    """Run complete training pipeline with iterative improvement."""
    
    print(f"\n{'='*70}")
    print(f"TRAINING PIPELINE: {start_date} to {end_date}")
    print(f"Target MAE threshold: {threshold_mae} bps")
    print(f"{'='*70}\n")
    
    # Step 1: Build historical snapshots if needed
    build_historical_snapshots(start_date, end_date)
    
    # Step 2: Collect training data
    print(f"\n[STEP 2] Collecting training data...")
    training_data = collect_training_data(start_date, end_date)
    
    if len(training_data) < 7:
        print(f"[ERROR] Insufficient training data: {len(training_data)} examples (need at least 7)")
        return False
    
    # Save training data
    data_path = Path(__file__).parent / f"training_data_{start_date}_{end_date}.json"
    save_training_data(training_data, data_path)
    
    # Step 3: Train models iteratively
    print(f"\n[STEP 3] Training XGBoost models...")
    
    X, y, dates = load_training_data(data_path)
    feature_names = sorted(training_data[0]["features"].keys())
    
    best_models = None
    best_evaluation = None
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration}/{max_iterations} ---")
        
        # Train models
        models = train_models(X, y, dates, test_size=0.2, use_time_split=True)
        
        if not models:
            print("[ERROR] Model training failed")
            break
        
        # Evaluate
        evaluation = evaluate_accuracy(models, threshold_mae=threshold_mae)
        
        print(f"\nEvaluation Results:")
        print(f"  Mean R²: {evaluation['overall_metrics']['mean_r2']:.3f}")
        print(f"  Mean MAE: {evaluation['overall_metrics']['mean_mae']:.3f} bps")
        print(f"  Threshold met: {evaluation['all_targets_meet_threshold']}")
        
        # Save best models
        if best_evaluation is None or evaluation['overall_metrics']['mean_r2'] > best_evaluation['overall_metrics']['mean_r2']:
            best_models = models
            best_evaluation = evaluation
        
        # Check if threshold is met
        if evaluation['all_targets_meet_threshold']:
            print(f"\n[SUCCESS] Threshold met after {iteration} iteration(s)!")
            break
        
        # If not last iteration, could adjust hyperparameters here
        if iteration < max_iterations:
            print(f"[INFO] Threshold not met. Continuing to iteration {iteration + 1}...")
    
    # Step 4: Save best models
    if best_models:
        print(f"\n[STEP 4] Saving best models...")
        date = dt.date.today().isoformat()
        save_models(best_models, feature_names, date)
        
        # Save final evaluation
        eval_path = Path(__file__).parent / "models" / f"final_evaluation_{date}.json"
        with open(eval_path, "w") as f:
            json.dump(best_evaluation, f, indent=2)
        
        print(f"[SUCCESS] Pipeline complete!")
        print(f"  Final Mean R²: {best_evaluation['overall_metrics']['mean_r2']:.3f}")
        print(f"  Final Mean MAE: {best_evaluation['overall_metrics']['mean_mae']:.3f} bps")
        print(f"  Threshold met: {best_evaluation['all_targets_meet_threshold']}")
        
        return best_evaluation['all_targets_meet_threshold']
    
    return False

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Run complete training pipeline")
    ap.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--threshold-mae", type=float, default=3.0, help="MAE threshold in bps")
    ap.add_argument("--max-iterations", type=int, default=5, help="Max training iterations")
    args = ap.parse_args()
    
    end_date = args.end_date or dt.date.today().isoformat()
    
    success = run_training_pipeline(
        args.start_date,
        end_date,
        threshold_mae=args.threshold_mae,
        max_iterations=args.max_iterations
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

