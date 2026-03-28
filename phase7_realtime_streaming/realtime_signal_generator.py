"""
Real-Time Signal Generator
Generates BUY/SELL signals in real-time based on 1-minute bars
"""

import pandas as pd
from datetime import datetime
from enum import Enum

class SignalAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalConfidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RealtimeSignalGenerator:
    """
    Generates real-time trading signals with confidence levels.
    
    Signal Rules:
    - BUY: EMA50 > EMA200, RSI < 70, MACD bullish, Volume > average
    - SELL: EMA50 < EMA200, RSI > 30, MACD bearish, Price at resistance
    - HOLD: No clear signal
    
    Confidence Calculation:
    - HIGH: 4+ indicators agree
    - MEDIUM: 3 indicators agree
    - LOW: 2 or fewer indicators agree
    
    Usage:
        gen = RealtimeSignalGenerator()
        signal = gen.generate_signal(ticker, indicators, past_position)
    """
    
    def __init__(self, debug=False):
        self.debug = debug
    
    def generate_signal(self, ticker, indicators, current_position=None):
        """
        Generate signal for a ticker based on current indicators.
        
        Args:
            ticker: Stock ticker
            indicators: Dict from RealtimeIndicatorCalculator
            current_position: Current position data if any (for exit signals)
        
        Returns:
            dict: {
                'ticker': ticker,
                'action': 'BUY'|'SELL'|'HOLD',
                'confidence': 'HIGH'|'MEDIUM'|'LOW',
                'price': current_price,
                'timestamp': datetime,
                'reasons': [list of reasons],
                'indicators': {dict of indicator values}
            }
        """
        
        reasons = []
        buy_signals = 0
        sell_signals = 0
        
        current_price = indicators.get('current_price', 0)
        
        # === TREND ANALYSIS ===
        if indicators.get('ema_trend') == 'UPTREND':
            buy_signals += 1
            reasons.append("EMA50 > EMA200 (Uptrend)")
        else:
            sell_signals += 1
            reasons.append("EMA50 < EMA200 (Downtrend)")
        
        # === RSI ANALYSIS ===
        rsi = indicators.get('rsi', 50)
        if rsi < 30:  # Oversold - potential bounce
            buy_signals += 1
            reasons.append(f"RSI {rsi:.0f} (Oversold - Bounce potential)")
        elif rsi > 70:  # Overbought - potential pullback
            sell_signals += 1
            reasons.append(f"RSI {rsi:.0f} (Overbought - Pullback expected)")
        else:
            reasons.append(f"RSI {rsi:.0f} (Neutral)")
        
        # === MACD ANALYSIS ===
        macd_direction = indicators.get('macd_signal', 'NEUTRAL')
        if macd_direction == 'BULLISH':
            buy_signals += 1
            reasons.append("MACD bullish (Line > Signal)")
        elif macd_direction == 'BEARISH':
            sell_signals += 1
            reasons.append("MACD bearish (Line < Signal)")
        else:
            reasons.append("MACD neutral (Line ≈ Signal)")
        
        # === VOLUME ANALYSIS ===
        volume_confirmation = indicators.get('volume_confirmation', 'WEAK')
        volume_ratio = indicators.get('volume_ratio', 1)
        if volume_confirmation == 'STRONG':
            reasons.append(f"Strong volume ({volume_ratio:.1f}x average)")
            # Volume confirms trend direction
            if indicators.get('ema_trend') == 'UPTREND':
                buy_signals += 1
            else:
                sell_signals += 1
        else:
            reasons.append(f"Weak volume ({volume_ratio:.1f}x average)")
        
        # === BOLLINGER BANDS ANALYSIS ===
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        bb_middle = indicators.get('bb_middle', 0)
        
        if current_price > bb_upper:
            sell_signals += 1
            reasons.append("Price above upper Bollinger Band (Overbought)")
        elif current_price < bb_lower:
            buy_signals += 1
            reasons.append("Price below lower Bollinger Band (Oversold)")
        
        # === EXIT SIGNALS (if currently holding) ===
        if current_position:
            position_type = current_position.get('type', 'LONG')
            entry_price = current_position.get('entry_price', 0)
            
            # Take profit: 2% profit target
            if position_type == 'LONG' and entry_price > 0:
                profit_target = entry_price * 1.02
                if current_price >= profit_target:
                    sell_signals += 1
                    reasons.append(f"Take profit (Target: ${profit_target:.2f})")
            
            # Stop loss: 1.5% stop
            if position_type == 'LONG' and entry_price > 0:
                stop_loss = entry_price * 0.985
                if current_price <= stop_loss:
                    sell_signals += 2  # Extra weight to stop loss
                    reasons.append(f"Stop loss (${stop_loss:.2f})")
        
        # === DETERMINE SIGNAL ===
        action = self._determine_action(buy_signals, sell_signals, current_price, indicators)
        confidence = self._calculate_confidence(buy_signals, sell_signals)
        
        signal = {
            'ticker': ticker,
            'action': action.value,
            'confidence': confidence.value,
            'price': current_price,
            'timestamp': datetime.now(),
            'reasons': reasons,
            'indicators': {
                'ema50': indicators.get('ema50', 0),
                'ema200': indicators.get('ema200', 0),
                'rsi': rsi,
                'macd': indicators.get('macd', 0),
                'atr': indicators.get('atr', 0),
                'volume_ratio': volume_ratio,
            },
            'signal_strength': max(buy_signals, sell_signals),
        }
        
        if self.debug:
            self._print_signal(signal)
        
        return signal
    
    def _determine_action(self, buy_signals, sell_signals, price, indicators):
        """
        Determine final action: BUY, SELL, or HOLD
        
        Logic:
        - Use trend as primary filter
        - In uptrend: prefer BUY
        - In downtrend: prefer SELL
        - If unclear: HOLD
        """
        
        trend = indicators.get('ema_trend', 'UNKNOWN')
        
        # If strong agreement on one direction
        if buy_signals >= 3 and buy_signals > sell_signals:
            return SignalAction.BUY
        elif sell_signals >= 3 and sell_signals > buy_signals:
            return SignalAction.SELL
        
        # Moderate signals with trend confirmation
        if buy_signals >= sell_signals + 1 and trend == 'UPTREND':
            return SignalAction.BUY
        elif sell_signals >= buy_signals + 1 and trend == 'DOWNTREND':
            return SignalAction.SELL
        
        # Default to HOLD if no clear signal
        return SignalAction.HOLD
    
    def _calculate_confidence(self, buy_signals, sell_signals):
        """Calculate confidence level based on signal strength"""
        total_agreement = max(buy_signals, sell_signals)
        
        if total_agreement >= 5:
            return SignalConfidence.HIGH
        elif total_agreement >= 3:
            return SignalConfidence.MEDIUM
        else:
            return SignalConfidence.LOW
    
    def _print_signal(self, signal):
        """Print signal details for debugging"""
        timestamp = signal['timestamp'].strftime('%H:%M:%S')
        print(f"\n[{timestamp}] {signal['ticker']}")
        print(f"  Action: {signal['action']} ({signal['confidence']})")
        print(f"  Price: ${signal['price']:.2f}")
        print(f"  Reasons:")
        for reason in signal['reasons']:
            print(f"    • {reason}")


class MultiTickerSignalGenerator:
    """
    Generate signals for multiple tickers simultaneously.
    Returns ranked list of best opportunities.
    """
    
    def __init__(self):
        self.generator = RealtimeSignalGenerator()
    
    def generate_all_signals(self, tickers_indicators, current_positions=None):
        """
        Generate signals for all tickers.
        
        Args:
            tickers_indicators: Dict[ticker -> indicators_dict]
            current_positions: Dict[ticker -> position_dict]
        
        Returns:
            List of signals, ranked by confidence and strength
        """
        
        signals = []
        current_positions = current_positions or {}
        
        for ticker, indicators in tickers_indicators.items():
            current_pos = current_positions.get(ticker)
            signal = self.generator.generate_signal(ticker, indicators, current_pos)
            signals.append(signal)
        
        # Rank by: Action (SELL/BUY first), then confidence, then strength
        def rank_key(sig):
            action_priority = {'SELL': 0, 'BUY': 1, 'HOLD': 2}
            confidence_priority = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            
            return (
                action_priority.get(sig['action'], 2),
                confidence_priority.get(sig['confidence'], 2),
                -sig['signal_strength'],  # Higher strength first
            )
        
        signals.sort(key=rank_key)
        
        return signals


if __name__ == "__main__":
    # Test with realistic indicator data
    sample_indicators = {
        'current_price': 150.25,
        'ema50': 149.50,
        'ema200': 148.00,
        'ema_trend': 'UPTREND',
        'rsi': 35,
        'macd': 0.45,
        'macd_signal': 0.40,
        'macd_signal': 'BULLISH',
        'bb_upper': 152.00,
        'bb_middle': 150.00,
        'bb_lower': 148.00,
        'atr': 2.5,
        'volume_ratio': 1.8,
        'volume_confirmation': 'STRONG',
    }
    
    gen = RealtimeSignalGenerator(debug=True)
    signal = gen.generate_signal('AAPL', sample_indicators)
    
    print("\n=== Generated Signal ===")
    for key, value in signal.items():
        if key != 'reasons' and key != 'indicators':
            print(f"{key}: {value}")
