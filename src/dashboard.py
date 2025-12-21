"""Flask application exposing an interactive backtest dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
from flask import Flask, jsonify, render_template, request

from . import (
    backtesting,
    data_loader,
    indicators,
    sentiment,
    serialization,
    strategy,
)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parents[1] / "templates"),
        static_folder=str(Path(__file__).resolve().parents[1] / "static"),
    )

    @app.route("/", methods=["GET"])
    def index() -> str:
        return render_template("dashboard.html")

    @app.route("/api/time_series", methods=["GET"])
    def api_time_series() -> Any:
        try:
            enriched, _metrics = _run_pipeline_from_request()
            payload = serialization.serialize_time_series(enriched)
            return jsonify(payload)
        except Exception as e:
            print(f"API Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sentiment", methods=["GET"])
    def api_sentiment() -> Any:
        try:
            enriched, _metrics = _run_pipeline_from_request()
            payload = serialization.serialize_sentiment(enriched)
            return jsonify(payload)
        except Exception as e:
            print(f"API Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/performance", methods=["GET"])
    def api_performance() -> Any:
        try:
            enriched, metrics = _run_pipeline_from_request()
            backtest_df, metrics = backtesting.run_backtest(enriched)
            payload = serialization.serialize_performance(backtest_df, metrics)
            signal, explanation = strategy.latest_recommendation(enriched)
            payload["latest_signal"] = signal
            payload["latest_explanation"] = explanation
            return jsonify(payload)
        except Exception as e:
            print(f"API Error: {e}")
            return jsonify({"error": str(e)}), 500

    return app


def _parse_parameters_from_request() -> Dict[str, int]:
    """
    Read strategy parameters from the query string with safe defaults.

    Returns
    -------
    dict[str, int]
        Dictionary of user-selected parameter values.
    """
    def _get_int(name: str, default: int) -> int:
        raw = request.args.get(name, "")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default
        return value

    params = {
        "short_window": _get_int("short_window", 5),
        "long_window": _get_int("long_window", 50),
        "extreme_fear_threshold": _get_int("extreme_fear", 25),
        "extreme_greed_threshold": _get_int("extreme_greed", 75),
    }
    return params


# Simple global cache to avoid refetching on every request
_CACHE: Dict[str, Any] = {}


def _get_cached_data(
    params: Dict[str, int],
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Fetch data from cache or load it if missing/stale."""
    # Create a cache key based on parameters
    key = str(sorted(params.items()))

    if key in _CACHE:
        print("Returning cached data for key:", key)
        return _CACHE[key]

    print("Loading new data for key:", key)

    project_root = Path(__file__).resolve().parents[1]
    fg_csv = data_loader.get_default_data_paths(project_root)

    # Load data (this might take time due to yfinance)
    try:
        _price_df, _fg_df, merged = data_loader.load_all_data(fg_csv)
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

    enriched = indicators.add_moving_averages(
        merged,
        short_window=params["short_window"],
        long_window=params["long_window"],
    )
    enriched = indicators.add_bollinger_bands(enriched)
    enriched = indicators.add_kalman_trend(enriched)
    enriched = sentiment.add_sentiment_regime(
        enriched,
        extreme_fear_threshold=params["extreme_fear_threshold"],
        extreme_greed_threshold=params["extreme_greed_threshold"],
    )
    enriched = strategy.generate_positions(enriched)
    enriched = strategy.generate_trade_signals(enriched)

    backtest_df, metrics = backtesting.run_backtest(enriched)
    enriched["_strategy_equity"] = backtest_df["strategy_equity"]
    enriched["_benchmark_equity"] = backtest_df["benchmark_equity"]

    # Update cache
    _CACHE[key] = (enriched, metrics)
    return enriched, metrics


def _run_pipeline_from_request():
    """
    Run the data and strategy pipeline based on user parameters.

    Returns
    -------
    tuple[pd.DataFrame, dict[str, float]]
        Enriched data frame and backtest metrics dictionary.
    """
    params = _parse_parameters_from_request()
    return _get_cached_data(params)


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
