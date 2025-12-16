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


def get_latest_recommendation(df):
    """Returns the latest signal and a brief explanation."""
    if df.empty:
        return "Unknown", "No data available."
        
    last_row = df.iloc[-1]
    signal = last_row.get('trade_signal', 'Hold')
    
    sma_s = last_row.get('sma_short', 0)
    sma_l = last_row.get('sma_long', 0)
    
    explanation = f"Short SMA ({sma_s:.2f}) vs Long SMA ({sma_l:.2f})."
    return signal, explanation