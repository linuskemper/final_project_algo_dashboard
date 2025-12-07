from __future__ import annotations
import pandas as pd

def classify_sentiment_value(
    value: float,
    extreme_fear_threshold: int = 25,
    extreme_greed_threshold: int = 75,
) -> str:
    """
    Classify a Fear & Greed index value into qualitative regimes.

    Parameters
    ----------
    value:
        Numeric Fear & Greed index value.
    extreme_fear_threshold:
        Threshold below which the market is considered in extreme fear.
    extreme_greed_threshold:
        Threshold above which the market is considered in extreme greed.

    Returns

    str
        One of 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'.
    """
    if value <= extreme_fear_threshold:
        return "Extreme Fear"
    if value < 45:
        return "Fear"
    if value <= 55:
        return "Neutral"
    if value < extreme_greed_threshold:
        return "Greed"
    return "Extreme Greed"

def add_sentiment_regime(
    data: pd.DataFrame,
    extreme_fear_threshold: int = 25,
    extreme_greed_threshold: int = 75,
) -> pd.DataFrame:
    """
    Add a qualitative sentiment regime column to a merged data frame.

    Parameters
    ----------
    data:
        Data frame with a numeric 'fg_value' column.
    extreme_fear_threshold:
        Threshold below which the market is considered in extreme fear.
    extreme_greed_threshold:
        Threshold above which the market is considered in extreme greed.

    Returns
    -------
    pd.DataFrame
        Data frame with an added 'sentiment_regime' column.
    """
    result = data.copy()
    result["sentiment_regime"] = result["fg_value"].apply(
        lambda x: classify_sentiment_value(
            x,
            extreme_fear_threshold=extreme_fear_threshold,
            extreme_greed_threshold=extreme_greed_threshold,
        )
    )
    return result