"""
phase2_indicators/trend.py — EMA Trend Signal
Calculates EMA50 and EMA200, then generates trend signal
"""

import pandas as pd
from config import EMA_FAST, EMA_SLOW


def add_trend_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add EMA trend columns to DataFrame.
    
    Columns added:
    - EMA50: Fast exponential moving average
    - EMA200: Slow exponential moving average
    - trend_signal: True when Close > EMA50 > EMA200 (uptrend)
    """
    df = df.copy()
    
    # Calculate EMAs using pandas exponential moving average
    df[f'EMA{EMA_FAST}'] = df['Close'].ewm(span=EMA_FAST, adjust=False).mean()
    df[f'EMA{EMA_SLOW}'] = df['Close'].ewm(span=EMA_SLOW, adjust=False).mean()
    
    # Trend signal: Price above fast EMA, fast EMA above slow EMA
    df['trend_signal'] = (
        (df['Close'] > df[f'EMA{EMA_FAST}']) &
        (df[f'EMA{EMA_FAST}'] > df[f'EMA{EMA_SLOW}'])
    )
    
    return df
