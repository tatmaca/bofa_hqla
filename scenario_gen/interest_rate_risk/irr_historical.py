"""
irr_historical.py
-----------------
Computes empirical probabilities of yield-curve steepening and flattening
over a specified horizon.

Author: Togay Atmaca (tatmaca)
Created: 2025-10-19
"""

import pandas as pd
import numpy as np


def compute_2s10s(yield_2y: pd.Series, yield_10y: pd.Series) -> pd.Series:
    """Return 2s10s spread in basis points."""
    return (yield_10y - yield_2y) * 100  # convert to bps


def historical_probabilities(
    spread: pd.Series,
    horizon_days: int = 126,
    threshold: float = 25.0,
    n_bootstrap: int = 1000,
) -> dict:
    """
    Estimate historical probability of steepening / flattening.

    Parameters
    ----------
    spread : pd.Series
        Time series of 2s10s spread in basis points.
    horizon_days : int
        Rolling window length (≈6 months).
    threshold : float
        Absolute threshold for defining event.
    n_bootstrap : int
        Number of bootstrap resamples for confidence intervals.
    """
    delta = spread.shift(-horizon_days) - spread
    steep = (delta >= threshold).mean()
    flat = (delta <= -threshold).mean()

    # bootstrap confidence intervals
    boot_steep, boot_flat = [], []
    for _ in range(n_bootstrap):
        sample = delta.sample(frac=1, replace=True)
        boot_steep.append((sample >= threshold).mean())
        boot_flat.append((sample <= -threshold).mean())

    ci = lambda x: (np.percentile(x, 2.5), np.percentile(x, 97.5))
    return {
        "steepening_prob": steep,
        "flattening_prob": flat,
        "steepening_ci": ci(boot_steep),
        "flattening_ci": ci(boot_flat),
    }
