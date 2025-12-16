"""Indicator calculation utilities for the trading strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """
    Calculate a simple moving average for a price series.
    """
    return series.rolling(window=window, min_periods=window).mean()


def calculate_bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands for a price series.
    """
    middle = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)

    return pd.DataFrame(
        {"bb_middle": middle, "bb_upper": upper, "bb_lower": lower}, index=series.index
    )


def add_moving_averages(
    data: pd.DataFrame,
    short_window: int = 5,
    long_window: int = 50,
) -> pd.DataFrame:
    """
    Add short and long simple moving averages to the data frame.
    """
    result = data.copy()
    result["sma_short"] = calculate_sma(result["close"], short_window)
    result["sma_long"] = calculate_sma(result["close"], long_window)
    return result


def add_bollinger_bands(
    data: pd.DataFrame, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """
    Add Bollinger Bands to the data frame.
    """
    result = data.copy()
    bands = calculate_bollinger_bands(result["close"], window, num_std)
    result = pd.concat([result, bands], axis=1)
    return result


def estimate_kalman_trend(
    series: pd.Series,
    process_variance: float = 1e-5,
    measurement_variance: float = 1e-2,
    initial_estimate_variance: float = 1.0,
) -> pd.Series:
    """
    Estimate the trend of a series using a simple 1D Kalman filter.
    """
    values = series.to_numpy(dtype=float)
    n_obs = values.size

    if n_obs == 0:
        return series.copy()

    estimates = np.empty(n_obs, dtype=float)

    estimate = values[0]
    estimate_variance = float(initial_estimate_variance)
    estimates[0] = estimate

    for i in range(1, n_obs):
        # Predict
        estimate_variance += process_variance

        # Update
        kalman_gain = estimate_variance / (estimate_variance + measurement_variance)
        estimate += kalman_gain * (values[i] - estimate)
        estimate_variance *= 1.0 - kalman_gain

        estimates[i] = estimate

    return pd.Series(estimates, index=series.index, name="kalman_trend")



def add_kalman_trend(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add a Kalman-filter-based trend estimate to the data frame.
    """
    result = data.copy()
    result["kalman_trend"] = estimate_kalman_trend(result["close"])
    return result
