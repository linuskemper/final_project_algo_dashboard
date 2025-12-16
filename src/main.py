from __future__ import annotations

from pathlib import Path

from src import backtesting, data_loader, indicators, sentiment, strategy


def run_default_backtest() -> None:
    """Run the full pipeline and print summary metrics."""
    project_root = Path(__file__).resolve().parents[1]
    fg_csv = data_loader.get_default_data_paths(project_root)

    price_df, fg_df, merged = data_loader.load_all_data(fg_csv)

    enriched = indicators.add_moving_averages(merged)
    enriched = indicators.add_kalman_trend(enriched)
    enriched = sentiment.add_sentiment_regime(enriched)
    enriched = strategy.generate_positions(enriched)
    enriched = strategy.generate_trade_signals(enriched)

    backtest_df, metrics = backtesting.run_backtest(enriched)
    signal, explanation = strategy.get_latest_recommendation(enriched)

    print("Backtest complete for BTC-USD (2020-01-01 to 2024-12-31)")
    print("------------------------------------------------------")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
    print()
    print(f"Latest recommendation: {signal}")
    print(explanation)


if __name__ == "__main__":
    run_default_backtest()