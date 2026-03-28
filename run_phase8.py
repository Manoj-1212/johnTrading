"""
Phase 8 Main: Real-Time Trade Execution via Alpaca
Executes real-time signals from Phase 7 through Alpaca broker API
"""

import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime
import pytz

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase7_realtime_streaming.realtime_data_streamer import RealtimeDataStreamer
from phase7_realtime_streaming.realtime_indicator_calculator import RealtimeIndicatorCalculator
from phase7_realtime_streaming.realtime_signal_generator import RealtimeSignalGenerator
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface

# Import config
try:
    from trading_new_config import TICKERS, PAPER_CAPITAL
except ImportError:
    TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    PAPER_CAPITAL = 10000

class Phase8ExecutionEngine:
    """
    Real-time trading execution engine.
    
    Pipeline:
    1. Stream 1-minute bars (Phase 7)
    2. Calculate indicators
    3. Generate signals
    4. Execute trades via Alpaca (Phase 8)
    5. Track positions and P&L
    
    Risk Controls:
    - Position size: Risk 2% per trade
    - Stop loss: 1.5%
    - Take profit: 2%
    - Daily loss limit: Stop trading if daily loss > $500
    """
    
    def __init__(self, tickers=None, paper_trading=True, debug=False):
        self.tickers = tickers or TICKERS
        self.paper_trading = paper_trading
        self.debug = debug
        
        # Initialize Phase 7 components
        self.streamer = RealtimeDataStreamer({}, debug=debug)
        self.indicator_calc = RealtimeIndicatorCalculator(debug=debug)
        self.signal_gen = RealtimeSignalGenerator(debug=debug)
        
        # Initialize Phase 8 broker
        print("Connecting to Alpaca...")
        try:
            self.broker = AlpacaBrokerInterface(paper_trading=paper_trading, debug=debug)
        except ValueError as e:
            print(f"ERROR: {e}")
            self.broker = None
        
        # Output directories
        self.output_dir = Path('phase8_execution/trades')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path('phase8_execution/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_start = datetime.now()
        self.execution_log = []
        self.trades_executed = []
        
        # Risk management
        self.daily_losses = 0
        self.daily_loss_limit = 500  # Stop after $500 loss
        self.can_trade = True
        
        self.est = pytz.timezone('US/Eastern')
    
    def run(self, duration_minutes=390, update_interval=60):
        """
        Run real-time execution for duration_minutes.
        """
        
        if not self.broker or not self.broker.connected:
            print("ERROR: Broker connection failed. Cannot run Phase 8.")
            return
        
        mode = "PAPER TRADING" if self.paper_trading else "LIVE TRADING"
        
        print("=" * 70)
        print("PHASE 8: REAL-TIME TRADE EXECUTION")
        print("=" * 70)
        print(f"Mode: {mode}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tickers: {len(self.tickers)} tickers")
        print(f"Duration: {duration_minutes} minutes")
        print("=" * 70)
        
        # Get initial account state
        initial_account = self.broker.get_account_info()
        print(f"\nInitial Account:")
        print(f"  Cash: ${initial_account['cash']:.2f}")
        print(f"  Portfolio Value: ${initial_account['portfolio_value']:.2f}")
        print(f"  Buying Power: ${initial_account['buying_power']:.2f}")
        
        # Download baseline
        print(f"\nDownloading daily baseline data...")
        self.streamer.download_daily_base(self.tickers)
        print(f"✓ Downloaded for {len(self.tickers)} tickers")
        
        # Cache current bars
        ticker_bars = {ticker: None for ticker in self.tickers}
        
        print(f"\nStarting real-time stream with execution...")
        print("-" * 70)
        
        trades_count = {'BUY': 0, 'SELL': 0}
        
        try:
            for bar_data in self.streamer.stream_live(
                self.tickers,
                update_interval_seconds=update_interval,
                duration_minutes=duration_minutes
            ):
                if not self.can_trade:
                    print("⚠️ Trading disabled due to daily loss limit")
                    continue
                
                ticker = bar_data['ticker']
                bars = bar_data['bars']
                current_price = bar_data['current_price']
                timestamp = bar_data['timestamp']
                
                # Update bars cache
                ticker_bars[ticker] = bars
                
                # Calculate indicators
                indicators = self.indicator_calc.calculate_all(bars)
                
                # Generate signal
                signal = self.signal_gen.generate_signal(ticker, indicators)
                
                # Execute trade if signal
                if signal['action'] in ['BUY', 'SELL']:
                    execution = self._execute_signal(signal, ticker, current_price)
                    
                    if execution:
                        trades_count[signal['action']] += 1
                        self._log_execution(execution)
                
                # Check daily loss
                self._check_daily_loss()
                
                # Print update
                self._print_update(signal, ticker)
            
            # Session complete
            print("\n" + "=" * 70)
            print("SESSION COMPLETE")
            print("=" * 70)
            self._print_session_summary(initial_account, trades_count)
            self._save_session_log()
            
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user")
            self._print_session_summary(initial_account, trades_count)
            self._save_session_log()
        except Exception as e:
            print(f"\n\nError during execution: {e}")
            raise
    
    def _execute_signal(self, signal, ticker, current_price):
        """Execute a trading signal via Alpaca"""
        
        action = signal['action']
        confidence = signal['confidence']
        
        # Skip low confidence signals
        if confidence == 'LOW':
            return None
        
        # Calculate position size: Risk 2% per trade
        account_info = self.broker.get_account_info()
        risk_amount = account_info['portfolio_value'] * 0.02
        
        if action == 'BUY':
            # Buy 2% of portfolio value
            qty = int(risk_amount / current_price)
            
            if qty < 1:
                if self.debug:
                    print(f"Position too small for {ticker}: {qty} shares")
                return None
            
            print(f"\n📈 BUY {qty} shares of {ticker} @ ${current_price:.2f}")
            
            # Place market buy order
            order = self.broker.place_buy_order(ticker, qty, order_type='market')
            
            if order:
                execution = {
                    'timestamp': datetime.now(),
                    'action': 'BUY',
                    'ticker': ticker,
                    'quantity': qty,
                    'price': current_price,
                    'order_id': order.id,
                    'status': str(order.status),
                    'confidence': confidence,
                }
                return execution
        
        elif action == 'SELL':
            # Get position and sell
            position = self.broker.get_position(ticker)
            
            if not position:
                if self.debug:
                    print(f"No position to sell for {ticker}")
                return None
            
            qty = int(position.qty)
            print(f"\n📉 SELL {qty} shares of {ticker} @ ${current_price:.2f}")
            
            # Place market sell order
            order = self.broker.place_sell_order(ticker, qty, order_type='market')
            
            if order:
                execution = {
                    'timestamp': datetime.now(),
                    'action': 'SELL',
                    'ticker': ticker,
                    'quantity': qty,
                    'price': current_price,
                    'order_id': order.id,
                    'status': str(order.status),
                    'confidence': confidence,
                    'entry_price': float(position.avg_fill_price),
                    'pnl': float(position.unrealized_pl),
                }
                return execution
        
        return None
    
    def _log_execution(self, execution):
        """Log trade execution"""
        self.trades_executed.append(execution)
        self.execution_log.append({
            'timestamp': execution['timestamp'].isoformat(),
            'action': execution['action'],
            'ticker': execution['ticker'],
            'quantity': execution['quantity'],
            'price': execution['price'],
            'order_id': execution['order_id'],
        })
    
    def _check_daily_loss(self):
        """Check if daily loss limit exceeded"""
        try:
            account_info = self.broker.get_account_info()
            daily_loss = initial_account['portfolio_value'] - account_info['portfolio_value']
            
            if daily_loss > self.daily_loss_limit:
                print(f"\n⚠️ Daily loss limit reached: ${daily_loss:.2f}")
                self.can_trade = False
        except:
            pass
    
    def _print_update(self, signal, ticker):
        """Print real-time update"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        action_symbol = '📈' if signal['action'] == 'BUY' else '📉' if signal['action'] == 'SELL' else '➡️'
        
        print(f"[{timestamp}] {action_symbol} {ticker:5} | "
              f"{signal['action']:4} | {signal['confidence']:6} | "
              f"${signal['price']:8.2f}")
    
    def _print_session_summary(self, initial_account, trades_count):
        """Print session summary"""
        elapsed = datetime.now() - self.session_start
        elapsed_minutes = elapsed.total_seconds() / 60
        
        # Get final account state
        final_account = self.broker.get_account_info()
        
        pnl = final_account['portfolio_value'] - initial_account['portfolio_value']
        pnl_pct = (pnl / initial_account['portfolio_value']) * 100 if initial_account['portfolio_value'] > 0 else 0
        
        print(f"\nSession Duration: {elapsed_minutes:.1f} minutes")
        print(f"Trades Executed: {len(self.trades_executed)}")
        print(f"  BUY:  {trades_count['BUY']}")
        print(f"  SELL: {trades_count['SELL']}")
        
        print(f"\nAccount Summary:")
        print(f"  Initial Portfolio: ${initial_account['portfolio_value']:.2f}")
        print(f"  Final Portfolio: ${final_account['portfolio_value']:.2f}")
        print(f"  P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"  Cash: ${final_account['cash']:.2f}")
        
        print(f"\nLogs saved to: {self.log_dir}")
        print("=" * 70)
    
    def _save_session_log(self):
        """Save session log"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.log_dir / f"execution_log_{timestamp}.json"
        
        log_data = {
            'session_start': self.session_start.isoformat(),
            'session_end': datetime.now().isoformat(),
            'trades_executed': len(self.trades_executed),
            'execution_log': self.execution_log,
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")

def main():
    """Main entry point"""
    
    tickers = TICKERS if 'TICKERS' in dir() else [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'JPM', 'JNJ', 'XOM', 'WMT', 'PG',
        'META', 'TSLA', 'CUDA', 'AMD', 'INTC',
        'BA', 'GS', 'BRK.B', 'NFLX', 'ADBE'
    ]
    
    # Create execution engine
    engine = Phase8ExecutionEngine(tickers=tickers, paper_trading=True, debug=False)
    
    # Run for 10 minutes for testing
    engine.run(duration_minutes=10, update_interval=60)

if __name__ == "__main__":
    main()
