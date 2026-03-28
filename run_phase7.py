"""
Phase 7 Main: Real-Time Intraday Trading Orchestrator
Coordinates data streaming, indicator calculation, and signal generation
"""

import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
import pytz

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase7_realtime_streaming.realtime_data_streamer import RealtimeDataStreamer
from phase7_realtime_streaming.realtime_indicator_calculator import RealtimeIndicatorCalculator
from phase7_realtime_streaming.realtime_signal_generator import RealtimeSignalGenerator, MultiTickerSignalGenerator

# Import config
try:
    from trading_new_config import TICKERS, PAPER_CAPITAL
except ImportError:
    # Define defaults if config not available
    TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    PAPER_CAPITAL = 10000

class Phase7Orchestrator:
    """
    Coordinates real-time trading pipeline:
    1. Stream 1-minute bars during market hours
    2. Calculate indicators on every new bar
    3. Generate signals based on indicators
    4. Log all activity for later execution
    """
    
    def __init__(self, tickers=None, debug=False):
        self.tickers = tickers or TICKERS
        self.debug = debug
        
        # Initialize components
        self.streamer = RealtimeDataStreamer({}, debug=debug)
        self.indicator_calc = RealtimeIndicatorCalculator(debug=debug)
        self.signal_gen = RealtimeSignalGenerator(debug=debug)
        self.multi_signal_gen = MultiTickerSignalGenerator()
        
        # Output directory
        self.output_dir = Path('phase7_realtime_streaming/realtime_signals')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path('phase7_realtime_streaming/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_start = datetime.now()
        self.bars_processed = 0
        self.signals_generated = 0
        self.session_log = []
        
        self.est = pytz.timezone('US/Eastern')
        
    def run_continuous(self, duration_minutes=390, update_interval=60):
        """
        Run real-time trading for duration_minutes.
        
        Args:
            duration_minutes: How long to run (390 = full market day)
            update_interval: Seconds between bar updates
        """
        
        print("=" * 70)
        print("PHASE 7: REAL-TIME INTRADAY TRADING")
        print("=" * 70)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tickers: {self.tickers}")
        print(f"Duration: {duration_minutes} minutes")
        print("=" * 70)
        
        # Pre-download daily data for baseline
        print(f"\n[1/3] Downloading daily baseline data...")
        self.streamer.download_daily_base(self.tickers)
        print(f"✓ Downloaded daily data for {len(self.tickers)} tickers")
        
        # Current bars cache
        ticker_bars = {ticker: None for ticker in self.tickers}
        ticker_indicators = {ticker: {} for ticker in self.tickers}
        
        print(f"\n[2/3] Starting live data stream...")
        print(f"Streaming {len(self.tickers)} tickers at {update_interval}s intervals")
        print("-" * 70)
        
        # Stream and process bars
        signal_count = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        
        try:
            for bar_data in self.streamer.stream_live(
                self.tickers, 
                update_interval_seconds=update_interval,
                duration_minutes=duration_minutes
            ):
                ticker = bar_data['ticker']
                bars = bar_data['bars']
                timestamp = bar_data['timestamp']
                
                # Update bars cache
                ticker_bars[ticker] = bars
                
                # Calculate indicators for this ticker
                indicators = self.indicator_calc.calculate_all(bars)
                ticker_indicators[ticker] = indicators
                
                # Generate signal for this ticker
                signal = self.signal_gen.generate_signal(ticker, indicators)
                
                # Log signal
                self._log_signal(signal)
                signal_count[signal['action']] += 1
                
                self.bars_processed += 1
                self.signals_generated += 1
                
                # Save signal to file
                self._save_signal(signal, timestamp)
                
                # Print real-time update
                self._print_realtime_update(signal)
                
                # Periodically save session state
                if self.signals_generated % 50 == 0:
                    self._save_session_state(ticker_indicators, signal_count)
            
            # Session complete
            print("\n" + "=" * 70)
            print("SESSION COMPLETE")
            print("=" * 70)
            self._print_session_summary(signal_count)
            self._save_session_state(ticker_indicators, signal_count)
            
        except KeyboardInterrupt:
            print("\n\nStream interrupted by user")
            self._print_session_summary(signal_count)
            self._save_session_state(ticker_indicators, signal_count)
        except Exception as e:
            print(f"\n\nError during stream: {e}")
            raise
    
    def _log_signal(self, signal):
        """Log signal to session log"""
        log_entry = {
            'timestamp': signal['timestamp'].isoformat(),
            'ticker': signal['ticker'],
            'action': signal['action'],
            'confidence': signal['confidence'],
            'price': signal['price'],
            'strength': signal['signal_strength'],
        }
        self.session_log.append(log_entry)
    
    def _save_signal(self, signal, timestamp):
        """Save individual signal to file"""
        filename = self.output_dir / f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{signal['ticker']}.json"
        
        signal_data = {
            'timestamp': signal['timestamp'].isoformat(),
            'ticker': signal['ticker'],
            'action': signal['action'],
            'confidence': signal['confidence'],
            'price': signal['price'],
            'reasons': signal['reasons'],
            'indicators': signal['indicators'],
            'signal_strength': signal['signal_strength'],
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(signal_data, f, indent=2)
        except Exception as e:
            print(f"Error saving signal: {e}")
    
    def _save_session_state(self, indicators_by_ticker, signal_counts):
        """Save current session state"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.log_dir / f"session_state_{timestamp}.json"
        
        # Create summary
        summary = {
            'session_start': self.session_start.isoformat(),
            'current_time': datetime.now().isoformat(),
            'elapsed_minutes': (datetime.now() - self.session_start).total_seconds() / 60,
            'bars_processed': self.bars_processed,
            'signals_generated': self.signals_generated,
            'signal_counts': signal_counts,
            'latest_indicators': {
                ticker: {
                    'price': ind.get('current_price', 0),
                    'ema_trend': ind.get('ema_trend', 'UNKNOWN'),
                    'rsi': ind.get('rsi', 0),
                    'macd_signal': ind.get('macd_signal', 'NEUTRAL'),
                }
                for ticker, ind in indicators_by_ticker.items()
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            print(f"Error saving session state: {e}")
    
    def _print_realtime_update(self, signal):
        """Print single signal in real-time"""
        timestamp = signal['timestamp'].strftime('%H:%M:%S')
        action_symbol = '📈' if signal['action'] == 'BUY' else '📉' if signal['action'] == 'SELL' else '➡️'
        
        confidence_color = {
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '⚪'
        }
        
        print(f"[{timestamp}] {action_symbol} {signal['ticker']:5} | "
              f"{signal['action']:4} | {confidence_color.get(signal['confidence'], '')} {signal['confidence']:6} | "
              f"${signal['price']:8.2f} | Strength: {signal['signal_strength']}")
    
    def _print_session_summary(self, signal_counts):
        """Print summary of entire session"""
        elapsed = datetime.now() - self.session_start
        elapsed_minutes = elapsed.total_seconds() / 60
        
        print(f"\nSession Duration: {elapsed_minutes:.1f} minutes")
        print(f"Bars Processed: {self.bars_processed}")
        print(f"Signals Generated: {self.signals_generated}")
        print(f"\nSignal Distribution:")
        print(f"  BUY:  {signal_counts['BUY']:3} ({100*signal_counts['BUY']/max(1, self.signals_generated):.1f}%)")
        print(f"  SELL: {signal_counts['SELL']:3} ({100*signal_counts['SELL']/max(1, self.signals_generated):.1f}%)")
        print(f"  HOLD: {signal_counts['HOLD']:3} ({100*signal_counts['HOLD']/max(1, self.signals_generated):.1f}%)")
        
        print(f"\nSignals saved to: {self.output_dir}")
        print(f"Logs saved to: {self.log_dir}")
        print("=" * 70)

def main():
    """Main entry point"""
    
    # You can customize here
    tickers = TICKERS if 'TICKERS' in dir() else [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'JPM', 'JNJ', 'XOM', 'WMT', 'PG',
        'META', 'TSLA', 'CUDA', 'AMD', 'INTC',
        'BA', 'GS', 'BRK.B', 'NFLX', 'ADBE'
    ]
    
    # Create and run orchestrator
    orchestrator = Phase7Orchestrator(tickers=tickers, debug=False)
    
    # Run for 10 minutes for testing (use 390 for full day)
    orchestrator.run_continuous(duration_minutes=10, update_interval=60)

if __name__ == "__main__":
    main()
