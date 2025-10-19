"""
irr_forecast.py
---------------
Forecasts 6-month probabilities of yield-curve steepening/flattening
using logistic regression on market and macro drivers.

Author: Togay Atmaca (tatmaca)
Created: 2025-10-19
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expect columns:
    ['slope_2s10s', 'fed_futures_slope', 'move_index',
     'breakeven_5y5y', 'treasury_ois_spread']
    """
    return df.dropna()


def label_targets(
    slope: pd.Series, horizon_days: int = 126, threshold: float = 25.0
) -> pd.DataFrame:
    delta = slope.shift(-horizon_days) - slope
    return pd.DataFrame(
        {
            "steep_flag": (delta >= threshold).astype(int),
            "flat_flag": (delta <= -threshold).astype(int),
        }
    )


def fit_forecast_model(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    """Standardized logistic regression pipeline."""
    pipe = Pipeline(
        [("scaler", StandardScaler()), ("logit", LogisticRegression(max_iter=1000))]
    )
    pipe.fit(X, y)
    return pipe


def forecast_probabilities(
    features: pd.DataFrame,
    slope: pd.Series,
    horizon_days: int = 126,
    threshold: float = 25.0,
) -> pd.DataFrame:
    """
    Returns predicted probabilities for steepening and flattening at each t.
    """
    labels = label_targets(slope, horizon_days, threshold)
    X = prepare_features(features).iloc[:-horizon_days]
    y_steep = labels["steep_flag"].dropna().iloc[:-horizon_days]
    y_flat = labels["flat_flag"].dropna().iloc[:-horizon_days]

    model_steep = fit_forecast_model(X, y_steep)
    model_flat = fit_forecast_model(X, y_flat)

    probs = pd.DataFrame(
        {
            "P_steep": model_steep.predict_proba(X)[:, 1],
            "P_flat": model_flat.predict_proba(X)[:, 1],
        },
        index=X.index,
    )

    return probs
