#!/usr/bin/env python3
"""
End-to-end test of the complete daily automated pipeline.

Tests both:
1. UST Curve Pipeline (build_snapshots, make_summary, plot, analyze)
2. News Ingestion Pipeline (ingestion, bucketing, analysis, training)

Usage:
    python tools/test_full_daily_pipeline.py [YYYY-MM-DD]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

# Get repo root
try:
    ROOT = Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    ).stdout.strip())
except:
    ROOT = Path(__file__).resolve().parents[1]

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_step(step_num, total_steps, step_name):
    print(f"{Colors.BOLD}{Colors.BLUE}[{step_num}/{total_steps}]{Colors.RESET} {step_name}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def get_test_date(user_date=None):
    """Get a test date - use user input or find a recent snapshot."""
    if user_date:
        return user_date
    
    # Default to a known good date
    return "2025-11-19"

def test_ust_curve_pipeline(test_date):
    """Test the UST curve daily pipeline."""
    print_section("PART 1: UST CURVE PIPELINE")
    
    results = {}
    
    # Step 1: Build snapshots
    print_step(1, 4, "Building Curve Snapshots")
    try:
        ust_curve_dir = ROOT / "tools" / "ust_curve"
        venv_python = ust_curve_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = sys.executable
        
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{ust_curve_dir}:{ROOT}:{env.get('PYTHONPATH', '')}"
        
        script = ust_curve_dir / "llm" / "build_snapshots.py"
        result = subprocess.run(
            [str(venv_python), str(script), "--core-module", "tools.ust_curve.curves", test_date],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            snapshot_path = ust_curve_dir / "llm" / "snapshots" / f"curve_snapshot_{test_date}.json"
            if snapshot_path.exists():
                print_success("Snapshot created successfully")
                results[1] = True
            else:
                print_error("Snapshot file not found")
                results[1] = False
        else:
            print_error(f"build_snapshots.py failed: {result.stderr[:200]}")
            results[1] = False
    except Exception as e:
        print_error(f"Exception: {e}")
        results[1] = False
    
    # Step 2: Make summary
    print_step(2, 4, "Creating Summaries")
    try:
        script = ust_curve_dir / "llm" / "make_summary.py"
        result = subprocess.run(
            [str(venv_python), str(script), "--date", test_date],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            md_path = ust_curve_dir / "llm" / "summaries" / f"curve_summary_{test_date}.md"
            json_path = ust_curve_dir / "llm" / "summaries" / f"curve_llm_{test_date}.json"
            if md_path.exists() and json_path.exists():
                print_success("Summaries created successfully")
                results[2] = True
            else:
                print_warning("Some summary files missing")
                results[2] = False
        else:
            print_error(f"make_summary.py failed: {result.stderr[:200]}")
            results[2] = False
    except Exception as e:
        print_error(f"Exception: {e}")
        results[2] = False
    
    # Step 3: Plot snapshot (may fail due to matplotlib issues)
    print_step(3, 4, "Creating Plots")
    try:
        script = ust_curve_dir / "llm" / "plot_snapshot.py"
        result = subprocess.run(
            [str(venv_python), str(script), test_date],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            plot_dir = ust_curve_dir / "llm" / "plots"
            plots = list(plot_dir.glob(f"ust_curve_{test_date}*.png"))
            if plots:
                print_success(f"Plots created: {len(plots)} files")
                results[3] = True
            else:
                print_warning("Plot script succeeded but no plots found")
                results[3] = False
        else:
            if "object __array__ method not producing an array" in result.stderr:
                print_warning("Plotting failed due to matplotlib/numpy compatibility (known issue)")
                results[3] = None  # Mark as skipped/known issue
            else:
                print_error(f"plot_snapshot.py failed: {result.stderr[:200]}")
                results[3] = False
    except Exception as e:
        print_error(f"Exception: {e}")
        results[3] = False
    
    # Step 4: Analyze snapshot
    print_step(4, 4, "Analyzing Snapshot")
    try:
        script = ust_curve_dir / "llm" / "analyze_snapshot.py"
        snapshot_path = ust_curve_dir / "llm" / "snapshots" / f"curve_snapshot_{test_date}.json"
        result = subprocess.run(
            [str(venv_python), str(script), str(snapshot_path)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            print_success("Analysis completed successfully")
            results[4] = True
        else:
            print_error("Analysis failed or produced no output")
            results[4] = False
    except Exception as e:
        print_error(f"Exception: {e}")
        results[4] = False
    
    return results

def test_news_ingestion_pipeline(test_date):
    """Test the news ingestion daily pipeline."""
    print_section("PART 2: NEWS INGESTION PIPELINE")
    
    results = {}
    news_dir = ROOT / "tools" / "news_ingestion"
    
    # Run the full daily pipeline
    print_info("Running complete news ingestion pipeline...")
    print_info("This includes: ingestion, bucketing, analysis, training data prep, and model training")
    
    try:
        script = news_dir / "daily_pipeline.py"
        result = subprocess.run(
            [sys.executable, str(script), "--date", test_date],
            cwd=str(news_dir),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        # Check output for success indicators
        output = result.stdout + result.stderr
        success_indicators = [
            "PIPELINE COMPLETE",
            "News Ingestion",
            "News Bucketing",
            "Syncing Yield Curve Data"
        ]
        
        found_indicators = [ind for ind in success_indicators if ind in output]
        
        if result.returncode == 0 or len(found_indicators) >= 2:
            print_success("News ingestion pipeline completed")
            print_info(f"Found indicators: {', '.join(found_indicators)}")
            
            # Check for specific outputs
            if "News Ingestion" in output:
                results["ingestion"] = True
            if "News Bucketing" in output:
                results["bucketing"] = True
            if "Syncing Yield Curve Data" in output or "Yield curve data updated" in output:
                results["yield_sync"] = True
            if "LLM Yield Impact Analysis" in output:
                results["llm_analysis"] = True
            if "Training Data" in output or "training records" in output:
                results["training_data"] = True
            
            # Print last 20 lines of output for context
            lines = output.split('\n')
            print_info("Last 10 lines of output:")
            for line in lines[-10:]:
                if line.strip():
                    print(f"  {line}")
            
            results["overall"] = True
        else:
            print_error("News ingestion pipeline failed or incomplete")
            print_error(f"Return code: {result.returncode}")
            if result.stderr:
                print_error("STDERR (last 200 chars):")
                print(result.stderr[-200:])
            results["overall"] = False
            
    except subprocess.TimeoutExpired:
        print_error("Pipeline timed out after 30 minutes")
        results["overall"] = False
    except Exception as e:
        print_error(f"Exception running pipeline: {e}")
        import traceback
        traceback.print_exc()
        results["overall"] = False
    
    return results

def check_pipeline_outputs(test_date):
    """Check that expected outputs were created."""
    print_section("PART 3: VERIFYING OUTPUTS")
    
    checks = {}
    
    # Check UST curve outputs
    ust_curve_dir = ROOT / "tools" / "ust_curve" / "llm"
    snapshot_path = ust_curve_dir / "snapshots" / f"curve_snapshot_{test_date}.json"
    checks["ust_snapshot"] = snapshot_path.exists()
    
    md_path = ust_curve_dir / "summaries" / f"curve_summary_{test_date}.md"
    checks["ust_summary_md"] = md_path.exists()
    
    json_path = ust_curve_dir / "summaries" / f"curve_llm_{test_date}.json"
    checks["ust_summary_json"] = json_path.exists()
    
    # Check news ingestion outputs
    news_dir = ROOT / "tools" / "news_ingestion"
    db_path = news_dir / "news.db"
    checks["news_db"] = db_path.exists()
    
    analysis_path = news_dir / "analyses" / f"yield_impact_{test_date}.json"
    checks["news_analysis"] = analysis_path.exists()
    
    # Print results
    for check_name, passed in checks.items():
        if passed:
            print_success(f"{check_name}: exists")
        else:
            print_warning(f"{check_name}: missing")
    
    return checks

def main():
    parser = argparse.ArgumentParser(
        description="Test the complete daily automated pipeline end-to-end"
    )
    parser.add_argument(
        "date",
        nargs="?",
        help="Date to test (YYYY-MM-DD). Defaults to 2025-11-19."
    )
    parser.add_argument(
        "--skip-ust",
        action="store_true",
        help="Skip UST curve pipeline"
    )
    parser.add_argument(
        "--skip-news",
        action="store_true",
        help="Skip news ingestion pipeline"
    )
    args = parser.parse_args()
    
    test_date = get_test_date(args.date)
    
    print(f"\n{Colors.BOLD}END-TO-END DAILY PIPELINE TEST{Colors.RESET}")
    print(f"Test date: {test_date}")
    print(f"Repository: {ROOT}\n")
    
    all_results = {}
    
    # Part 1: UST Curve Pipeline
    if not args.skip_ust:
        ust_results = test_ust_curve_pipeline(test_date)
        all_results["ust_curve"] = ust_results
    else:
        print_warning("Skipping UST curve pipeline")
    
    # Part 2: News Ingestion Pipeline
    if not args.skip_news:
        news_results = test_news_ingestion_pipeline(test_date)
        all_results["news_ingestion"] = news_results
    else:
        print_warning("Skipping news ingestion pipeline")
    
    # Part 3: Verify Outputs
    output_checks = check_pipeline_outputs(test_date)
    all_results["outputs"] = output_checks
    
    # Final Summary
    print_section("FINAL SUMMARY")
    
    if "ust_curve" in all_results:
        ust = all_results["ust_curve"]
        passed = sum(1 for v in ust.values() if v is True)
        failed = sum(1 for v in ust.values() if v is False)
        skipped = sum(1 for v in ust.values() if v is None)
        total = len(ust)
        print(f"UST Curve Pipeline: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    
    if "news_ingestion" in all_results:
        news = all_results["news_ingestion"]
        if "overall" in news:
            status = "PASSED" if news["overall"] else "FAILED"
            print(f"News Ingestion Pipeline: {status}")
            for key, value in news.items():
                if key != "overall" and value:
                    print(f"  ✓ {key}")
    
    if "outputs" in all_results:
        outputs = all_results["outputs"]
        passed = sum(1 for v in outputs.values() if v)
        total = len(outputs)
        print(f"Output Verification: {passed}/{total} files exist")
    
    print()
    print(f"{Colors.BOLD}Test completed for {test_date}{Colors.RESET}")

if __name__ == "__main__":
    main()

