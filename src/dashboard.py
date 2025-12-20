import pandas as pd
from flask import Flask, render_template, request, jsonify
from src import indicators, strategy, serialization
from src import data_loader
from pathlib import Path
from typing import Dict, Any, Tuple
from . import (
data_loader,
indicators,
sentiment,
backtesting
)

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Simple cache to avoid reloading data every time
_CACHE: Dict[str, Any] = {}

def get_data_pipeline():
    """ Execution data loading pipeline """
    if "full_data" in _CACHE:
        return _CACHE["full_data"]
    try:
        # TODO: prices and sentiment functions compare
        prices = data_loader.download_bitcoin_history()
        sentiment = data_loader.load_fear_greed_index()
        merged = data_loader.merge_price_and_sentiment(prices, sentiment)
        _CACHE["full_data"] = merged
        return merged
    except Exception as e:
        print(f"Error loading data: {e}")
        raise e

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder = str(Path(__file__).resolve().parent[1] / "templates"),
        static_folder = str(Path(__file__).resolve().parent[1] / "static")
    )
    @app.route("/", methods = ["GET"])
    def index() -> str:
        return render_template("dashboard.html")


def _parse_parameter_from_request() -> Dict[str, int]:
    def _get_int(name: str, default: int) -> int:
        raw = request.args.get(name, "")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default
        return value

    parms = {
        "short_window": _get_int("short_window", 5),
        "long_window": _get_int("long_window", 50),
        "extreme_fear_threshold": _get_int("extreme_fear", 25),
        "extreme_greed_threshold": _get_int("extreme_greed", 75)
    }
    return parms

def _get_cached_data(
        params: Dict[str, int],
) -> Tuple[pd.DataFrame, Dict[str, float]]:

    key = str(sorted(params.items()))

    if key in _CACHE:
        print("Returning cached data for key:", key)
        return _CACHE[key]

    print("Loading new data for key:", key)

    project_root = Path(__file__).resolve().parents[1]
    fg_csv = data_loader.get_default_data_paths(project_root)

    try:
        _price_df, _fg_df, merged = data_loader.load_all_data(fg_csv)
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

    enriched = indicators.add_moving_averages(
        merged,
        short_window = params["short_window"],
        long_window=params["long_window"]
    )
    enriched = indicators.add_bollinger_bands(enriched)
    enriched = indicators.add_kalman_trend(enriched)
    enriched = sentiment.add_sentiment_regime(
        enriched,
        extreme_fear_threshold = params["extreme_fear_threshold"],
        extreme_greed_threshold = params["extreme_greed_threshold"]
    )
    enriched = strategy.generate_positions(enriched)
    enriched = strategy.generate_trade_signals(enriched)

    backtest_df, metrics = backtesting.run_backtest(enriched)
    enriched["_strategy_equity"] = backtest_df["strategy_equity"]
    enriched["_benchmark_equity"] = backtest_df["benchmark_equity"]

    _CACHE[key] = (backtest_df, metrics)
    return backtest_df, metrics

@app.route("/api/data")
def get_dashboard_data():
    try:
        # 1. Load the data
        df = get_data_pipeline().copy()

        # 2. Parse parameters
        short_window = int(request.args.get("short_window", 20))
        long_window = int(request.args.get("long_window", 50))

        # 3. Apply indicators
        df["sma_short"] = indicators.calculate_sma(df["close"], short_window)
        df["sma_long"] = indicators.calculate_sma(df["close"], long_window)

        bb_df = indicators.calculate_bollinger_bands(df["close"])
        df = df.join(bb_df)

        df["kalman_trend"] = indicators.calculate_kalman_trend(df["close"])

        # 4. Apply strategy
        df = strategy.generate_signals(df)

        # 5. Serialize
        payload = serialization. serialize_time_series(df)

        # Add metadata/latest signal
        sig, expl = strategy.get_latest_recommendation(df)
        payload["latest_signal"] = sig
        payload["latest_explanation"] = expl

        return jsonify(payload)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port = 5000)