"""
config.py — Single source of truth for all parameters
Central configuration for the 7-indicator trading signal system
"""

# === UNIVERSE ===
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]  # Paper trade candidates
BENCHMARK = "VOO"
START_DATE = "2020-01-01"
END_DATE = "2025-01-01"
INTERVAL = "1d"  # daily bars

# === PHASE 1: DATA ===
DATA_CACHE_DIR = "phase1_data/cache"
MIN_BARS_REQUIRED = 252  # 1 trading year minimum

# === PHASE 2: INDICATOR PARAMETERS ===
EMA_FAST = 50
EMA_SLOW = 200
RSI_PERIOD = 14
RSI_LOW = 45
RSI_HIGH = 65
VOLUME_LOOKBACK = 20       # bars for volume average
VOLUME_THRESHOLD = 0.80    # current vol must be > 80% of avg
ATR_PERIOD = 14
ATR_LOOKBACK = 30          # bars for ATR average
FIB_LEVELS = [0.382, 0.5, 0.618]   # valid pullback zones
REGRESSION_LOOKBACK = 50   # bars for linear regression

# === PHASE 3: BACKTEST RULES ===
MIN_SIGNALS_TO_BUY = 5     # out of 7 (change to 4 to test 4/7)
MANDATORY_SIGNALS = ["elliott_wave", "fibonacci"]  # MUST be True for any trade
HOLDING_PERIOD_MAX = 20    # max bars to hold if no exit signal
STOP_LOSS_PCT = 0.07       # 7% stop loss
TAKE_PROFIT_PCT = 0.15     # 15% take profit

# === PHASE 6: PAPER TRADE ===
PAPER_CAPITAL = 10_000     # starting paper capital
MAX_POSITIONS = 5
POSITION_SIZE_PCT = 0.20   # 20% per position
VOO_OUTPERFORM_TARGET = 0.05  # beat VOO by 5% to scale up
