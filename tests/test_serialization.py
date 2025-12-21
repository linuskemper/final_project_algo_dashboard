"""Tests for serialization helpers."""

import numpy as np
import pandas as pd

from src import serialization


def _build_enriched_frame():
    index = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "close": np.linspace(100, 110, 5),
            "sma_short": np.linspace(100, 110, 5),
            "sma_long": np.linspace(100, 110, 5),
            "kalman_trend": np.linspace(100, 110, 5),
            "position": [0, 1, 1, 0, 0],
            "trade_signal": ["Hold", "Buy", "Hold", "Sell", "Hold"],
            "fg_value": [20, 30, 40, 60, 80],
            "sentiment_regime": [
                "Extreme Fear",
                "Fear",
                "Neutral",
                "Greed",
                "Extreme Greed",
            ],
            "strategy_equity": np.linspace(1.0, 1.2, 5),
            "benchmark_equity": np.linspace(1.0, 1.3, 5),
        },
        index=index,
    )
    return df


def test_serialize_time_series_structure():
    df = _build_enriched_frame()
    payload = serialization.serialize_time_series(df)
    assert "dates" in payload
    assert "close" in payload
    assert len(payload["dates"]) == len(df)


def test_serialize_sentiment_structure():
    df = _build_enriched_frame()
    payload = serialization.serialize_sentiment(df)
    assert "fg_value" in payload
    assert len(payload["fg_value"]) == len(df)


def test_serialize_performance_structure():
    df = _build_enriched_frame()
    metrics = {"strategy_cumulative_return": 0.1}
    payload = serialization.serialize_performance(df, metrics)
    assert "strategy_equity" in payload
    assert payload["metrics"]["strategy_cumulative_return"] == 0.1
