"""
phase2_indicators/volatility.py — ATR Volatility Signal
Calculates ATR(14) using Wilder's method
"""

import pandas as pd
import numpy as np
from config import ATR_PERIOD, ATR_LOOKBACK


def add_atr_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add ATR volatility columns to DataFrame.
    
    Uses Wilder's smoothing method for True Range.
    
    Columns added:
    - ATR: Average True Range (volatility)
    - ATR_avg: Rolling average of ATR over lookback period
    - atr_signal: True when current ATR > rolling average (elevated volatility)
    """
    df = df.copy()
    
    # Calculate True Range components
    high, low, close = df['High'], df['Low'], df['Close']
    prev_close = close.shift(1)
    
    # True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR = Wilder's smoothed TR
    df['ATR'] = tr.ewm(alpha=1/ATR_PERIOD, adjust=False).mean()
    
    # Rolling average of ATR
    df['ATR_avg'] = df['ATR'].rolling(ATR_LOOKBACK).mean()
    
    # Signal: Current ATR above average (elevated volatility = potential strong move)
    df['atr_signal'] = df['ATR'] > df['ATR_avg']
    
    return df
