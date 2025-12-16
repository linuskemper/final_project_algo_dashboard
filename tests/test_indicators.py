"""Tests for indicator helper functions."""

import numpy as np
import pandas as pd

from src import indicators


def test_calculate_sma_basic():
    series = pd.Series([1, 2, 3, 4, 5])
    sma = indicators.calculate_sma(series, window=3)
    expected = pd.Series([np.nan, np.nan, 2.0, 3.0, 4.0])
    pd.testing.assert_series_equal(sma, expected)


def test_add_moving_averages_shapes():
    df = pd.DataFrame({"close": np.arange(10, dtype=float)})
    result = indicators.add_moving_averages(df, short_window=2, long_window=4)
    assert "sma_short" in result.columns
    assert "sma_long" in result.columns
    assert len(result) == len(df)


def test_kalman_trend_filter_reduces_variance():
    index = pd.date_range("2020-01-01", periods=100, freq="D")
    raw = pd.Series(np.random.randn(100).cumsum() + 100, index=index)
    trend = indicators.estimate_kalman_trend(raw)
    assert trend.std() < raw.std()
