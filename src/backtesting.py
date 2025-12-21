"""Backtesting utilities for the Bitcoin trading strategy."""

from __future__ import annotations

from math import sqrt
from typing import Dict, Tuple

import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def run_backtest(data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Run a simple long/flat backtest based on the 'position' column.

    Parameters
    ----------
    data:
        Data frame with columns 'return' (daily returns of Bitcoin)
        and 'position' (1 for long, 0 for flat).

    Returns
    -------
    tuple[pd.DataFrame, dict[str, float]]
        Data frame enriched with strategy performance columns and a
        dictionary with summary metrics.
    """
    result = data.copy()

    result["position_lagged"] = result["position"].shift(1).fillna(0)
    result["strategy_return"] = result["position_lagged"] * result["return"]

    result["strategy_equity"] = (1.0 + result["strategy_return"]).cumprod()
    result["benchmark_equity"] = (1.0 + result["return"]).cumprod()

    drawdown = result["strategy_equity"] / result["strategy_equity"].cummax() - 1.0
    max_drawdown = float(drawdown.min())

    strat_ret = result["strategy_return"]
    mean_daily = float(strat_ret.mean())
    std_daily = float(strat_ret.std())

    if std_daily > 0.0:
        sharpe_ratio = mean_daily / std_daily * sqrt(TRADING_DAYS_PER_YEAR)
    else:
        sharpe_ratio = 0.0

    buy_and_hold_ret = float(result["benchmark_equity"].iloc[-1] - 1.0)
    strategy_ret = float(result["strategy_equity"].iloc[-1] - 1.0)

    active_days = result["position_lagged"] != 0
    if active_days.any():
        hit_rate = float(
            (result.loc[active_days, "strategy_return"] > 0).mean()
        )
    else:
        hit_rate = 0.0

    metrics = {
        "strategy_cumulative_return": strategy_ret,
        "benchmark_cumulative_return": buy_and_hold_ret,
        "strategy_max_drawdown": max_drawdown,
        "strategy_sharpe_ratio": sharpe_ratio,
        "strategy_hit_rate": hit_rate,
    }

    return result, metrics
