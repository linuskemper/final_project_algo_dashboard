"""Tests for sentiment helper functions."""

import pandas as pd

from src import sentiment


def test_classify_sentiment_value_extremes():
    assert sentiment.classify_sentiment_value(5) == "Extreme Fear"
    assert sentiment.classify_sentiment_value(90) == "Extreme Greed"


def test_add_sentiment_regime_creates_column():
    df = pd.DataFrame(
        {"fg_value": [10, 30, 50, 65, 85]},
        index=pd.date_range("2020-01-01", periods=5, freq="D"),
    )
    result = sentiment.add_sentiment_regime(df)
    assert "sentiment_regime" in result.columns
    assert len(result["sentiment_regime"].unique()) >= 2


def test_summarize_sentiment_returns_tuple():
    df = pd.DataFrame({"fg_value": [10, 20, 30, 40]})
    mean_value, std_value = sentiment.summarize_sentiment(df)
    assert isinstance(mean_value, float)
    assert isinstance(std_value, float)
