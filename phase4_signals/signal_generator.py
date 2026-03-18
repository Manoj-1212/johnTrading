"""
phase4_signals/signal_generator.py — Live Buy/Sell Signal Generator
Generates today's signals based on latest indicator values
"""

import pandas as pd
from phase2_indicators.combiner import build_full_indicator_set, SIGNAL_COLS
from config import MIN_SIGNALS_TO_BUY


class SignalGenerator:
    """Generate live trading signals based on indicator analysis."""
    
    @staticmethod
    def generate(df: pd.DataFrame, ticker: str) -> dict:
        """
        Generate signal for a ticker based on latest data.
        
        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame (will calculate indicators)
        ticker : str
            Ticker symbol
        
        Returns
        -------
        dict
            Signal information including action (BUY/SELL/HOLD) and confidence
        """
        # Calculate all indicators
        df = build_full_indicator_set(df)
        
        # Get latest bar
        latest = df.iloc[-1]
        
        # List of active and missing signals
        active = [s.replace('_signal', '') for s in SIGNAL_COLS if latest.get(s, False)]
        missing = [s.replace('_signal', '') for s in SIGNAL_COLS if not latest.get(s, False)]
        
        signal_count = int(latest['signal_count'])
        mandatory_ok = bool(latest['mandatory_ok'])
        
        # Determine action
        if mandatory_ok and signal_count >= MIN_SIGNALS_TO_BUY:
            action = 'BUY'
        elif signal_count <= 2:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Confidence level based on signal count
        if signal_count >= 6:
            confidence = 'HIGH'
        elif signal_count >= 4:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'ticker': ticker,
            'date': str(df.index[-1].date()),
            'action': action,
            'signal_count': signal_count,
            'mandatory_ok': mandatory_ok,
            'confidence': confidence,
            'signals_active': active,
            'signals_missing': missing,
            'composite_score': round(float(latest['composite_score']), 2),
            'price': round(float(latest['Close']), 2),
            'rsi': round(float(latest['RSI']), 1) if 'RSI' in latest else None,
        }
