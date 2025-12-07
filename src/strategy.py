import pandas as pd
import numpy as np

def generate_signals(df):
    """
    Generates trading signals based on SMA crossovers and Fear & Greed index.
    """
    df = df.copy()
    
    # Ensure required columns exist
    if 'sma_short' not in df.columns or 'sma_long' not in df.columns:
        print("Warning: Missing SMA columns")
        return df
    
    # Default to 0 (Hold)
    df['position'] = 0
    
    # Buy condition: Short SMA > Long SMA
    buy_condition = (df['sma_short'] > df['sma_long']) 
    
    # Apply conditions
    df.loc[buy_condition, 'position'] = 1
    df.loc[~buy_condition, 'position'] = 0 # Sell/Neutral otherwise
    
    # Calculate trade signals (changes in position)
    df['signal_diff'] = df['position'].diff()
    
    sig_map = {1.0: 'Buy', -1.0: 'Sell', 0.0: 'Hold'}
    df['trade_signal'] = df['signal_diff'].map(sig_map).fillna('Hold')
    
    return df

def get_latest_recommendation(df):
    """Returns the latest signal and a brief explanation."""
    if df.empty:
        return "Unknown", "No data available."
        
    last_row = df.iloc[-1]
    signal = last_row.get('trade_signal', 'Hold')
    
    sma_s = last_row.get('sma_short', 0)
    sma_l = last_row.get('sma_long', 0)
    
    explanation = f"Short SMA ({sma_s:.2f}) vs Long SMA ({sma_l:.2f})."
    return signal, explanation