"""Trading strategy logic and signal generation."""

from __future__ import annotations
from typing import Tuple
import pandas as pd
from .sentiment import is_extreme_fear, is_extreme_greed


def generate_positions(
    data: pd.DataFrame,
    short_ma_col: str = "sma_short",
    long_ma_col: str = "sma_long",
    trend_col: str = "kalman_trend",
    sentiment_col: str = "sentiment_regime",
) -> pd.DataFrame:
    """
    Generate long/flat positions based on price indicators and sentiment.
    """
    result = data.copy()

    short_ma = result[short_ma_col]
    long_ma = result[long_ma_col]
    trend = result[trend_col]
    sentiment = result[sentiment_col]

    positions = []
    current_position = 0

    for idx in result.index:
        enter_long = (
            (short_ma.loc[idx] > long_ma.loc[idx])
            and (trend.loc[idx] > 0)
            and not is_extreme_greed(sentiment.loc[idx])
        )

        exit_or_avoid = (
            (short_ma.loc[idx] < long_ma.loc[idx])
            or is_extreme_fear(sentiment.loc[idx])
        )

        if enter_long:
            current_position = 1
        elif exit_or_avoid:
            current_position = 0

        positions.append(current_position)

    result["position"] = positions
    return result

def generate_trade_signals(data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert position changes into buy and sell signals.
    """
    result = data.copy()
    prev_position = result["position"].shift(1).fillna(0)

    buy_mask = (prev_position == 0) & (result["position"] == 1)
    sell_mask = (prev_position == 1) & (result["position"] == 0)

    result["trade_signal"] = "Hold"
    result.loc[buy_mask, "trade_signal"] = "Buy"
    result.loc[sell_mask, "trade_signal"] = "Sell"
    return result

def get_latest_recommendation(data: pd.DataFrame) -> Tuple[str, str]:
    """
    Return the latest trade recommendation and a short explanation.
    """
    if data.empty:
        return "Hold", "No data available."

    last_row = data.iloc[-1]
    signal = str(last_row["trade_signal"])

    if signal == "Buy":
        explanation = (
            "Entry signal: positive momentum, positive trend, and "
            "no extreme greed in sentiment."
        )
    elif signal == "Sell":
        explanation = (
            "Exit signal: weakening momentum or extreme fear in sentiment."
        )
    else:
        explanation = (
            "No new signal: keep the current position until conditions change."
        )

    return signal, explanation