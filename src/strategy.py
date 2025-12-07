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