
# Algo Dash

An interactive dashboard for algorithmic trading strategies.

## Features

- **Interactive Dashboard**: Real-time visualization of trading signals and performance metrics
- **Technical Indicators**: Moving averages, Bollinger Bands, and Kalman trend filters
- **Sentiment Analysis**: Fear & Greed index integration for regime detection
- **Backtesting Engine**: Historical performance evaluation with benchmark comparison
- **Strategy Optimization**: Configurable parameters for moving average windows and sentiment thresholds

## Usage

```python
flask --app src.dashboard run --host 0.0.0.0 --port 5001
```

## Architecture

The application follows a modular pipeline:
1. Data loading from CSV and price feeds
2. Technical indicator calculation
3. Sentiment regime classification
4. Trading signal generation
5. Backtest execution with caching
