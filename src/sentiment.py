from __future__ import annotations

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