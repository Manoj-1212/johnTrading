"""
phase2_indicators/volume.py — Volume Analysis Signal
Detects above-average volume using 20-bar moving average
"""

import pandas as pd
from config import VOLUME_LOOKBACK, VOLUME_THRESHOLD


def add_volume_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add volume analysis columns to DataFrame.
    
    Columns added:
    - volume_avg_20: 20-bar simple moving average of volume
    - volume_ratio: Current volume / average volume
    - volume_signal: True when volume >= 80% of average (at least 0.8x)
    """
    df = df.copy()
    
    # Calculate rolling volume average
    df['volume_avg_20'] = df['Volume'].rolling(VOLUME_LOOKBACK).mean()
    
    # Calculate volume ratio
    df['volume_ratio'] = df['Volume'] / df['volume_avg_20']
    
    # Signal: Volume above threshold ratio
    df['volume_signal'] = df['volume_ratio'] >= VOLUME_THRESHOLD
    
    return df
