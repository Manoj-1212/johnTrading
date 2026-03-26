"""
IMPROVED FIBONACCI RETRACEMENT DETECTOR
=======================================
Stricter rule-based Fibonacci detection using clearer swing definitions.

Key improvements:
1. Uses SwingDetector from elliott_wave_improved for consistency
2. Validates retracement levels more strictly
3. Checks for structure integrity (price must not break original swing low)
4. Aligns with Elliott Wave logic (should activate during W2)
5. Conservative signal generation
"""

import pandas as pd
import numpy as np
from phase2_indicators.elliott_wave_improved import SwingDetector


class FibonacciDetector:
    """
    Detects Fibonacci retracement levels using identified swings.
    
    Traditional Fibonacci levels for retracements:
    - 23.6% (weak support)
    - 38.2% (golden zone - strong support)
    - 50.0% (technical support)
    - 61.8% (golden zone - strong support)
    - 78.6% (weak support)
    - 100% (breaks to new low)
    """
    
    def __init__(self, lookback_bars: int = 100):
        self.lookback = lookback_bars
        self.fib_levels = {
            0.236: 'weak_support',
            0.382: 'golden_zone',
            0.500: 'midpoint',
            0.618: 'golden_zone',
            0.786: 'weak_support'
        }
    
    def find_recent_swing(self, close: pd.Series, position: int) -> dict:
        """Find the most recent completed swing high-low sequence."""
        lookback = min(position, self.lookback)
        segment = close.iloc[max(0, position - lookback):position + 1]
        
        detector = SwingDetector(lookback_left=5, lookback_right=5, min_swing_size=0.005)
        swing_highs, swing_lows = detector.find_pivots(segment)
        
        if len(swing_highs) < 1:
            return {'valid': False}
        
        # Find most recent swing high
        recent_high_idx = swing_highs[-1]
        swing_high_val = segment.iloc[recent_high_idx]
        
        # Find the low before this high (previous support)
        swing_lows_before = [l for l in swing_lows if l < recent_high_idx]
        if not swing_lows_before:
            return {'valid': False}
        
        swing_low_idx = swing_lows_before[-1]
        swing_low_val = segment.iloc[swing_low_idx]
        
        if swing_high_val <= swing_low_val:
            return {'valid': False}
        
        swing_range = swing_high_val - swing_low_val
        
        return {
            'valid': True,
            'swing_high_idx': recent_high_idx,
            'swing_high_val': swing_high_val,
            'swing_low_idx': swing_low_idx,
            'swing_low_val': swing_low_val,
            'swing_range': swing_range
        }
    
    def calculate_fib_levels(self, swing_info: dict) -> dict:
        """Calculate Fibonacci levels for a swing."""
        if not swing_info.get('valid'):
            return {}
        
        high = swing_info['swing_high_val']
        low = swing_info['swing_low_val']
        swing_range = swing_info['swing_range']
        
        levels = {}
        for ratio, zone in self.fib_levels.items():
            level_price = high - (swing_range * ratio)
            levels[ratio] = {
                'price': level_price,
                'zone': zone
            }
        
        return levels
    
    def is_in_golden_zone(self, current_price: float, fib_levels: dict) -> Tuple[bool, float, float]:
        """
        Check if price is in 38.2%-61.8% retracement zone (golden zone).
        
        Returns: (is_in_zone, level_382, level_618)
        """
        level_382 = fib_levels[0.382]['price']
        level_618 = fib_levels[0.618]['price']
        
        # Golden zone between 38.2% and 61.8%
        in_zone = level_618 <= current_price <= level_382
        
        return in_zone, level_382, level_618


def add_fibonacci_signal_improved(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Fibonacci retracement signal using strict swing detection.
    
    Signal = True when:
    1. Price is in 38.2%-61.8% retracement zone ("golden zone")
    2. Structure is intact (price has not broken swing low)
    3. Swing is recent (< 100 bars back) and significant
    4. Should ideally align with Elliott Wave W2 detection
    """
    df = df.copy()
    df['fibonacci_signal'] = False
    df['fib_level_382'] = np.nan
    df['fib_level_618'] = np.nan
    df['fib_zone_name'] = 'NONE'
    df['fib_retrace_pct'] = np.nan
    
    close = df['Close']
    detector = FibonacciDetector(lookback_bars=100)
    
    for i in range(50, len(df)):  # Start after warmup
        swing_info = detector.find_recent_swing(close, i)
        
        if not swing_info.get('valid'):
            continue
        
        fib_levels = detector.calculate_fib_levels(swing_info)
        if not fib_levels:
            continue
        
        current_price = close.iloc[i]
        swing_low = swing_info['swing_low_val']
        
        # Check: is price in golden zone?
        in_zone, level_382, level_618 = detector.is_in_golden_zone(current_price, fib_levels)
        
        # Check: has structure been broken?
        structure_intact = current_price > swing_low
        
        # Calculate retrace percentage
        retrace_pct = (swing_info['swing_high_val'] - current_price) / swing_info['swing_range']
        
        if in_zone and structure_intact:
            df.at[df.index[i], 'fibonacci_signal'] = True
            df.at[df.index[i], 'fib_level_382'] = level_382
            df.at[df.index[i], 'fib_level_618'] = level_618
            df.at[df.index[i], 'fib_zone_name'] = 'GOLDEN_ZONE'
            df.at[df.index[i], 'fib_retrace_pct'] = retrace_pct * 100
        elif level_618 < current_price < level_382:
            # In golden zone but log it anyway
            df.at[df.index[i], 'fib_zone_name'] = 'GOLDEN_ZONE'
            df.at[df.index[i], 'fib_retrace_pct'] = retrace_pct * 100
    
    return df
