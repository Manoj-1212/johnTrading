"""
Trading Configuration - Supports Both Daily (Phases 1-6) and Intraday (Phases 7-9)
"""

import os
from pathlib import Path

# ============================================================================
# TICKERS & PORTFOLIO
# ============================================================================

# 21-ticker universe for diversification (CUDA->GE, BRK.B->V, +PLTR)
TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',  # Tech / Mega-cap
    'JPM', 'JNJ', 'XOM', 'WMT', 'PG',         # Blue chip
    'META', 'TSLA', 'GE', 'AMD', 'INTC',      # Growth / Semiconductors
    'BA', 'GS', 'V', 'NFLX', 'ADBE', 'PLTR'   # Diversified
]

PAPER_CAPITAL = 10000  # Starting paper trading capital

# ============================================================================
# PHASE 1-6: DAILY BATCH TRADING (Original System)
# ============================================================================

# Historical data settings
START_DATE = '2023-01-01'
END_DATE = None  # None = today
LOOKBACK = 250   # Trading days of historical data for backtesting

# Indicator settings
FAST_MA_PERIOD = 50
SLOW_MA_PERIOD = 200
RSI_PERIOD = 14
ATR_PERIOD = 14
BBands_PERIOD = 20
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Trading rules (Phases 1-6)
STOP_LOSS_PERCENT = 1.5    # Close if -1.5%
TAKE_PROFIT_PERCENT = 2.0  # Close if +2%
MIN_VOLUME = 1000000       # Minimum daily volume

# ============================================================================
# PHASE 7-9: REAL-TIME INTRADAY TRADING (New System)
# ============================================================================

# Market Hours (US Eastern Time)
MARKET_OPEN = "09:30"      # 9:30 AM EST
MARKET_CLOSE = "16:00"     # 4:00 PM EST
MARKET_TIMEZONE = "US/Eastern"

# Data Streaming Settings
INTRADAY_INTERVAL = "1m"   # 1-minute bars for real-time trading
ROLLING_WINDOW = 200       # Bars needed for all indicators (200 min = 3.3 hours)
STREAM_UPDATE_INTERVAL = 60  # Seconds between bar checks

# Real-Time Indicator Settings (same formulas, calculated on 1-min bars)
EMA_FAST = 50   # Fast exponential moving average
EMA_SLOW = 200  # Slow exponential moving average
RSI_FAST = 14   # Relative strength index
MACD_FAST_MA = 12
MACD_SLOW_MA = 26
MACD_SIGNAL_MA = 9

# ============================================================================
# PHASE 9: RISK MANAGEMENT (Critical for Real-Time Trading)
# ============================================================================

# Position Sizing & Limits
MAX_POSITION_SIZE_PCT = 0.05           # Max 5% of portfolio per position
RISK_PER_TRADE_PCT = 0.02             # Risk 2% per trade
ATR_MULTIPLIER = 2                    # Risk 2 x ATR per position

# Daily Loss Control
DAILY_LOSS_LIMIT_PCT = 0.02           # Stop trading if loss > 2% daily
DAILY_LOSS_LIMIT_DOLLAR = 200         # Or stop if loss > $200

# Volatility Control
MAX_VIX_FOR_TRADING = 50              # Don't trade if VIX > 50
VIX_CHECK_INTERVAL = 300              # Check VIX every 5 minutes

# Sector Limits
MAX_SECTOR_CONCENTRATION_PCT = 0.30   # Max 30% in one sector

# Stop Loss & Take Profit
STOP_LOSS_PCT = 1.5                   # Exit if -1.5%
TAKE_PROFIT_PCT = 2.0                 # Exit if +2%

# Position Limits
MAX_CONCURRENT_POSITIONS = 10         # Max 10 open positions
MIN_SHARES_PER_TRADE = 1             # Minimum 1 share

# ============================================================================
# PHASE 8: BROKER CONFIGURATION (Alpaca)
# ============================================================================

# Alpaca API Settings (from environment variables)
ALPACA_API_KEY = os.getenv('APCA_API_KEY_ID', '')
ALPACA_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY', '')
ALPACA_BASE_URL = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

# Paper Trading (Safe Testing)
# ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper (testing)
# Live Trading (REAL MONEY - USE WITH CAUTION)
# ALPACA_BASE_URL = "https://api.alpaca.markets"        # Live (real money)

ALPACA_PAPER_TRADING = True  # Set to False for LIVE TRADING

# Order Settings
DEFAULT_ORDER_TYPE = "market"     # market, limit, stop, trailing_stop
ORDER_TIME_IN_FORCE = "day"      # DAY orders (closed at market close)
ENABLE_TRAILING_STOP = False      # Use trailing stops (advanced)

# ============================================================================
# DIRECTORIES & LOGGING
# ============================================================================

# Base directory
BASE_DIR = Path(__file__).parent

# Daily batch output (Phases 1-6)
DATA_DIR = BASE_DIR / 'data'
BACKTEST_RESULTS_DIR = BASE_DIR / 'backtest_results'
SIGNALS_DIR = BASE_DIR / 'phase6_paper_trade'
PORTFOLIO_FILE = SIGNALS_DIR / 'paper_portfolio.json'

# Real-time intraday output (Phases 7-9)
PHASE7_CACHE_DIR = BASE_DIR / 'phase7_realtime_streaming' / 'data_cache'
PHASE7_SIGNALS_DIR = BASE_DIR / 'phase7_realtime_streaming' / 'realtime_signals'
PHASE7_LOGS_DIR = BASE_DIR / 'phase7_realtime_streaming' / 'logs'

PHASE8_TRADES_DIR = BASE_DIR / 'phase8_execution' / 'trades'
PHASE8_LOGS_DIR = BASE_DIR / 'phase8_execution' / 'logs'

PHASE9_TRADES_DIR = BASE_DIR / 'phase9_production_trading' / 'trades'
PHASE9_LOGS_DIR = BASE_DIR / 'phase9_production_trading' / 'logs'

# ============================================================================
# SIGNAL CONFIDENCE & THRESHOLDS
# ============================================================================

# Confidence levels
SIGNAL_CONFIDENCE_LEVELS = {
    'HIGH': 4,    # 4+ indicators agree
    'MEDIUM': 3,  # 3 indicators agree
    'LOW': 2      # 2 or fewer indicators agree
}

# Minimum confidence to trade
MIN_CONFIDENCE_TO_TRADE = 'MEDIUM'  # Require MEDIUM or HIGH confidence

# Signal strength (number of indicators agreeing)
MIN_SIGNAL_STRENGTH = 2

# ============================================================================
# DASHBOARD SETTINGS (Streamlit)
# ============================================================================

DASHBOARD_REFRESH_INTERVAL = 5  # Seconds between dashboard refreshes
DASHBOARD_PORT = 8501
DASHBOARD_HOST = "0.0.0.0"

# ============================================================================
# MODE SELECTION
# ============================================================================

# Choose operation mode
# 'daily' - Run Phases 1-6 once per day at market close
# 'intraday' - Run Phases 7-9 during market hours with real-time updates
TRADING_MODE = 'intraday'  # Change to 'daily' to use old system

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_trading_mode():
    """Get current trading mode"""
    return TRADING_MODE

def is_daily_mode():
    """Check if running in daily batch mode (Phases 1-6)"""
    return TRADING_MODE == 'daily'

def is_intraday_mode():
    """Check if running in real-time intraday mode (Phases 7-9)"""
    return TRADING_MODE == 'intraday'

def get_config_summary():
    """Print configuration summary"""
    print("\n" + "="*60)
    print("TRADING SYSTEM CONFIGURATION")
    print("="*60)
    print(f"Mode: {TRADING_MODE.upper()}")
    print(f"Tickers: {len(TICKERS)} stocks")
    print(f"Capital: ${PAPER_CAPITAL:,}")
    
    if is_daily_mode():
        print(f"Data Period: {START_DATE} to {END_DATE or 'Today'}")
        print(f"Lookback: {LOOKBACK} days")
        print(f"Execution: Once per day at market close (4 PM EST)")
    else:
        print(f"Market Hours: {MARKET_OPEN} - {MARKET_CLOSE} EST")
        print(f"Bar Interval: {INTRADAY_INTERVAL}")
        print(f"Update Interval: {STREAM_UPDATE_INTERVAL}s")
        print(f"Rolling Window: {ROLLING_WINDOW} bars ({ROLLING_WINDOW/60:.1f} hours)")
    
    print(f"\nRisk Controls:")
    print(f"  Max Position: {MAX_POSITION_SIZE_PCT:.0%}")
    print(f"  Daily Loss Limit: {DAILY_LOSS_LIMIT_PCT:.0%}")
    print(f"  Max VIX for Trading: {MAX_VIX_FOR_TRADING}")
    print(f"  Stop Loss: {STOP_LOSS_PCT:.1f}%")
    print(f"  Take Profit: {TAKE_PROFIT_PCT:.1f}%")
    
    print(f"\nBroker: Alpaca ({'Paper' if ALPACA_PAPER_TRADING else 'LIVE'})")
    print("="*60 + "\n")

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    get_config_summary()
    
    print("Quick Test:")
    print(f"  Daily Mode: {is_daily_mode()}")
    print(f"  Intraday Mode: {is_intraday_mode()}")
    print(f"  First Ticker: {TICKERS[0]}")
    print(f"  Portfolio Directory: {PORTFOLIO_FILE.parent}")
