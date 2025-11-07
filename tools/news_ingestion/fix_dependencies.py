#!/usr/bin/env python3
"""
Fix Dependencies Script
Fixes NumPy/XGBoost compatibility issues and OpenMP on macOS.
"""

import subprocess
import sys
import platform

def fix_dependencies():
    """Fix NumPy version compatibility and OpenMP."""
    print("Fixing dependencies for XGBoost training...")
    
    # Check if macOS
    is_macos = platform.system() == "Darwin"
    
    if is_macos:
        print("\n[1/3] Checking for OpenMP (required for XGBoost on macOS)...")
        try:
            # Check if libomp is installed
            result = subprocess.run(["brew", "list", "libomp"], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                print("  OpenMP not found. Installing via Homebrew...")
                print("  Run: brew install libomp")
                print("  Or install XGBoost with conda: conda install -c conda-forge xgboost")
            else:
                print("  ✓ OpenMP found")
        except FileNotFoundError:
            print("  ⚠ Homebrew not found. Install OpenMP manually:")
            print("    brew install libomp")
            print("  Or use conda: conda install -c conda-forge xgboost")
    
    print("\n[2/3] Fixing NumPy version (downgrading to <2.0.0)...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "numpy>=1.24.0,<2.0.0", "--upgrade", "--quiet"
        ], check=True)
        print("  ✓ NumPy downgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to downgrade NumPy: {e}")
        return False
    
    print("\n[3/3] Installing/upgrading XGBoost...")
    try:
        # Try pip first
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "xgboost>=2.0.0", "--upgrade", "--quiet"
        ], check=True)
        print("  ✓ XGBoost installed/upgraded")
    except subprocess.CalledProcessError:
        print("  ⚠ Pip install failed. Try conda:")
        print("    conda install -c conda-forge xgboost")
        return False
    
    print("\n[VERIFY] Verifying installation...")
    try:
        import numpy as np
        print(f"  ✓ NumPy {np.__version__}")
        
        try:
            import xgboost as xgb
            print(f"  ✓ XGBoost {xgb.__version__}")
            return True
        except Exception as e:
            if is_macos and "libomp" in str(e):
                print(f"  ✗ XGBoost import failed: OpenMP not found")
                print("\n[FIX] Install OpenMP:")
                print("  brew install libomp")
                print("\nOr use conda (handles OpenMP automatically):")
                print("  conda install -c conda-forge xgboost")
            else:
                print(f"  ✗ XGBoost import failed: {e}")
            return False
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_dependencies()
    if not success:
        print("\n[INFO] If XGBoost still fails, try:")
        print("  1. Install OpenMP: brew install libomp")
        print("  2. Or use conda: conda install -c conda-forge xgboost")
    sys.exit(0 if success else 1)

