#!/bin/bash
# Fix NumPy compatibility in conda environment
# Run this in your conda base environment

echo "Fixing NumPy compatibility for XGBoost/SciPy..."
echo "Current environment: $CONDA_DEFAULT_ENV"
echo ""

# Downgrade NumPy to <2.0
echo "[1/2] Downgrading NumPy to <2.0..."
conda install -y "numpy>=1.24.0,<2.0.0" -c conda-forge

# Reinstall SciPy and XGBoost to ensure compatibility
echo ""
echo "[2/2] Reinstalling SciPy and XGBoost for compatibility..."
conda install -y scipy xgboost -c conda-forge

echo ""
echo "Verifying installation..."
python3 -c "import numpy as np; print(f'✓ NumPy {np.__version__}')"
python3 -c "import scipy; print(f'✓ SciPy {scipy.__version__}')"
python3 -c "import xgboost as xgb; print(f'✓ XGBoost {xgb.__version__}')" 2>/dev/null || echo "⚠ XGBoost may need OpenMP: brew install libomp"

echo ""
echo "Done! Try running the pipeline again."

