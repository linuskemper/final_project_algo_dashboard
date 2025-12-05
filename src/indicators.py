import pandas as pd
import numpy as np

def calculate_sma(series, window):
    """Calculates Simple Moving Average."""
    return series.rolling(window=window).mean()

def calculate_bollinger_bands(series, window=20, std_dev=2):
    """Calculates Bollinger Bands."""
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return pd.DataFrame({
        'bb_middle': sma,
        'bb_upper': upper_band,
        'bb_lower': lower_band
    }, index=series.index)

def calculate_kalman_trend(series):
    """Applies a simple Kalman-like filter for trend estimation."""
    values = series.values
    n = len(values)
    trend = np.zeros(n)
    estimate = values[0]
    error_est = 1.0
    error_meas = 1.0
    q = 0.01

    # Simple 1D Kalman implementation
    for i in range(1, n):
        # Prediction
        estimate = estimate 
        error_est = error_est + q
        
        # Update
        kalman_gain = error_est / (error_est + error_meas)
        estimate = estimate + kalman_gain * (values[i] - estimate)
        error_est = (1 - kalman_gain) * error_est
        
        trend[i] = estimate
        
    return pd.Series(trend, index=series.index, name="kalman_trend")