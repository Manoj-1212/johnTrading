"""
phase2_indicators/combiner.py — Combine All 7 Indicators
Merges all indicator signals into composite score and overall signal
"""

import pandas as pd
from phase2_indicators.trend import add_trend_signal
from phase2_indicators.momentum import add_rsi_signal
from phase2_indicators.volume import add_volume_signal
from phase2_indicators.volatility import add_atr_signal
from phase2_indicators.elliott_wave import add_elliott_wave_signal
from phase2_indicators.fibonacci import add_fibonacci_signal
from phase2_indicators.regression import add_regression_signal


# List of all 7 signal column names
SIGNAL_COLS = [
    'trend_signal', 'rsi_signal', 'volume_signal',
    'atr_signal', 'elliott_wave_signal', 'fibonacci_signal', 'regression_signal'
]


def build_full_indicator_set(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all 7 indicators and return combined DataFrame.
    
    Adds columns:
    - All 7 indicator signals (boolean)
    - signal_count: Sum of active signals (0-7)
    - mandatory_ok: True when both Elliott Wave AND Fibonacci are True
    - composite_score: signal_count / 7 (0.0 to 1.0)
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame with Date index
    
    Returns
    -------
    pd.DataFrame
        DataFrame with all indicator columns added
    """
    df = df.copy()
    
    # Apply all 7 indicators
    df = add_trend_signal(df)
    df = add_rsi_signal(df)
    df = add_volume_signal(df)
    df = add_atr_signal(df)
    df = add_elliott_wave_signal(df)
    df = add_fibonacci_signal(df)
    df = add_regression_signal(df)
    
    # Count active signals
    df['signal_count'] = df[SIGNAL_COLS].sum(axis=1).astype(int)
    
    # Check mandatory signals (both Elliott + Fibonacci must be True)
    df['mandatory_ok'] = df['elliott_wave_signal'] & df['fibonacci_signal']
    
    # Composite score (0.0 to 1.0)
    df['composite_score'] = df['signal_count'] / 7.0
    
    return df
