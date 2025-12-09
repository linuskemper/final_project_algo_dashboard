from flask import Flask, render_template
from src import data_loader

app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route("/")
def home():
    return render_template("dashboard.html")

_CACHE = {}

def get_data_pipeline():
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