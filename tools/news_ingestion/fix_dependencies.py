#!/usr/bin/env python3
"""
Fix Dependencies Script
Fixes NumPy/XGBoost compatibility issues.
"""

import subprocess
import sys

def fix_dependencies():
    """Fix NumPy version compatibility."""
    print("Fixing NumPy/XGBoost compatibility...")
    print("Current NumPy version may be incompatible with XGBoost.")
    print("Downgrading NumPy to <2.0.0...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "numpy>=1.24.0,<2.0.0", "--upgrade"
        ], check=True)
        print("✓ NumPy downgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to downgrade NumPy: {e}")
        return False
    
    print("\nInstalling/upgrading XGBoost...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "xgboost>=2.0.0", "--upgrade"
        ], check=True)
        print("✓ XGBoost installed/upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install XGBoost: {e}")
        return False
    
    print("\nVerifying installation...")
    try:
        import numpy as np
        import xgboost as xgb
        print(f"✓ NumPy {np.__version__}")
        print(f"✓ XGBoost {xgb.__version__}")
        return True
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_dependencies()
    sys.exit(0 if success else 1)

