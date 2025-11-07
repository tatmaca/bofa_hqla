#!/usr/bin/env python3
"""
Daily Pipeline Runner with Logging
Runs the daily pipeline and logs output to a file.
Designed to be called by cron or scheduler.
"""

import os
import sys
import datetime as dt
from pathlib import Path
import subprocess

# Get script directory
SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def main():
    # Get today's date
    today = dt.date.today()
    date_str = today.isoformat()
    
    # Log file with date
    log_file = LOG_DIR / f"daily_pipeline_{date_str}.log"
    
    # Run pipeline and capture output
    print(f"Running daily pipeline for {date_str}...")
    print(f"Logging to: {log_file}")
    
    try:
        # Run the pipeline
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "daily_pipeline.py")],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Write output to log file
        with open(log_file, "w") as f:
            f.write(f"Daily Pipeline Run - {date_str}\n")
            f.write(f"Started: {dt.datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\nSTDERR:\n")
                f.write(result.stderr)
            f.write(f"\n\nExit code: {result.returncode}\n")
            f.write(f"Completed: {dt.datetime.now().isoformat()}\n")
        
        # Print summary
        print(f"Pipeline completed with exit code: {result.returncode}")
        print(f"Output logged to: {log_file}")
        
        # Return exit code
        sys.exit(result.returncode)
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Pipeline timed out after 1 hour")
        with open(log_file, "w") as f:
            f.write(f"ERROR: Pipeline timed out\n")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        with open(log_file, "w") as f:
            f.write(f"ERROR: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

