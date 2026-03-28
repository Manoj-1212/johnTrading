"""
Production Trading System - Automated 24/7 Operation
Runs continuously, automatically trading during market hours
Can be managed with systemd service or cron jobs
"""

import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
import pytz
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase7_realtime_streaming.realtime_data_streamer import RealtimeDataStreamer
from phase7_realtime_streaming.realtime_indicator_calculator import RealtimeIndicatorCalculator
from phase7_realtime_streaming.realtime_signal_generator import RealtimeSignalGenerator
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
from phase9_risk_management.risk_manager import RiskManager, PortfolioMonitor

# Import config
try:
    from trading_new_config import TICKERS, PAPER_CAPITAL
except ImportError:
    TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
               'JPM', 'JNJ', 'XOM', 'WMT', 'PG',
               'META', 'TSLA', 'CUDA', 'AMD', 'INTC',
               'BA', 'GS', 'BRK.B', 'NFLX', 'ADBE']
    PAPER_CAPITAL = 10000

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging for production"""
    
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f'trading_{timestamp}.log'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler (DEBUG level)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# ============================================================================
# MARKET HOURS DETECTION
# ============================================================================

class MarketHours:
    """Detect and manage market hours (US Eastern Time)"""
    
    # Market open: 9:30 AM EST
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 30
    
    # Market close: 4:00 PM EST
    MARKET_CLOSE_HOUR = 16
    MARKET_CLOSE_MINUTE = 0
    
    # Extended hours (optional)
    PRE_MARKET_HOUR = 4
    POST_MARKET_HOUR = 20
    
    EST = pytz.timezone('US/Eastern')
    
    @classmethod
    def is_market_open(cls):
        """Check if market is currently open"""
        now = datetime.now(cls.EST)
        
        # Regular market hours: 9:30 AM - 4:00 PM, Monday-Friday
        market_open = now.replace(hour=cls.MARKET_OPEN_HOUR, minute=cls.MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = now.replace(hour=cls.MARKET_CLOSE_HOUR, minute=cls.MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        
        is_weekday = now.weekday() < 5  # Monday=0, Friday=4
        
        return is_weekday and market_open <= now <= market_close
    
    @classmethod
    def is_trading_day(cls):
        """Check if today is a trading day (Monday-Friday)"""
        now = datetime.now(cls.EST)
        return now.weekday() < 5
    
    @classmethod
    def time_to_market_open(cls):
        """Get seconds until next market open"""
        now = datetime.now(cls.EST)
        
        market_open = now.replace(hour=cls.MARKET_OPEN_HOUR, minute=cls.MARKET_OPEN_MINUTE, second=0, microsecond=0)
        
        # If already past market open today, check for next day
        if now > market_open:
            # Add 1 day
            market_open += timedelta(days=1)
        
        # If it's weekend, find next Monday
        while market_open.weekday() > 4:
            market_open += timedelta(days=1)
        
        return int((market_open - now).total_seconds())
    
    @classmethod
    def time_to_market_close(cls):
        """Get seconds until market close"""
        now = datetime.now(cls.EST)
        
        market_open = now.replace(hour=cls.MARKET_OPEN_HOUR, minute=cls.MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = now.replace(hour=cls.MARKET_CLOSE_HOUR, minute=cls.MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        
        # If market not open yet, go to tomorrow
        if now < market_open:
            market_close += timedelta(days=1)
        
        # If past market close, go to next day
        if now > market_close:
            market_close += timedelta(days=1)
        
        return int((market_close - now).total_seconds())

# ============================================================================
# PRODUCTION TRADING ENGINE
# ============================================================================

class AutomatedTradingEngine:
    """
    Production trading engine that runs continuously:
    - Waits for market open
    - Trades during market hours
    - Exits gracefully at market close
    - Auto-restarts next business day via systemd/cron
    """
    
    def __init__(self, paper_trading=True):
        self.paper_trading = paper_trading
        self.logger = logger
        self.tickers = TICKERS
        
        # Initialize components
        self.streamer = RealtimeDataStreamer({}, debug=False)
        self.indicator_calc = RealtimeIndicatorCalculator(debug=False)
        self.signal_gen = RealtimeSignalGenerator(debug=False)
        
        # Initialize broker
        try:
            self.broker = AlpacaBrokerInterface(paper_trading=paper_trading, debug=True)
            self.connected = self.broker.connected
        except Exception as e:
            self.logger.error(f"Broker connection failed: {e}")
            self.broker = None
            self.connected = False
        
        if self.connected:
            # Initialize risk manager
            account_info = self.broker.get_account_info()
            self.risk_manager = RiskManager(
                self.broker,
                portfolio_value=account_info['portfolio_value'],
                debug=False
            )
            self.portfolio_monitor = PortfolioMonitor(self.broker, self.risk_manager)
        
        # Session tracking
        self.session_start = None
        self.trades_executed = []
        self.signals_generated = 0
        
        self.logger.info(f"Trading Engine initialized (Broker connected: {self.connected})")
    
    def wait_for_market_open(self):
        """Wait until market opens"""
        
        self.logger.info("Waiting for market open...")
        
        while not MarketHours.is_market_open():
            seconds_until_open = MarketHours.time_to_market_open()
            
            hours = seconds_until_open // 3600
            minutes = (seconds_until_open % 3600) // 60
            
            if seconds_until_open > 3600:
                self.logger.info(f"Market opens in {hours}h {minutes}m - sleeping for 30 minutes")
                time.sleep(30 * 60)  # Sleep 30 minutes at a time
            else:
                self.logger.info(f"Market opens in {minutes} minutes - sleeping for 1 minute")
                time.sleep(1 * 60)
        
        self.logger.info("✓ Market is now OPEN - Starting trading")
    
    def should_continue_trading(self):
        """Check if we should continue trading during market hours"""
        
        # Check if market is still open
        if not MarketHours.is_market_open():
            self.logger.info("⏹️  Market closed - stopping trading session")
            return False
        
        # Check if within 5 minutes of market close
        seconds_to_close = MarketHours.time_to_market_close()
        if seconds_to_close < 300:  # 5 minutes
            self.logger.warning(f"⏹️  Market closing in {seconds_to_close}s - stopping trading")
            return False
        
        return True
    
    def run_continuous(self):
        """
        Main production loop:
        1. Wait for market open
        2. Trade during market hours
        3. Exit at market close
        4. Systemd/cron will restart next day
        """
        
        self.logger.info("="*80)
        self.logger.info("PRODUCTION AUTOMATED TRADING ENGINE (24/7 Mode)")
        self.logger.info("="*80)
        
        if not self.connected:
            self.logger.error("ERROR: Broker not connected. Exiting.")
            sys.exit(1)
        
        try:
            # Wait for market open
            self.wait_for_market_open()
            
            # Start trading session
            self.session_start = datetime.now()
            
            # Get initial state
            initial_account = self.broker.get_account_info()
            self.logger.info(f"Initial Account: Cash=${initial_account['cash']:.2f}, "
                           f"Value=${initial_account['portfolio_value']:.2f}")
            
            # Download baseline data
            self.logger.info("Downloading daily baseline data...")
            self.streamer.download_daily_base(self.tickers)
            self.logger.info(f"✓ Baseline ready for {len(self.tickers)} tickers")
            
            # Main trading loop
            self.logger.info("-" * 80)
            self.logger.info("Starting real-time stream...")
            
            trades_count = {'BUY': 0, 'SELL': 0, 'BLOCKED': 0}
            
            for bar_data in self.streamer.stream_live(
                self.tickers,
                update_interval_seconds=60,
                duration_minutes=10000  # Very long duration (will exit via should_continue_trading)
            ):
                # Check if we should continue
                if not self.should_continue_trading():
                    break
                
                ticker = bar_data['ticker']
                bars = bar_data['bars']
                current_price = bar_data['current_price']
                timestamp = bar_data['timestamp']
                
                try:
                    # Calculate indicators
                    indicators = self.indicator_calc.calculate_all(bars)
                    
                    # Generate signal
                    signal = self.signal_gen.generate_signal(ticker, indicators)
                    self.signals_generated += 1
                    
                    # Execute signal
                    if signal['action'] in ['BUY', 'SELL']:
                        # Risk check
                        risk_allowed, reason = self._check_risk_before_trade(signal, ticker, current_price, indicators)
                        
                        if risk_allowed:
                            # Execute trade
                            executed = self._execute_trade(signal, ticker, current_price)
                            if executed:
                                trades_count[signal['action']] += 1
                                self.trades_executed.append(executed)
                                self.logger.info(f"Trade executed: {signal['action']} {ticker} @ ${current_price:.2f}")
                        else:
                            trades_count['BLOCKED'] += 1
                            self.logger.warning(f"Trade blocked ({ticker}): {reason}")
                    
                    # Monitor positions
                    alerts = self.portfolio_monitor.check_positions()
                    for alert in alerts:
                        self.logger.warning(f"ALERT: {alert['message']}")
                
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    continue
            
            # Session complete
            self.logger.info("-" * 80)
            final_account = self.broker.get_account_info()
            self._log_session_summary(initial_account, final_account, trades_count)
            
        except KeyboardInterrupt:
            self.logger.warning("⚠️  Interrupted by user")
            final_account = self.broker.get_account_info()
            self._log_session_summary(initial_account, final_account, trades_count)
        
        except Exception as e:
            self.logger.error(f"FATAL ERROR: {e}", exc_info=True)
            sys.exit(1)
    
    def _check_risk_before_trade(self, signal, ticker, current_price, indicators):
        """Check risk constraints"""
        
        action = signal['action']
        
        if action == 'BUY':
            qty = self.risk_manager.calculate_position_size(
                ticker, current_price,
                self.broker.account.cash,
                atr=indicators.get('atr', 0)
            )
            allowed, reason = self.risk_manager.can_execute_buy(
                ticker, qty, current_price,
                atr=indicators.get('atr', 0)
            )
        elif action == 'SELL':
            allowed, reason = self.risk_manager.can_execute_sell(ticker, 1)
        else:
            allowed, reason = False, "Invalid action"
        
        return allowed, reason
    
    def _execute_trade(self, signal, ticker, current_price):
        """Execute trade via broker"""
        
        try:
            action = signal['action']
            
            if action == 'BUY':
                qty = int(signal['price'] / current_price) if signal['price'] > 0 else 1
                qty = max(1, int(self.broker.account.cash * 0.02 / current_price))
                
                order = self.broker.place_buy_order(ticker, qty)
                if order:
                    return {
                        'timestamp': datetime.now(),
                        'action': 'BUY',
                        'ticker': ticker,
                        'quantity': qty,
                        'price': current_price,
                        'order_id': order.id,
                    }
            
            elif action == 'SELL':
                position = self.broker.get_position(ticker)
                if position:
                    qty = int(position.qty)
                    order = self.broker.place_sell_order(ticker, qty)
                    if order:
                        return {
                            'timestamp': datetime.now(),
                            'action': 'SELL',
                            'ticker': ticker,
                            'quantity': qty,
                            'price': current_price,
                            'order_id': order.id,
                        }
        
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
        
        return None
    
    def _log_session_summary(self, initial_account, final_account, trades_count):
        """Log session summary"""
        
        elapsed = datetime.now() - self.session_start
        pnl = final_account['portfolio_value'] - initial_account['portfolio_value']
        pnl_pct = (pnl / initial_account['portfolio_value']) * 100
        
        self.logger.info("="*80)
        self.logger.info("SESSION SUMMARY")
        self.logger.info("="*80)
        self.logger.info(f"Duration: {elapsed.total_seconds()/60:.1f} minutes")
        self.logger.info(f"Signals: {self.signals_generated}")
        self.logger.info(f"Trades: BUY={trades_count['BUY']}, SELL={trades_count['SELL']}, BLOCKED={trades_count['BLOCKED']}")
        self.logger.info(f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        self.logger.info(f"Final Portfolio: ${final_account['portfolio_value']:.2f}")
        self.logger.info("="*80)

def main():
    """Main entry point"""
    
    # Determine trading mode (paper or live)
    paper_trading = os.getenv('TRADING_MODE', 'paper').lower() == 'paper'
    
    if not paper_trading:
        logger.warning("⚠️⚠️⚠️ LIVE TRADING MODE ENABLED ⚠️⚠️⚠️")
        logger.warning("Real money will be used!")
        time.sleep(3)
    else:
        logger.info("Running in PAPER TRADING mode (safe)")
    
    # Create and run engine
    engine = AutomatedTradingEngine(paper_trading=paper_trading)
    engine.run_continuous()

if __name__ == "__main__":
    main()
