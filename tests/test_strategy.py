"""Tests for trading strategy signal generation."""

import pandas as pd

from src import strategy


def _build_simple_data():
    index = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "close": [100, 102, 104, 103, 105],
            "sma_short": [100, 101, 102, 103, 104],
            "sma_long": [100, 100, 100, 100, 100],
            "kalman_trend": [0.1, 0.2, 0.3, 0.1, 0.2],
            "sentiment_regime": [
                "Neutral",
                "Neutral",
                "Neutral",
                "Neutral",
                "Neutral",
            ],
        },
        index=index,
    )
    return df


def test_generate_positions_long_when_conditions_met():
    df = _build_simple_data()
    result = strategy.generate_positions(df)
    assert result["position"].iloc[-1] == 1


def test_generate_trade_signals_buy_and_sell():
    df = _build_simple_data()
    df.loc[df.index[-1], "sma_short"] = 90
    with_positions = strategy.generate_positions(df)
    with_signals = strategy.generate_trade_signals(with_positions)

    assert "Buy" in with_signals["trade_signal"].values
    assert "Sell" in with_signals["trade_signal"].values
