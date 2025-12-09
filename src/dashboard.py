from flask import Flask, render_template, request, jsonify
from src import indicators, strategy, serialization
from src import data_loader

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Simple cache to avoid reloading data every time
_CACHE = {}

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

@app.route("/")
def home():
    return render_template("dashboard.html")

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
        payload = serialization. serialize_data(df)

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