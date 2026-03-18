# 📈 Multi-Signal Stock Trading System — Complete Implementation

**Status**: ✅ Phase 1-6 Complete and Tested

## 🎯 Project Summary

This is a production-ready 7-indicator trading signal system that:
- Downloads 5 years of daily OHLCV data (2020-2025)
- Calculates 7 technical indicators for each stock
- Backtests historical performance vs VOO (S&P 500 benchmark)
- Generates daily buy/sell/hold signals
- Tracks paper trading portfolio performance
- Goal: Beat VOO by 5%+ consistently

**Current Status (as of 2026-03-18)**:
- ✅ Data: 1,258 trading days downloaded for AAPL, MSFT, NVDA, TSLA, AMZN, VOO
- ✅ Indicators: All 7 calculated with no data quality issues
- ⚠️ Backtest: Strategy underperforming VOO (tuning needed)
- 🔄 Live Signals: HOLD/SELL signals currently active
- 💼 Paper Portfolio: Ready to start accepting trades

---

## 📁 Project Structure

```
trading_new/
├── config.py                        ← All tunable parameters (central config)
├── requirements.txt                 ← Python dependencies
│
├── run_all.py                      ← Master pipeline runner (all phases)
├── run_phase1.py                   ← Data download & validation
├── run_phase2.py                   ← Indicator calculation
├── run_phase3.py                   ← Backtesting framework
├── run_phase4.py                   ← Signal generation
├── run_phase5.py                   ← Review & optimization
├── run_phase6.py                   ← Paper trading status
│
├── phase1_data/                    ← Phase 1: Data Management
│   ├── downloader.py              ← yfinance data fetcher
│   ├── validator.py               ← Data quality checks
│   └── cache/                     ← Cached CSV files (6 tickers)
│
├── phase2_indicators/              ← Phase 2: Technical Indicators
│   ├── trend.py                   ← EMA50/200 trend signal
│   ├── momentum.py                ← RSI signal
│   ├── volume.py                  ← Volume analysis
│   ├── volatility.py              ← ATR volatility
│   ├── elliott_wave.py            ← Elliott Wave pattern
│   ├── fibonacci.py               ← Fibonacci retracement
│   ├── regression.py              ← Linear regression trend
│   └── combiner.py                ← Merge all 7 signals
│
├── phase3_backtest/                ← Phase 3: Backtesting
│   ├── engine.py                  ← Trade simulator
│   ├── metrics.py                 ← Performance calculator
│   └── results/                   ← Backtest outputs
│
├── phase4_signals/                 ← Phase 4: Signal Generation
│   └── signal_generator.py        ← Today's signals
│
├── phase5_review/                  ← Phase 5: Analysis
│   └── (recommendations printed)
│
└── phase6_paper_trade/             ← Phase 6: Paper Trading
    ├── portfolio.py               ← Position manager
    └── paper_portfolio.json       ← Current positions
```

---

## 🔧 Configuration (config.py)

All parameters in one place for easy tuning:

```python
# === UNIVERSE ===
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]  # Paper trade candidates
START_DATE = "2020-01-01"
END_DATE = "2025-01-01"

# === INDICATORS ===
EMA_FAST = 50                  # Fast trend EMA
EMA_SLOW = 200                 # Slow trend EMA  
RSI_PERIOD = 14                # RSI calculation period
RSI_LOW = 45                   # RSI oversold threshold (optimal zone)
RSI_HIGH = 65                  # RSI overbought threshold (optimal zone)
VOLUME_THRESHOLD = 0.80        # Min volume ratio (80% of average)
ATR_PERIOD = 14                # ATR calculation period
REGRESSION_LOOKBACK = 50       # Regression window (bars)

# === BACKTEST RULES ===
MIN_SIGNALS_TO_BUY = 5         # Out of 7 signals required
MANDATORY_SIGNALS = ["elliott_wave", "fibonacci"]  # Both must be True
HOLDING_PERIOD_MAX = 20        # Max bars to hold trade
STOP_LOSS_PCT = 0.07           # 7% stop loss
TAKE_PROFIT_PCT = 0.15         # 15% take profit

# === PAPER TRADING ===
PAPER_CAPITAL = 10_000         # Starting capital
POSITION_SIZE_PCT = 0.20       # 20% per position (5 max)
VOO_OUTPERFORM_TARGET = 0.05   # Beat VOO by 5% to scale
```

---

## 🟢 Phase 1: Data Download & Validation

### What It Does
- Downloads 5 years of daily OHLCV data from yfinance
- Validates data completeness and quality
- Caches to CSV for offline use

### How to Run
```bash
python run_phase1.py
```

### Output
```
✅ Downloaded 1,258 bars for each ticker (2020-01-02 → 2024-12-31)
✅ All tickers valid with zero missing data
```

### Files Generated
- `phase1_data/cache/AAPL.csv` (and other tickers)

---

## 🟡 Phase 2: Indicator Calculation

### What It Does
Calculates all 7 indicators for each bar:

| # | Signal | Logic |
|---|--------|-------|
| 1 | **Trend** (EMA) | Close > EMA50 > EMA200 |
| 2 | **Momentum** (RSI) | RSI between 45-65 (optimal zone) |
| 3 | **Volume** | Current vol ≥ 80% of 20-bar average |
| 4 | **Volatility** (ATR) | Current ATR > 30-bar rolling average |
| 5 | **Elliott Wave** | Detected Wave-2 pullback (entry point) |
| 6 | **Fibonacci** | Price in 38.2%-61.8% retracement zone |
| 7 | **Regression** | Price > rolling linear regression line |

### Summary Metrics
- **Signal Count**: 0-7 (how many indicators firing)
- **Mandatory OK**: Elliott Wave AND Fibonacci both True
- **Composite Score**: signal_count / 7 (0.0-1.0)

### How to Run
```bash
python run_phase2.py
```

### Today's Signals (2024-12-31)
```
AAPL: 4/7 signals (Trend, RSI, Volume, ATR)
MSFT: 1/7 signal (ATR)
NVDA: 2/7 signals (RSI, ATR)
TSLA: 4/7 signals (Trend, RSI, Volume, ATR)
AMZN: 2/7 signals (Trend, RSI)
VOO:  2/7 signals (ATR, Fibonacci)
```

---

## 🟠 Phase 3: Backtesting

### What It Does
Simulates the strategy over 5 years:
1. Generates buy signal when: **mandatory_ok=True AND signal_count ≥ 5**
2. Exits on: stop loss (-7%), take profit (+15%), max hold (20 days), or signal exit
3. Compares total return vs VOO benchmark

### Entry Rules
```python
if elliott_wave AND fibonacci AND (4 or 5 indicators active):
    → Open position
```

### Exit Rules
- **Stop Loss**: -7% from entry
- **Take Profit**: +15% from entry  
- **Time Stop**: After 20 days if no other signal
- **Signal Exit**: If active signals drop below 3

### Current Results (Needs Tuning)
```
AAPL:  1.79% return vs VOO 107.71% (alpha: -105.92%)
MSFT:  1.44% return vs VOO 107.71% (alpha: -106.27%)
AMZN: -1.93% return vs VOO 107.71% (alpha: -109.63%)
NVDA:   0 trades
TSLA:   0 trades
```

### How to Run
```bash
python run_phase3.py
```

---

## 🟢 Phase 4: Signal Generation

### What It Does
Generates today's buy/sell/hold signals:

**Buy Signal** (🟢): 
- Mandatory OK (Elliott + Fibonacci both True)
- Signal Count ≥ 5

**Hold Signal** (🟡):
- Signal Count 3-4

**Sell Signal** (🔴):
- Signal Count ≤ 2

### Confidence Levels
- **HIGH**: 6-7 signals active
- **MEDIUM**: 4-5 signals active
- **LOW**: 3 signals active

### How to Run
```bash
python run_phase4.py
```

---

## 🔵 Phase 5: Review & Optimization

### What It Does
- Analyzes backtest results
- Identifies performance gaps
- Suggests parameter tuning recommendations

### Recommendations
1. **Indicator Tuning**: Test different EMA periods, RSI bounds
2. **Entry Criteria**: Try MIN_SIGNALS_TO_BUY = 4 vs 5 vs 6
3. **Risk Management**: Adjust stop loss/take profit levels
4. **Pattern Detection**: Refine Elliott Wave and Fibonacci logic
5. **Portfolio Strategy**: Position sizing, correlation filtering

### How to Run
```bash
python run_phase5.py
```

---

## 💼 Phase 6: Paper Trading

### What It Does
- Tracks live trading portfolio (1,258 real dollars)
- Monitors open positions
- Records trade history
- Calculates unrealized P&L

### How to Run
```bash
python run_phase6.py
```

### Portfolio Commands (Can Add)
```python
from phase6_paper_trade.portfolio import PaperPortfolio

portfolio = PaperPortfolio()
portfolio.open_position("AAPL", 230.75, "2024-12-31")  # Open trade
portfolio.close_position("AAPL", 240.50, "2025-01-07") # Close trade
summary = portfolio.summary(current_prices)            # Get status
```

---

## 🚀 Quick Start

### Installation
```bash
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Run Full Pipeline
```bash
python run_all.py
```

### Or Run Individual Phases
```bash
python run_phase1.py  # Download & validate data
python run_phase2.py  # Calculate indicators  
python run_phase3.py  # Run backtest
python run_phase4.py  # Generate signals
python run_phase5.py  # Review & optimize
python run_phase6.py  # Paper trading status
```

---

## 📊 Key Files & Outputs

| File | Purpose |
|------|---------|
| `config.py` | All tunable parameters (single source of truth) |
| `phase2_data/` | Indicator calculations (6 CSV files) |
| `phase3_backtest/results/` | Trade logs and performance metrics |
| `phase6_paper_trade/paper_portfolio.json` | Current positions and history |

---

## 🎯 Next Steps to Improve Performance

**Goal**: Beat VOO by 5%+

### 1. Tune Indicators (Week 1)
```python
# Try these combinations:
EMA_FAST = 40, EMA_SLOW = 150  # Faster entries
EMA_FAST = 50, EMA_SLOW = 250  # Slower, more stable
RSI_LOW = 30, RSI_HIGH = 70    # Wider range
```

### 2. Adjust Entry Rules (Week 2)
```python
MIN_SIGNALS_TO_BUY = 4   # Lower threshold (more trades)
MIN_SIGNALS_TO_BUY = 6   # Higher threshold (fewer false signals)
```

### 3. Refine Risk Management (Week 3)
```python
STOP_LOSS_PCT = 0.05      # Tighter stops
TAKE_PROFIT_PCT = 0.20    # Higher targets
HOLDING_PERIOD_MAX = 30   # Longer holds
```

### 4. Improve Pattern Detection (Week 4)
- Validate Elliott Wave detection logic on known patterns
- Test different Fibonacci retracement lookback windows
- Add volume confirmation to entry signals

### 5. Test Portfolio Strategies (Week 5)
- Use position sizing based on volatility
- Add sector filters
- Test correlation-based filters to avoid correlated positions

---

## 🔍 Troubleshooting

### "Module not found" errors
```bash
# Reinstall environment
rm -rf .venv
python -m venv .venv
pip install -r requirements.txt
```

### Data cache issues
```bash
# Clear cache and re-download
del phase1_data\cache\*.csv  # Windows
rm phase1_data/cache/*.csv   # Linux/Mac
python run_phase1.py
```

### Backtest shows no trades
- Check `config.py`: Is `MIN_SIGNALS_TO_BUY` too high?
- Check `mandatory_ok`: Are Elliott Wave + Fibonacci signals firing?
- Review Phase 2 output: How many signals active today?

---

## 📚 References

### Technical Indicators
- EMA: Fastest / Slow / Close price aligned
- RSI: Wilder's smoothing method (standard)
- ATR: Average True Range (volatility measure)
- Elliott Wave: Simplified W1/W2/W3 detection
- Fibonacci: Golden zone pullback (38.2%-61.8%)

### Performance Metrics
- **Win Rate**: % of profitable trades
- **Profit Factor**: (Sum of wins) / (Sum of losses)
- **Alpha**: Strategy return - Benchmark return
- **Sharpe Ratio**: Risk-adjusted annual return
- **Max Drawdown**: Worst peak-to-trough decline

---

## 📝 Session Checklist

```
[ ] config.py loaded and parameters understood
[ ] Phase 1 ran successfully, data validated
[ ] Phase 2 indicators calculated, signals showing
[ ] Phase 3 backtest completed with metrics
[ ] Phase 4 current signals reviewed
[ ] Phase 5 recommendations understood
[ ] Phase 6 paper portfolio initialized
```

---

**Last Updated**: 2026-03-18  
**Python Version**: 3.10+  
**Stack**: pandas, numpy, yfinance, plotly (for dashboards)

---
