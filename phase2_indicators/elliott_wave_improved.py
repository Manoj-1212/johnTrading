"""
IMPROVED ELLIOTT WAVE DETECTOR
==============================
Stricter, rule-based Elliott Wave detection using clearer swing definitions.

Key improvements:
1. Clearer swing high/low definitions (local extrema with confirmation)
2. Proper Wave 1, 2, 3 sequence validation
3. Fibonacci retracement validation (Wave-2 must retrace 38.2%-61.8%)
4. Wave structure integrity checks
5. Conservative signal generation
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


class SwingDetector:
    """Finds significant swing highs and lows with confirmation."""
    
    def __init__(self, lookback_left: int = 5, lookback_right: int = 5,
                 min_swing_size: float = 0.01):
        """
        lookback_left: bars to left of potential pivot
        lookback_right: bars to right of potential pivot (for confirmation)
        min_swing_size: minimum % move to qualify as swing (e.g., 1%)
        """
        self.left = lookback_left
        self.right = lookback_right
        self.min_size = min_swing_size
    
    def find_pivots(self, close: pd.Series) -> Tuple[List[int], List[int]]:
        """
        Find swing highs and lows.
        Uses (left + right + 1) bar window: left bars + current + right bars.
        Wait for right-side confirmation before confirming a pivot.
        """
        highs = []  # indices of swing highs
        lows = []   # indices of swing lows
        
        for i in range(self.left, len(close) - self.right):
            window_low = i - self.left
            window_high = i + self.right + 1
            window = close.iloc[window_low:window_high]
            
            # Check if this bar is an extremum
            center_val = close.iloc[i]
            max_in_window = window.max()
            min_in_window = window.min()
            
            # Swing high: center is max in window, and is high enough
            if center_val >= max_in_window * (1 - 1e-6):  # Allow for floating point error
                pct_above_left = (center_val - close.iloc[window_low]) / close.iloc[window_low]
                if pct_above_left >= self.min_size:
                    highs.append(i)
            
            # Swing low: center is min in window, and is low enough
            if center_val <= min_in_window * (1 + 1e-6):
                pct_below_left = (close.iloc[window_low] - center_val) / close.iloc[window_low]
                if pct_below_left >= self.min_size:
                    lows.append(i)
        
        return highs, lows
    
    def find_sequence(self, close: pd.Series, 
                     position: int) -> Dict:
        """
        Find Wave 1 → Wave 2 → Wave 3 structure leading up to position.
        Returns: {
            'w1_start': idx, 'w1_end': idx, 'w1_size': float,
            'w2_end': idx, 'w2_retrace': float,
            'w3_start': idx, 'valid': bool
        }
        """
        lookback = min(position, 200)  # Look back up to 200 bars
        segment = close.iloc[max(0, position - lookback):position + 1]
        
        detector = SwingDetector(lookback_left=5, lookback_right=5, min_swing_size=0.005)
        swing_highs, swing_lows = detector.find_pivots(segment)
        
        if len(swing_lows) < 2 or len(swing_highs) < 1:
            return {'valid': False}
        
        # Find the most recent complete W1-W2 structure
        # W1 = swing low → swing high
        # W2 = pullback from W1 high
        
        # Start from the rightmost low (most recent)
        for i in range(len(swing_lows) - 1, -1, -1):
            w1_start_idx = swing_lows[i]
            
            # Find next high after this low (Wave 1 high)
            w1_h_candidates = [h for h in swing_highs if h > w1_start_idx]
            if not w1_h_candidates:
                continue
            
            w1_end_idx = w1_h_candidates[0]
            w1_size = segment.iloc[w1_end_idx] - segment.iloc[w1_start_idx]
            
            if w1_size <= 0:
                continue
            
            # Find next low after W1 high (Wave 2 low)
            w2_l_candidates = [l for l in swing_lows if l > w1_end_idx]
            if not w2_l_candidates:
                continue
            
            w2_end_idx = w2_l_candidates[0]
            w2_val = segment.iloc[w2_end_idx]
            w1_high = segment.iloc[w1_end_idx]
            
            # Check Wave 2 validity:
            # 1. Must retrace 38.2%-61.8% of Wave 1
            # 2. Must stay above Wave 1 low
            w1_low = segment.iloc[w1_start_idx]
            retrace_pct = (w1_high - w2_val) / w1_size
            
            if not (0.382 <= retrace_pct <= 0.618):
                continue
            
            if w2_val < w1_low:
                continue
            
            # If we've found a valid W1-W2, check if W3 is starting
            # W3 entry: price above W1 high
            current_price = segment.iloc[-1]
            
            if current_price > w1_high:
                # Potential Wave 3 in progress
                return {
                    'valid': True,
                    'w1_start_idx': w1_start_idx,
                    'w1_end_idx': w1_end_idx,
                    'w1_size': w1_size,
                    'w1_low': w1_low,
                    'w1_high': w1_high,
                    'w2_end_idx': w2_end_idx,
                    'w2_val': w2_val,
                    'w2_retrace': retrace_pct,
                    'w3_start_idx': w2_end_idx,
                    'current_price': current_price
                }
        
        return {'valid': False}


def add_elliott_wave_signal_improved(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Elliott Wave signal using strict rule-based detection.
    
    Signal = True when:
    1. Valid Wave 1-2-3 structure confirmed
    2. Wave 2 retraces 38.2%-61.8% of Wave 1
    3. Price currently above Wave 1 high (Wave 3 starting)
    4. Both Elliott Wave AND Fibonacci signals should align (see fibonacci.py)
    """
    df = df.copy()
    df['elliott_wave_signal'] = False
    df['wave_structure'] = 'NONE'
    df['w1_size'] = np.nan
    df['w2_retrace_pct'] = np.nan
    
    close = df['Close']
    
    for i in range(100, len(df)):  # Start after warmup period
        result = SwingDetector().find_sequence(close, i)
        
        if result.get('valid'):
            df.at[df.index[i], 'elliott_wave_signal'] = True
            df.at[df.index[i], 'wave_structure'] = 'W1→W2→W3'
            df.at[df.index[i], 'w1_size'] = result['w1_size']
            df.at[df.index[i], 'w2_retrace_pct'] = result['w2_retrace'] * 100
    
    return df
