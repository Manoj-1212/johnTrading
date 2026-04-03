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
from config import MANDATORY_SIGNALS


# List of all 7 signal column names
SIGNAL_COLS = [
    'trend_signal', 'rsi_signal', 'volume_signal',
    'atr_signal', 'elliott_wave_signal', 'fibonacci_signal', 'regression_signal'
]

# Map short names to signal column names
_SIGNAL_NAME_MAP = {
    'trend': 'trend_signal',
    'rsi': 'rsi_signal',
    'volume': 'volume_signal',
    'atr': 'atr_signal',
    'elliott_wave': 'elliott_wave_signal',
    'fibonacci': 'fibonacci_signal',
    'regression': 'regression_signal',
}


def build_full_indicator_set(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all 7 indicators and return combined DataFrame.
    
    Adds columns:
    - All 7 indicator signals (boolean)
    - signal_count: Sum of active signals (0-7)
    - mandatory_ok: True when all MANDATORY_SIGNALS from config are True
    - composite_score: signal_count / 7 (0.0 to 1.0)
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
    
    # Check mandatory signals (configurable from config.py)
    if MANDATORY_SIGNALS:
        mandatory_cols = [_SIGNAL_NAME_MAP[s] for s in MANDATORY_SIGNALS if s in _SIGNAL_NAME_MAP]
        if mandatory_cols:
            df['mandatory_ok'] = df[mandatory_cols].all(axis=1)
        else:
            df['mandatory_ok'] = True
    else:
        # No mandatory signals = always OK (more permissive)
        df['mandatory_ok'] = True
    
    # Composite score (0.0 to 1.0)
    df['composite_score'] = df['signal_count'] / 7.0
    
    return df
