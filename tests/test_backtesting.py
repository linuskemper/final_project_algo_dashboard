"""Tests for backtesting helper functions."""

import pandas as pd

from src import backtesting


def test_run_backtest_basic_metrics():
    index = pd.date_range("2020-01-01", periods=10, freq="D")
    returns = pd.Series(0.01, index=index)
    positions = pd.Series(1, index=index)

    df = pd.DataFrame({"return": returns, "position": positions}, index=index)
    result, metrics = backtesting.run_backtest(df)

    assert "strategy_equity" in result.columns
    assert "benchmark_equity" in result.columns
    assert metrics["strategy_cumulative_return"] > 0
    assert metrics["benchmark_cumulative_return"] > 0


def test_hit_rate_between_zero_and_one():
    index = pd.date_range("2020-01-01", periods=5, freq="D")
    returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.0], index=index)
    positions = pd.Series([1, 1, 1, 1, 1], index=index)
    df = pd.DataFrame({"return": returns, "position": positions}, index=index)

    _result, metrics = backtesting.run_backtest(df)
    assert 0.0 <= metrics["strategy_hit_rate"] <= 1.0
