"""Helpers to convert analysis results into JSON-ready structures."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd


def _to_list_handle_nan(series: pd.Series) -> List:
    """Convert a pandas Series to a list, replacing NaNs with None."""
    return [None if pd.isna(x) else x for x in series.tolist()]


def _optional_series(
    df: pd.DataFrame, column: str, decimals: int = 2
) -> List:
    if column not in df.columns:
        return [None] * len(df)
    return _to_list_handle_nan(df[column].round(decimals))


def serialize_time_series(data: pd.DataFrame) -> Dict[str, List]:
    """
    Serialize main time series data for interactive charts.
    """
    df = data.copy()
    df = df.sort_index()

    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    # Ensure we handle potential NaNs (e.g. from rolling windows)
    # by converting them to None, which becomes Valid JSON 'null'.
    payload = {
        "dates": dates,
        "close": _to_list_handle_nan(df["close"].round(2)),
        "sma_short": _to_list_handle_nan(df["sma_short"].round(2)),
        "sma_long": _to_list_handle_nan(df["sma_long"].round(2)),
        "bb_middle": _optional_series(df, "bb_middle"),
        "bb_upper": _optional_series(df, "bb_upper"),
        "bb_lower": _optional_series(df, "bb_lower"),
        "kalman_trend": _to_list_handle_nan(df["kalman_trend"].round(2)),
        "position": df["position"].fillna(0).astype(int).tolist(),
        "trade_signal": df["trade_signal"].fillna("Hold").astype(str).tolist(),
    }

    buy_indices = [
        i for i, signal in enumerate(payload["trade_signal"])
        if signal == "Buy"
    ]
    sell_indices = [
        i for i, signal in enumerate(payload["trade_signal"])
        if signal == "Sell"
    ]

    payload["buy_indices"] = buy_indices
    payload["sell_indices"] = sell_indices
    return payload


def serialize_sentiment(data: pd.DataFrame) -> Dict[str, List]:
    """
    Serialize sentiment data for interactive charts.
    """
    df = data.copy()
    df = df.sort_index()

    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    payload = {
        "dates": dates,
        "fg_value": _to_list_handle_nan(df["fg_value"].round(0)),
        "sentiment_regime": (
            df["sentiment_regime"].fillna("Unknown").astype(str).tolist()
        ),
    }
    return payload


def serialize_performance(
    data: pd.DataFrame, metrics: Dict[str, float]
) -> Dict:
    """
    Serialize performance curves and summary metrics.
    """
    df = data.copy()
    df = df.sort_index()

    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    payload = {
        "dates": dates,
        "strategy_equity": _to_list_handle_nan(
            df["strategy_equity"].round(3)
        ),
        "benchmark_equity": _to_list_handle_nan(
            df["benchmark_equity"].round(3)
        ),
        "metrics": metrics,
    }
    return payload
