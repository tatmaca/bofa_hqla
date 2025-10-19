"""
base.py
-------
Base utilities and constants for HQLA risk metrics.

Author: Togay Atmaca
Created: 2025-10-19
"""

from typing import Dict

# Liquidity coverage ratios (LCR) for HQLA asset classes
# Example regulatory haircuts (simple version)
LCR_LIQUIDITY_FACTORS: Dict[str, float] = {
    "L1": 1.0,  # Level 1 HQLA, cash & UST
    "L2A": 0.85,  # Level 2A HQLA
    "L2B": 0.50,  # Level 2B HQLA
}

# Risk weights for RWA calculation (simplified)
RWA_WEIGHTS: Dict[str, float] = {"L1": 0.0, "L2A": 0.2, "L2B": 0.5}


# Utility function
def clamp(x, min_val, max_val):
    return max(min(x, max_val), min_val)
