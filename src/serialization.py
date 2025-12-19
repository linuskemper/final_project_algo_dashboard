import pandas as pd
from typing import List, Dict

def _to_list_handle_nan(series: pd.Series) -> List:
    """ Converts a Pandas Series to a list, handling NaNs by replacing them """
    return [None if pd.isna(x) else x for x in series.tolist()]

def serialize_time_series(data: pd.DataFrame) -> Dict[str, List]:
    """
    Serializes time-series data and indicators into a format suitable for JSON API responses.

    Parameters:
        data: pd.DataFrame containing "close", "sma_short", "sma_long",
        "kalman_trend", "position" and "trade_signal".

    Returns:
        Dict: Names with all the parameters
    """
    df = data.copy()
    df = df.sort_index()

    # Create valid date string
    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    payload = {
        "dates": dates,
        "close": _to_list_handle_nan(df["close"].round(2)),
        "sma_short": _to_list_handle_nan(df["sma_short"].round(2)),
        "sma_long": _to_list_handle_nan(df["sma_long"].round(2)),
        "bb_middle": _to_list_handle_nan(df["bb_middle"].round(2)),
        "bb_upper": _to_list_handle_nan(df["bb_upper"].round(2)),
        "bb_lower": _to_list_handle_nan(df["bb_lower"].round(2)),
        "kalman_trend": _to_list_handle_nan(df["kalman_trend"].round(2)),
        "position": df["position"].fillna(0).astype(int).tolist(),
        "trade_signal": df["trade_signal"].fillna("Hold").astype(str).tolist()
    }

    buy_indices = [
        i for i, signal in enumerate(payload["trade_signal"]) if signal == "Buy"
    ]
    sell_indices = [
        i for i, signal in enumerate(payload["trade_signal"]) if signal == "Sell"
    ]

    payload["buy_indices"] = buy_indices
    payload["sell_indices"] = sell_indices

    return payload

def serialize_sentiment(data: pd.DataFrame) -> Dict[str, List]:
    """
    Serializes sentiment data for API responses.

    Args:
        data: DataFrame with 'fg_value' and 'sentiment_regime' over dates.

    Returns:
        Dict: Sentiment time series
    """
    df = data.copy()
    df = df.sort_index()

    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    payload = {
        "dates": dates,
        "fg_value": _to_list_handle_nan(df["fg_value"].round(0)),
        "sentiment_regime": (
            df["sentiment_regime"].fillna("Unknown").astype(str).tolist()
        )
    }
    return payload

def serialize_performance(data: pd.DataFrame, metrics: Dict[str, float]) -> Dict:
    """
    Serializes strategy performance data and metrics for API responses.

    Args:
        data: DataFrame containing 'strategy_equity' and 'benchmark_equity' columns.
        metrics: Dictionary of calculated performance metrics.

    Returns:
        Dict: Combined performance payload.
    """
    df = data.copy()
    df = df.sort_index()

    dates = [idx.strftime("%Y-%m-%d") for idx in df.index]

    payload = {
        "dates": dates,
        "strategy_equity": _to_list_handle_nan(df["strategy_equity"].round(3)),
        "benchmark_equity": _to_list_handle_nan(df["benchmark_equity"].round(3)),
        "metrics": metrics
    }
    return payload