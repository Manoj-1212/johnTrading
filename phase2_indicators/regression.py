"""
phase2_indicators/regression.py — Linear Regression Trend Signal
Calculates rolling linear regression line and detects uptrend
"""

import pandas as pd
import numpy as np
from config import REGRESSION_LOOKBACK


def add_regression_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add linear regression columns to DataFrame.
    
    Calculates a rolling linear regression of Close over REGRESSION_LOOKBACK bars.
    For each bar, fits a line and checks if price is above the trend.
    
    Columns added:
    - regression_line: Fitted regression line value at current bar
    - regression_signal: True when Close > regression_line (above trend)
    """
    df = df.copy()
    
    reg_line = [np.nan] * len(df)
    close = df['Close'].values
    
    # Calculate rolling linear regression
    for i in range(REGRESSION_LOOKBACK, len(close)):
        # Get last N closes
        y = close[i - REGRESSION_LOOKBACK:i]
        # X values: bar positions 0 to N-1
        x = np.arange(REGRESSION_LOOKBACK)
        # Fit line: y = slope * x + intercept
        slope, intercept = np.polyfit(x, y, 1)
        # Calculate regression value at current position (last bar)
        reg_line[i] = slope * (REGRESSION_LOOKBACK - 1) + intercept
    
    df['regression_line'] = reg_line
    df['regression_signal'] = df['Close'] > df['regression_line']
    
    return df
