"""
Real-Time Indicator Calculator
Recalculates all 7 indicators on every new 1-minute bar
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime

class RealtimeIndicatorCalculator:
    """
    Calculates technical indicators on rolling 1-minute bar windows.
    
    Indicators:
    - EMA (50, 200) - Trend
    - RSI (14) - Momentum
    - MACD - Momentum
    - Bollinger Bands (20) - Volatility
    - ATR (14) - Volatility
    - Volume MA (20) - Volume confirmation
    - Elliott Wave + Fibonacci - Advanced patterns
    
    Usage:
        calc = RealtimeIndicatorCalculator()
        indicators = calc.calculate_all(bars)
    """
    
    def __init__(self, debug=False):
        self.debug = debug
        self.min_bars_required = 50  # Reduced from 200 for faster signal generation
    
    def calculate_all(self, bars_df):
        """
        Calculate all indicators on current bar data.
        
        Args:
            bars_df: DataFrame with columns [Open, High, Low, Close, Volume]
        
        Returns:
            dict with all indicator values
        """
        if bars_df.empty or len(bars_df) < self.min_bars_required:
            return self._empty_indicators()
        
        try:
            # Trend Indicators
            ema50 = self._ema(bars_df['Close'], 50)
            ema200 = self._ema(bars_df['Close'], 200)
            
            # Momentum Indicators
            rsi14 = self._rsi(bars_df['Close'], 14)
            macd_line, signal_line, macd_hist = self._macd(bars_df['Close'])
            
            # Volatility Indicators
            bb_upper, bb_middle, bb_lower = self._bollinger_bands(bars_df['Close'], 20)
            atr14 = self._atr(bars_df, 14)
            
            # Volume Indicator
            volume_ma20 = self._sma(bars_df['Volume'], 20)
            current_volume = bars_df['Volume'].iloc[-1]
            # Ensure scalar comparison
            volume_ma20_scalar = float(volume_ma20) if not isinstance(volume_ma20, (int, float)) else volume_ma20
            current_volume_scalar = current_volume.item() if hasattr(current_volume, 'item') else float(current_volume)
            volume_ratio = current_volume_scalar / volume_ma20_scalar if volume_ma20_scalar > 0 else 1
            
            # Price Levels
            current_price = bars_df['Close'].iloc[-1]
            # Ensure current_price is scalar
            current_price = float(current_price.item()) if hasattr(current_price, 'item') else float(current_price)
            
            # Elliott Wave simplified (just counting recent swings)
            elliott_value = self._elliott_wave_value(bars_df)
            
            # Fibonacci levels
            fib_levels = self._fibonacci_levels(bars_df)
            
            # Liquidity sweep pattern
            liq_sweep = self._liquidity_sweep(bars_df)
            
            indicators = {
                'timestamp': datetime.now(),
                'current_price': current_price,
                
                # Trend
                'ema50': float(ema50),
                'ema200': float(ema200),
                'ema_trend': 'UPTREND' if float(ema50) > float(ema200) else 'DOWNTREND',
                
                # Momentum
                'rsi': rsi14,
                'rsi_level': self._rsi_level(rsi14),
                'macd': macd_line,
                'macd_signal': signal_line,
                'macd_hist': macd_hist,
                'macd_signal': self._macd_signal_direction(macd_line, signal_line),
                
                # Volatility
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'atr': atr14,
                'atr_percent': (atr14 / current_price * 100) if current_price > 0 else 0,
                
                # Volume
                'volume_ratio': volume_ratio,
                'volume_confirmation': 'STRONG' if volume_ratio > 1.5 else 'WEAK',
                
                # Elliott Wave
                'elliott_value': elliott_value,
                
                # Fibonacci
                'fib_resistance': fib_levels['resistance'],
                'fib_support': fib_levels['support'],
                
                # Liquidity Sweep
                'liquidity_sweep': liq_sweep['signal'],
                'swing_high': liq_sweep['swing_high'],
                'swing_low': liq_sweep['swing_low'],
                'liquidity_sweep_desc': liq_sweep['description'],
            }
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return self._empty_indicators()
    
    def _ema(self, series, period):
        """Exponential Moving Average"""
        if len(series) < period:
            val = series.iloc[-1]
            return val.item() if hasattr(val, 'item') else float(val)
        ema_result = series.ewm(span=period, adjust=False).mean()
        val = ema_result.iloc[-1]
        return val.item() if hasattr(val, 'item') else float(val)
    
    def _sma(self, series, period):
        """Simple Moving Average"""
        if len(series) < period:
            val = series.mean()
            return val.item() if hasattr(val, 'item') else float(val)
        rolling_mean = series.rolling(window=period).mean()
        val = rolling_mean.iloc[-1]
        return val.item() if hasattr(val, 'item') else float(val)
    
    def _rsi(self, series, period=14):
        """Relative Strength Index"""
        if len(series) < period + 1:
            return 50  # Neutral RSI
        
        deltas = series.diff()
        gains = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
        losses = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
        
        # Extract scalar values using .item() to avoid Series comparison issues
        gains_val = gains.iloc[-1].item() if hasattr(gains.iloc[-1], 'item') else float(gains.iloc[-1])
        losses_val = losses.iloc[-1].item() if hasattr(losses.iloc[-1], 'item') else float(losses.iloc[-1])
        
        # Avoid division by zero
        if losses_val == 0 or gains_val == 0:
            return 50
        
        rs = gains_val / losses_val
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _rsi_level(self, rsi):
        """Interpret RSI value"""
        if rsi > 70:
            return 'OVERBOUGHT'
        elif rsi < 30:
            return 'OVERSOLD'
        else:
            return 'NEUTRAL'
    
    def _macd(self, series):
        """MACD (Moving Average Convergence Divergence)"""
        if len(series) < 26:
            return 0, 0, 0
        
        ema12 = series.ewm(span=12, adjust=False).mean()
        ema26 = series.ewm(span=26, adjust=False).mean()
        
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        # Extract scalar values explicitly
        return float(macd_line.iloc[-1].item()), float(signal_line.iloc[-1].item()), float(macd_hist.iloc[-1].item())
    
    def _macd_signal_direction(self, macd_line, signal_line):
        """MACD crossover direction"""
        # Convert to scalars explicitly
        macd_val = float(macd_line)
        signal_val = float(signal_line)
        
        if macd_val > signal_val:
            return 'BULLISH'
        elif macd_val < signal_val:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _bollinger_bands(self, series, period=20):
        """Bollinger Bands"""
        if len(series) < period:
            val = series.iloc[-1]
            val_scalar = float(val.item()) if hasattr(val, 'item') else float(val)
            return val_scalar, val_scalar, val_scalar
        
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        
        # Explicitly convert to float
        upper_val = float(upper.iloc[-1].item())
        sma_val = float(sma.iloc[-1].item())
        lower_val = float(lower.iloc[-1].item())
        
        return upper_val, sma_val, lower_val
    
    def _atr(self, bars_df, period=14):
        """Average True Range"""
        if len(bars_df) < period:
            return 0
        
        # Calculate True Range
        high_low = bars_df['High'] - bars_df['Low']
        high_close = abs(bars_df['High'] - bars_df['Close'].shift())
        low_close = abs(bars_df['Low'] - bars_df['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        atr_val = atr.iloc[-1]
        # Use .item() to extract scalar properly
        return float(atr_val.item()) if atr_val is not None else 0
    
    def _elliott_wave_value(self, bars_df):
        """Simplified Elliott Wave momentum indicator"""
        if len(bars_df) < 5:
            return 0
        
        # Count recent up/down bars
        closes = bars_df['Close'].tail(5)
        diffs = closes.diff()[1:]  # Skip first NaN
        
        up_count = (diffs > 0).sum()
        down_count = (diffs < 0).sum()
        
        return up_count - down_count  # Range: -5 to +5
    
    def _fibonacci_levels(self, bars_df):
        """Calculate Fibonacci support/resistance"""
        if len(bars_df) < 20:
            return {'support': 0, 'resistance': 0}
        
        # High and low from last 20 bars
        recent_high = bars_df['High'].tail(20).max()
        recent_low = bars_df['Low'].tail(20).min()
        diff = recent_high - recent_low
        
        # Fibonacci levels: 0.618 and 1.618
        support = recent_low + (diff * 0.382)
        resistance = recent_high - (diff * 0.382)
        
        return {
            'support': support,
            'resistance': resistance,
            'range': diff
        }
    
    def _liquidity_sweep(self, bars_df, lookback=20, sweep_min_pct=0.001,
                         sweep_max_pct=0.003, max_candles=3):
        """
        Detect liquidity sweep pattern on real-time bars.

        A sweep fires when:
          LONG:  any of the last max_candles bars wicked 0.1-0.3 % below
                 the swing_low, AND the current bar closes back above it.
          SHORT: any of the last max_candles bars wicked 0.1-0.3 % above
                 the swing_high, AND the current bar closes back below it.

        Returns dict: signal ('LONG_SWEEP'|'SHORT_SWEEP'|'NONE'),
                      swing_high, swing_low, description
        """
        min_required = lookback + max_candles + 1
        if len(bars_df) < min_required:
            return {'signal': 'NONE', 'swing_high': 0, 'swing_low': 0, 'description': ''}
        
        # Pivot window: bars BEFORE the sweep zone (exclude last max_candles bars)
        pivot_bars = bars_df.iloc[-(lookback + max_candles):-max_candles]
        swing_high = float(pivot_bars['High'].max())
        swing_low  = float(pivot_bars['Low'].min())
        
        # Sweep zone: the most recent max_candles bars
        sweep_bars = bars_df.iloc[-max_candles:]
        current_close = float(bars_df['Close'].iloc[-1])
        
        lows  = [float(v) for v in sweep_bars['Low'].values]
        highs = [float(v) for v in sweep_bars['High'].values]
        
        # === BULLISH LIQUIDITY SWEEP ===
        if swing_low > 0:
            swept_below = any(l < swing_low * (1 - sweep_min_pct) for l in lows)
            not_too_deep = all(l >= swing_low * (1 - sweep_max_pct) for l in lows)
            reversed_up  = current_close > swing_low
            
            if swept_below and not_too_deep and reversed_up:
                return {
                    'signal': 'LONG_SWEEP',
                    'swing_high': swing_high,
                    'swing_low': swing_low,
                    'description': f'Bullish sweep below ${swing_low:.2f} → reversed to ${current_close:.2f}',
                }
        
        # === BEARISH LIQUIDITY SWEEP ===
        if swing_high > 0:
            swept_above  = any(h > swing_high * (1 + sweep_min_pct) for h in highs)
            not_too_high = all(h <= swing_high * (1 + sweep_max_pct) for h in highs)
            reversed_down = current_close < swing_high
            
            if swept_above and not_too_high and reversed_down:
                return {
                    'signal': 'SHORT_SWEEP',
                    'swing_high': swing_high,
                    'swing_low': swing_low,
                    'description': f'Bearish sweep above ${swing_high:.2f} → reversed to ${current_close:.2f}',
                }
        
        return {'signal': 'NONE', 'swing_high': swing_high, 'swing_low': swing_low, 'description': ''}
    
    def _empty_indicators(self):
        """Return empty indicators dict"""
        return {
            'timestamp': datetime.now(),
            'current_price': 0,
            'ema50': 0,
            'ema200': 0,
            'ema_trend': 'UNKNOWN',
            'rsi': 50,
            'rsi_level': 'NEUTRAL',
            'macd': 0,
            'macd_signal': 0,
            'macd_hist': 0,
            'bb_upper': 0,
            'bb_middle': 0,
            'bb_lower': 0,
            'atr': 0,
            'atr_percent': 0,
            'volume_ratio': 1,
            'volume_confirmation': 'WEAK',
            'elliott_value': 0,
            'fib_resistance': 0,
            'fib_support': 0,
            'liquidity_sweep': 'NONE',
            'swing_high': 0,
            'swing_low': 0,
            'liquidity_sweep_desc': '',
        }


if __name__ == "__main__":
    # Test with sample data
    import yfinance as yf
    
    # Download test data
    test_data = yf.download('AAPL', period='30d', interval='1d', progress=False)
    
    calc = RealtimeIndicatorCalculator(debug=True)
    indicators = calc.calculate_all(test_data)
    
    print("\n=== Real-Time Indicators ===")
    for key, value in indicators.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
