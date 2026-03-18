"""
phase2_indicators/momentum.py — RSI Momentum Signal
Calculates RSI(14) using Wilder's smoothing method
"""

import pandas as pd
import numpy as np
from config import RSI_PERIOD, RSI_LOW, RSI_HIGH


def add_rsi_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add RSI columns to DataFrame.
    
    Uses Wilder's smoothing method (not simple EMA).
    
    Columns added:
    - RSI: Raw RSI value (0-100)
    - rsi_signal: True when RSI is between RSI_LOW and RSI_HIGH (optimal zone)
    """
    df = df.copy()
    
    # Calculate price changes
    delta = df['Close'].diff()
    
    # Separate gains and losses
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Wilder's smoothed averages (alpha = 1/period)
    avg_gain = gain.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    
    # Relative Strength and RSI
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Signal: RSI in optimal momentum zone (not overbought/oversold)
    df['rsi_signal'] = df['RSI'].between(RSI_LOW, RSI_HIGH)
    
    return df
