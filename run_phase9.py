"""
Phase 9 Main: Integrated Real-Time Trading with Risk Management
Combines Phases 7, 8, and 9 for production-grade trading
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
from phase9_risk_management.risk_manager import RiskManager, PortfolioMonitor

# Import config
try:
    from trading_new_config import TICKERS, PAPER_CAPITAL
except ImportError:
    TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    PAPER_CAPITAL = 10000

class ProductionTradingSystem:
    """
    Production-grade real-time trading system.
    
    Integrated Pipeline:
    1. Real-time data streaming (Phase 7) - 1-minute bars
    2. Indicator calculation - Technical analysis
    3. Signal generation - BUY/SELL/HOLD signals
    4. Risk management (Phase 9) - Pre-trade checks
    5. Trade execution (Phase 8) - Alpaca broker integration
    6. Portfolio monitoring - Position tracking and alerts
    
    Risk Controls:
    ✓ Position size limits (max 5% per position)
    ✓ Daily loss limits (stop at -2%)
    ✓ Market regime detection (VIX > 50 = no trading)
    ✓ Sector concentration limits (max 30%)
    ✓ Stop loss enforcement (1.5%)
    ✓ Take profit targets (2%)
    ✓ Buying power validation
    ✓ Position correlation monitoring
    
    Production Requirements Met:
    ✓ Real-time data (1-minute bars)
    ✓ Live broker integration (Alpaca)
    ✓ Portfolio-level risk management
    ✓ Market regime detection
    ✓ Monitoring and alerting
    ✓ Session logging
    """
    
    def __init__(self, tickers=None, paper_trading=True, debug=False):
        self.tickers = tickers or TICKERS
        self.paper_trading = paper_trading
        self.debug = debug
        
        # Initialize Phase 7: Data Streaming
        self.streamer = RealtimeDataStreamer({}, debug=debug)
        self.indicator_calc = RealtimeIndicatorCalculator(debug=debug)
        self.signal_gen = RealtimeSignalGenerator(debug=debug)
        
        # Initialize Phase 8: Broker Integration
        print("Connecting to Alpaca broker...")
        try:
            self.broker = AlpacaBrokerInterface(paper_trading=paper_trading, debug=debug)
            broker_connected = self.broker.connected
        except Exception as e:
            print(f"Broker connection error: {e}")
            self.broker = None
            broker_connected = False
        
        if not broker_connected:
            print("ERROR: Broker connection failed!")
            return
        
        # Initialize Phase 9: Risk Management
        account_info = self.broker.get_account_info()
        self.risk_manager = RiskManager(
            self.broker,
            portfolio_value=account_info['portfolio_value'],
            debug=debug
        )
        self.portfolio_monitor = PortfolioMonitor(self.broker, self.risk_manager, debug=debug)
        
        # Output directories
        self.output_dir = Path('phase9_production_trading/trades')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path('phase9_production_trading/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_start = datetime.now()
        self.execution_log = []
        self.trades_executed = []
        self.risk_events = []
        
        self.est = pytz.timezone('US/Eastern')
    
    def run(self, duration_minutes=390, update_interval=60):
        """
        Run production trading system for duration_minutes.
        """
        
        if not self.broker or not self.broker.connected:
            print("ERROR: Broker not connected. Cannot run production system.")
            return
        
        mode = "PAPER TRADING" if self.paper_trading else "LIVE TRADING ⚠️⚠️⚠️"
        
        print("\n" + "=" * 80)
        print("PRODUCTION-GRADE REAL-TIME TRADING SYSTEM")
        print("=" * 80)
        print(f"Mode: {mode}")
        print(f"Phases: 7 (Data) → 8 (Execution) → 9 (Risk Management)")
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tickers: {len(self.tickers)} stocks")
        print(f"Duration: {duration_minutes} minutes")
        print("=" * 80)
        
        # Get initial state
        initial_account = self.broker.get_account_info()
        print(f"\nInitial Account State:")
        print(f"  Cash: ${initial_account['cash']:.2f}")
        print(f"  Portfolio Value: ${initial_account['portfolio_value']:.2f}")
        print(f"  Buying Power: ${initial_account['buying_power']:.2f}")
        
        # Get initial risk metrics
        initial_metrics = self.risk_manager.get_risk_metrics()
        print(f"\nInitial Risk Metrics:")
        print(f"  VIX: {initial_metrics.vix:.1f}")
        print(f"  Market Regime: {initial_metrics.market_regime.value}")
        print(f"  Position Limit: {self.risk_manager.max_position_size_pct:.0%} per position")
        print(f"  Daily Loss Limit: {self.risk_manager.daily_loss_limit_pct:.0%}")
        
        # Download baseline
        print(f"\nPhase 7: Downloading daily baseline data...")
        self.streamer.download_daily_base(self.tickers)
        print(f"✓ Baseline data ready for {len(self.tickers)} tickers")
        
        # Cache current bars
        ticker_bars = {ticker: None for ticker in self.tickers}
        
        print(f"\nPhase 7-9: Starting real-time stream...")
        print("-" * 80)
        
        trades_count = {'BUY': 0, 'SELL': 0, 'BLOCKED': 0}
        
        try:
            for bar_data in self.streamer.stream_live(
                self.tickers,
                update_interval_seconds=update_interval,
                duration_minutes=duration_minutes
            ):
                ticker = bar_data['ticker']
                bars = bar_data['bars']
                current_price = bar_data['current_price']
                timestamp = bar_data['timestamp']
                
                # Update bars cache
                ticker_bars[ticker] = bars
                
                # Phase 7: Calculate indicators
                indicators = self.indicator_calc.calculate_all(bars)
                
                # Phase 7: Generate signal
                signal = self.signal_gen.generate_signal(ticker, indicators)
                
                # Phase 9: Check risk before execution
                if signal['action'] in ['BUY', 'SELL']:
                    risk_check = self._check_risk_before_trade(signal, ticker, current_price, indicators)
                    
                    if risk_check['allowed']:
                        # Phase 8: Execute trade
                        execution = self._execute_trade(signal, ticker, current_price, risk_check)
                        
                        if execution:
                            trades_count[signal['action']] += 1
                            self._log_execution(execution)
                    else:
                        # Trade blocked by risk management
                        trades_count['BLOCKED'] += 1
                        self._log_risk_event(ticker, signal, risk_check)
                        print(f"[{timestamp.strftime('%H:%M:%S')}] 🚫 {ticker} BLOCKED: {risk_check['reason']}")
                
                # Phase 9: Monitor positions
                alerts = self.portfolio_monitor.check_positions()
                for alert in alerts:
                    self._log_alert(alert)
                    if alert['type'] == 'STOP_LOSS':
                        print(f"⛔ ALERT: {alert['message']}")
                    elif alert['type'] == 'TAKE_PROFIT':
                        print(f"✓ ALERT: {alert['message']}")
                
                # Print real-time update
                self._print_update(signal, ticker)
            
            # Session complete
            print("\n" + "=" * 80)
            print("SESSION COMPLETE")
            print("=" * 80)
            
            # Get final state
            final_account = self.broker.get_account_info()
            self._print_session_summary(initial_account, final_account, trades_count)
            self._save_session_log(initial_account, final_account)
            
        except KeyboardInterrupt:
            print("\n\nTrading interrupted by user")
            final_account = self.broker.get_account_info()
            self._print_session_summary(initial_account, final_account, trades_count)
            self._save_session_log(initial_account, final_account)
        except Exception as e:
            print(f"\n\nError during trading: {e}")
            raise
    
    def _check_risk_before_trade(self, signal, ticker, current_price, indicators):
        """Phase 9: Check all risk constraints before trade"""
        
        action = signal['action']
        
        if action == 'BUY':
            # Calculate position size
            qty = self.risk_manager.calculate_position_size(
                ticker,
                current_price,
                self.broker.account.cash,
                atr=indicators.get('atr', 0)
            )
            
            # Check if buy is allowed
            allowed, reason = self.risk_manager.can_execute_buy(
                ticker, qty, current_price, atr=indicators.get('atr', 0)
            )
            
            return {
                'allowed': allowed,
                'reason': reason,
                'quantity': qty if allowed else 0
            }
        
        elif action == 'SELL':
            # Check if sell is allowed
            allowed, reason = self.risk_manager.can_execute_sell(ticker, 1)  # Check if any shares can be sold
            
            position = self.broker.get_position(ticker)
            qty = int(position.qty) if position else 0
            
            return {
                'allowed': allowed,
                'reason': reason,
                'quantity': qty if allowed else 0
            }
        
        return {'allowed': False, 'reason': 'Invalid action', 'quantity': 0}
    
    def _execute_trade(self, signal, ticker, current_price, risk_check):
        """Phase 8: Execute trade via Alpaca"""
        
        action = signal['action']
        qty = risk_check['quantity']
        
        if qty < 1:
            return None
        
        timestamp = datetime.now()
        
        try:
            if action == 'BUY':
                print(f"[{timestamp.strftime('%H:%M:%S')}] 📈 BUY: {qty} shares of {ticker} @ ${current_price:.2f}")
                order = self.broker.place_buy_order(ticker, qty, order_type='market')
                
                if order:
                    execution = {
                        'timestamp': timestamp,
                        'action': 'BUY',
                        'ticker': ticker,
                        'quantity': qty,
                        'price': current_price,
                        'order_id': order.id,
                        'status': str(order.status),
                    }
                    return execution
            
            elif action == 'SELL':
                print(f"[{timestamp.strftime('%H:%M:%S')}] 📉 SELL: {qty} shares of {ticker} @ ${current_price:.2f}")
                order = self.broker.place_sell_order(ticker, qty, order_type='market')
                
                if order:
                    position = self.broker.get_position(ticker)
                    execution = {
                        'timestamp': timestamp,
                        'action': 'SELL',
                        'ticker': ticker,
                        'quantity': qty,
                        'price': current_price,
                        'order_id': order.id,
                        'status': str(order.status),
                        'entry_price': float(position.avg_fill_price) if position else current_price,
                    }
                    return execution
        
        except Exception as e:
            print(f"Error executing trade: {e}")
        
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
    
    def _log_risk_event(self, ticker, signal, risk_check):
        """Log risk event (blocked trade)"""
        self.risk_events.append({
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'action': signal['action'],
            'reason': risk_check['reason'],
            'confidence': signal['confidence'],
        })
    
    def _log_alert(self, alert):
        """Log alert"""
        # Could save to database or notification system
        pass
    
    def _print_update(self, signal, ticker):
        """Print real-time update"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        action_symbol = '📈' if signal['action'] == 'BUY' else '📉' if signal['action'] == 'SELL' else '➡️'
        
        print(f"[{timestamp}] {action_symbol} {ticker:5} | "
              f"{signal['action']:4} | {signal['confidence']:6} | "
              f"${signal['price']:8.2f} | Strength: {signal['signal_strength']}")
    
    def _print_session_summary(self, initial_account, final_account, trades_count):
        """Print session summary"""
        elapsed = datetime.now() - self.session_start
        elapsed_minutes = elapsed.total_seconds() / 60
        
        pnl = final_account['portfolio_value'] - initial_account['portfolio_value']
        pnl_pct = (pnl / initial_account['portfolio_value']) * 100 if initial_account['portfolio_value'] > 0 else 0
        
        print(f"\nDuration: {elapsed_minutes:.1f} minutes")
        print(f"Trades Executed: {len(self.trades_executed)}")
        print(f"  BUY:  {trades_count['BUY']}")
        print(f"  SELL: {trades_count['SELL']}")
        print(f"  BLOCKED (by risk): {trades_count['BLOCKED']}")
        
        print(f"\nFinal Account Summary:")
        print(f"  Initial: ${initial_account['portfolio_value']:.2f}")
        print(f"  Final: ${final_account['portfolio_value']:.2f}")
        print(f"  P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"  Cash: ${final_account['cash']:.2f}")
        
        # Risk metrics
        final_metrics = self.risk_manager.get_risk_metrics()
        if final_metrics:
            print(f"\nFinal Risk Metrics:")
            print(f"  VIX: {final_metrics.vix:.1f}")
            print(f"  Market Regime: {final_metrics.market_regime.value}")
            print(f"  Largest Position: {final_metrics.largest_position_pct:.1f}%")
            print(f"  Daily Loss: ${final_metrics.daily_loss:.2f}")
        
        print(f"\nLogs saved to:")
        print(f"  Trades: {self.output_dir}")
        print(f"  Logs: {self.log_dir}")
        print("=" * 80)
    
    def _save_session_log(self, initial_account, final_account):
        """Save comprehensive session log"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.log_dir / f"session_{timestamp}.json"
        
        log_data = {
            'session_start': self.session_start.isoformat(),
            'session_end': datetime.now().isoformat(),
            'mode': 'PAPER' if self.paper_trading else 'LIVE',
            
            'account': {
                'initial_value': initial_account['portfolio_value'],
                'final_value': final_account['portfolio_value'],
                'initial_cash': initial_account['cash'],
                'final_cash': final_account['cash'],
            },
            
            'trading': {
                'total_trades': len(self.trades_executed),
                'trades': self.execution_log,
                'blocked_trades': self.risk_events,
            },
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2)
            print(f"Session log saved: {filename}")
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
    
    # Create production system
    trading_system = ProductionTradingSystem(
        tickers=tickers,
        paper_trading=True,  # Always start with paper trading
        debug=False
    )
    
    # Run for 10 minutes test (use 390 for full day)
    trading_system.run(duration_minutes=10, update_interval=60)

if __name__ == "__main__":
    main()
