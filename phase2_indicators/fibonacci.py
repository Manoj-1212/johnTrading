"""
phase2_indicators/fibonacci.py — Fibonacci Retracement Signal
Detects price in Fibonacci pullback zones (golden zone)
"""

import pandas as pd
from config import REGRESSION_LOOKBACK, FIB_LEVELS


def add_fibonacci_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Fibonacci retracement columns to DataFrame.
    
    Identifies swing highs/lows over REGRESSION_LOOKBACK period and calculates
    Fibonacci retracement levels. Signal is True when price is in the
    "golden zone" (between 38.2% and 61.8% retrace).
    
    Columns added:
    - fib_high: Swing high over lookback
    - fib_low: Swing low over lookback
    - fib_382, fib_618: Fibonacci level prices
    - fibonacci_signal: True when price in golden zone
    """
    df = df.copy()
    
    # Identify swing highs and lows
    df['fib_high'] = df['Close'].rolling(REGRESSION_LOOKBACK).max()
    df['fib_low'] = df['Close'].rolling(REGRESSION_LOOKBACK).min()
    
    # Calculate Fibonacci range
    fib_range = df['fib_high'] - df['fib_low']
    
    # Fibonacci levels (measured from high downward)
    df['fib_382'] = df['fib_high'] - (fib_range * 0.382)  # 38.2% level
    df['fib_618'] = df['fib_high'] - (fib_range * 0.618)  # 61.8% level
    
    # Golden zone: price between 38.2% and 61.8% retracement
    # AND price hasn't broken below swing low (structure intact)
    df['fibonacci_signal'] = (
        (df['Close'] <= df['fib_382']) &
        (df['Close'] >= df['fib_618']) &
        (df['Close'] > df['fib_low'])
    )
    
    return df
