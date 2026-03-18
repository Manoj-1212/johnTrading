"""
phase2_indicators/elliott_wave.py — Elliott Wave Pattern Detection
Simplified Wave-3 detection using pivot-based rules
"""

import pandas as pd
import numpy as np


def add_elliott_wave_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Elliott Wave detection columns to DataFrame.
    
    Uses simplified rule-based approach over 60-bar rolling window:
    - Wave 1: Swing up from local min to local max
    - Wave 2: Pullback retracing 38.2%-61.8% of Wave 1
    - Wave 3: Recovery back toward Wave 1 high (entry signal)
    
    Columns added:
    - elliott_wave_signal: True when likely in Wave-2 pullback (Wave-3 entry)
    - wave_label: Debug label ('W1','W2','W3', or 'NA')
    """
    df = df.copy()
    df['elliott_wave_signal'] = False
    df['wave_label'] = 'NA'
    
    close = df['Close'].values
    n = len(close)
    window = 10  # pivot detection window
    
    # Scan through each bar looking for wave patterns
    for i in range(60, n):
        # Look at 60-bar segment ending at current bar
        segment = df.iloc[max(0, i-60):i]
        seg_close = segment['Close']
        
        if len(seg_close) < 30:
            continue
        
        # Find local highs and lows using rolling max/min
        local_max_idx = []
        local_min_idx = []
        
        for j in range(window, len(seg_close) - window):
            # Local maximum
            if seg_close.iloc[j] == seg_close.iloc[j-window:j+window].max():
                local_max_idx.append(j)
            # Local minimum
            if seg_close.iloc[j] == seg_close.iloc[j-window:j+window].min():
                local_min_idx.append(j)
        
        if len(local_max_idx) < 1 or len(local_min_idx) < 2:
            continue
        
        # === Wave 1: Swing Low → Swing High ===
        w1_low_i = local_min_idx[0]
        w1_high_i = next((x for x in local_max_idx if x > w1_low_i), None)
        
        if w1_high_i is None:
            continue
        
        w1_low = seg_close.iloc[w1_low_i]
        w1_high = seg_close.iloc[w1_high_i]
        w1_size = w1_high - w1_low
        
        if w1_size <= 0:
            continue
        
        # === Wave 2: Pullback after Wave 1 High ===
        w2_low_i = next((x for x in local_min_idx if x > w1_high_i), None)
        
        if w2_low_i is None:
            continue
        
        w2_low = seg_close.iloc[w2_low_i]
        
        # Wave 2 retrace ratio
        retrace = (w1_high - w2_low) / w1_size
        
        # Wave 2 must retrace 38.2% - 61.8% of Wave 1
        if not (0.382 <= retrace <= 0.618):
            continue
        
        # Wave 2 low must be above Wave 1 low (structure intact)
        if w2_low < w1_low:
            continue
        
        # === Wave 3: Recovery from Wave 2 ===
        # Current price should be recovering (above Wave 2 low)
        # but not yet broken through Wave 1 high (entry setup)
        current_price = seg_close.iloc[-1]
        
        if current_price > w2_low and current_price < w1_high * 1.02:
            df.at[df.index[i], 'elliott_wave_signal'] = True
            df.at[df.index[i], 'wave_label'] = 'W2→W3'
    
    return df
