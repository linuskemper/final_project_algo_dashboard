import pandas as pd

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