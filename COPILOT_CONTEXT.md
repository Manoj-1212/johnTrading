# 📈 Multi-Signal Stock Trading System — Full Project Context

> **For use with GitHub Copilot + Claude Sonnet**
> Paste this file into your Copilot Chat or Claude session at the start of every work session.
> This is the single source of truth for architecture, rules, and progress.

---

## 🏗️ Project Overview

Build a **7-indicator trading signal system** that backtests 2020–2025, generates buy/sell signals, and paper trades 3–5 stocks. The goal: beat VOO (S&P 500 ETF) by 5%+ consistently.

**Stack:** Python 3.11+, pandas, numpy, yfinance, ta-lib (or `ta` library), plotly, streamlit  
**AI Tools:** GitHub Copilot (code generation), Claude Sonnet (architecture + logic review)

---

## 📁 Project Structure

```
trading_system/
├── COPILOT_CONTEXT.md          ← This file (paste into every session)
├── requirements.txt
├── config.py                   ← All tunable parameters in one place
├── phase1_data/
│   ├── downloader.py           ← Stock data download (yfinance)
│   ├── validator.py            ← Data quality checks
│   └── cache/                  ← Cached CSV files (gitignored)
├── phase2_indicators/
│   ├── trend.py                ← EMA50, EMA200 trend alignment
│   ├── momentum.py             ← RSI calculation
│   ├── volume.py               ← Volume vs 20-bar average
│   ├── volatility.py           ← ATR vs 30-bar average
│   ├── elliott_wave.py         ← Wave-3 pattern detection
│   ├── fibonacci.py            ← Fibonacci pullback zones
│   ├── regression.py           ← Linear regression trend line
│   └── combiner.py             ← Merge all signals into one DataFrame
├── phase3_backtest/
│   ├── engine.py               ← Backtest loop (2020–2025)
│   ├── rules.py                ← Signal combination rules (4/7, 5/7)
│   └── metrics.py              ← Win rate, avg return, max drawdown
├── phase4_signals/
│   ├── signal_generator.py     ← Live buy/sell signal output
│   └── alert.py                ← Console/email alert (optional)
├── phase5_review/
│   ├── reporter.py             ← Performance report vs VOO
│   └── optimizer.py            ← Rule adjustment suggestions
├── phase6_paper_trade/
│   ├── portfolio.py            ← Track 3–5 stock paper positions
│   ├── weekly_review.py        ← Weekly P&L summary
│   └── scale_check.py          ← Flag when beating VOO by 5%+
├── dashboard/
│   └── app.py                  ← Streamlit dashboard (all phases)
└── tests/
    ├── test_indicators.py
    ├── test_backtest.py
    └── test_signals.py
```

---

## ⚙️ config.py — All Tunable Parameters

```python
# config.py — Single source of truth for all parameters

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
```

---

## 🔴 PHASE 1 — Data Download & Validation

### Goal
Download OHLCV data for all tickers + VOO benchmark. Validate completeness before proceeding.

### Implementation: `phase1_data/downloader.py`

```python
"""
COPILOT PROMPT:
Write a StockDownloader class that:
1. Downloads OHLCV data using yfinance for a list of tickers
2. Saves each ticker to CSV in DATA_CACHE_DIR
3. Returns a dict {ticker: pd.DataFrame}
4. Handles missing data, delisted stocks gracefully
5. Has a load_from_cache() method to avoid re-downloading
"""

import yfinance as yf
import pandas as pd
import os
from config import (TICKERS, BENCHMARK, START_DATE, END_DATE,
                    INTERVAL, DATA_CACHE_DIR, MIN_BARS_REQUIRED)

class StockDownloader:
    def __init__(self):
        os.makedirs(DATA_CACHE_DIR, exist_ok=True)
        self.data: dict[str, pd.DataFrame] = {}

    def download_all(self, force_refresh: bool = False) -> dict[str, pd.DataFrame]:
        """Download all tickers + benchmark. Returns {ticker: df}."""
        all_tickers = TICKERS + [BENCHMARK]
        for ticker in all_tickers:
            self.data[ticker] = self._download_one(ticker, force_refresh)
        return self.data

    def _download_one(self, ticker: str, force_refresh: bool) -> pd.DataFrame:
        cache_path = f"{DATA_CACHE_DIR}/{ticker}.csv"
        if not force_refresh and os.path.exists(cache_path):
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            print(f"[CACHE] {ticker}: {len(df)} bars loaded")
            return df
        try:
            df = yf.download(ticker, start=START_DATE, end=END_DATE,
                             interval=INTERVAL, auto_adjust=True, progress=False)
            df.to_csv(cache_path)
            print(f"[DOWNLOAD] {ticker}: {len(df)} bars saved")
            return df
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")
            return pd.DataFrame()

    def load_from_cache(self) -> dict[str, pd.DataFrame]:
        """Load all cached CSVs without downloading."""
        all_tickers = TICKERS + [BENCHMARK]
        for ticker in all_tickers:
            cache_path = f"{DATA_CACHE_DIR}/{ticker}.csv"
            if os.path.exists(cache_path):
                self.data[ticker] = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return self.data
```

### Implementation: `phase1_data/validator.py`

```python
"""
COPILOT PROMPT:
Write a DataValidator class that checks:
1. Each ticker has >= MIN_BARS_REQUIRED rows
2. No more than 5 consecutive NaN values in Close column
3. Date range covers START_DATE to END_DATE
4. Prints a validation report table (ticker | bars | missing | status)
5. Returns list of valid tickers only
"""

import pandas as pd
from config import MIN_BARS_REQUIRED, START_DATE, END_DATE

class DataValidator:
    def validate(self, data: dict[str, pd.DataFrame]) -> list[str]:
        valid = []
        print(f"\n{'='*60}")
        print(f"{'TICKER':<10} {'BARS':>6} {'MISSING':>8} {'DATE_RANGE':<25} {'STATUS'}")
        print(f"{'='*60}")
        for ticker, df in data.items():
            if df.empty:
                self._print_row(ticker, 0, 0, "N/A", "❌ EMPTY")
                continue
            bars = len(df)
            missing = df['Close'].isna().sum()
            max_consec_nan = self._max_consecutive_nan(df['Close'])
            date_range = f"{df.index[0].date()} → {df.index[-1].date()}"
            if bars >= MIN_BARS_REQUIRED and max_consec_nan <= 5:
                status = "✅ VALID"
                valid.append(ticker)
            else:
                status = f"❌ FAIL (bars={bars}, consec_nan={max_consec_nan})"
            self._print_row(ticker, bars, missing, date_range, status)
        print(f"{'='*60}")
        print(f"\n✅ Valid tickers ({len(valid)}): {valid}\n")
        return valid

    def _max_consecutive_nan(self, series: pd.Series) -> int:
        max_c, count = 0, 0
        for v in series:
            count = count + 1 if pd.isna(v) else 0
            max_c = max(max_c, count)
        return max_c

    def _print_row(self, ticker, bars, missing, date_range, status):
        print(f"{ticker:<10} {bars:>6} {missing:>8} {str(date_range):<25} {status}")
```

### Phase 1 Runner: `run_phase1.py`

```python
from phase1_data.downloader import StockDownloader
from phase1_data.validator import DataValidator

if __name__ == "__main__":
    print("=== PHASE 1: DATA DOWNLOAD & VALIDATION ===")
    dl = StockDownloader()
    data = dl.download_all(force_refresh=False)

    validator = DataValidator()
    valid_tickers = validator.validate(data)

    if len(valid_tickers) < 2:
        print("❌ Not enough valid data. Fix before proceeding to Phase 2.")
    else:
        print("✅ Phase 1 complete. Proceed to Phase 2.")
```

---

## 🟡 PHASE 2 — Calculate All 7 Indicators

### Indicator 1: Trend EMA (`phase2_indicators/trend.py`)

```python
"""
COPILOT PROMPT:
Add columns to df: EMA50, EMA200, trend_signal (bool).
trend_signal = True when: Close > EMA50 AND EMA50 > EMA200
Use pandas ewm(span=N, adjust=False).mean() — no external libraries needed.
"""

import pandas as pd
from config import EMA_FAST, EMA_SLOW

def add_trend_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[f'EMA{EMA_FAST}'] = df['Close'].ewm(span=EMA_FAST, adjust=False).mean()
    df[f'EMA{EMA_SLOW}'] = df['Close'].ewm(span=EMA_SLOW, adjust=False).mean()
    df['trend_signal'] = (
        (df['Close'] > df[f'EMA{EMA_FAST}']) &
        (df[f'EMA{EMA_FAST}'] > df[f'EMA{EMA_SLOW}'])
    )
    return df
```

### Indicator 2: RSI (`phase2_indicators/momentum.py`)

```python
"""
COPILOT PROMPT:
Calculate RSI(14) using Wilder's smoothing method (not simple EMA).
Add column: rsi_signal = True when RSI is between RSI_LOW and RSI_HIGH.
Also store the raw RSI value as column 'RSI'.
"""

import pandas as pd
import numpy as np
from config import RSI_PERIOD, RSI_LOW, RSI_HIGH

def add_rsi_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['rsi_signal'] = df['RSI'].between(RSI_LOW, RSI_HIGH)
    return df
```

### Indicator 3: Volume (`phase2_indicators/volume.py`)

```python
"""
COPILOT PROMPT:
Calculate 20-bar simple moving average of Volume.
Add: volume_avg_20, volume_ratio (current/avg), volume_signal = True when ratio >= VOLUME_THRESHOLD.
"""

import pandas as pd
from config import VOLUME_LOOKBACK, VOLUME_THRESHOLD

def add_volume_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['volume_avg_20'] = df['Volume'].rolling(VOLUME_LOOKBACK).mean()
    df['volume_ratio'] = df['Volume'] / df['volume_avg_20']
    df['volume_signal'] = df['volume_ratio'] >= VOLUME_THRESHOLD
    return df
```

### Indicator 4: ATR (`phase2_indicators/volatility.py`)

```python
"""
COPILOT PROMPT:
Calculate ATR(14) using Wilder's method:
  True Range = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))
  ATR = Wilder smoothed TR over ATR_PERIOD
Then calculate ATR rolling average over ATR_LOOKBACK bars.
atr_signal = True when current ATR > ATR rolling average.
"""

import pandas as pd
import numpy as np
from config import ATR_PERIOD, ATR_LOOKBACK

def add_atr_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    high, low, close = df['High'], df['Low'], df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(alpha=1/ATR_PERIOD, adjust=False).mean()
    df['ATR_avg'] = df['ATR'].rolling(ATR_LOOKBACK).mean()
    df['atr_signal'] = df['ATR'] > df['ATR_avg']
    return df
```

### Indicator 5: Elliott Wave (`phase2_indicators/elliott_wave.py`)

```python
"""
COPILOT PROMPT:
Detect Wave-3 Elliott Wave pattern (simplified rule-based approach):

Rules for Wave-3 detection (on daily closes):
1. Identify Wave-1: First significant swing up (local min → local max, using 10-bar pivot)
2. Identify Wave-2: Pullback that retraces 38.2%–61.8% of Wave-1 (Fibonacci)
3. Wave-3 start: Price breaks above Wave-1 high with strong volume
4. Wave-3 signal = True when: 
   - We are in a confirmed Wave-2 pullback (price above Wave-1 low)
   - Price has NOT yet broken above Wave-1 high (we're at the entry point)
   - RSI was oversold during Wave-2 (< 50 at pullback low)

Use a rolling 50-bar window to identify wave structure.
Add column: elliott_wave_signal (bool), wave_label (str: 'W1','W2','W3','NA')
"""

import pandas as pd
import numpy as np

def find_pivots(series: pd.Series, window: int = 10) -> tuple[pd.Series, pd.Series]:
    """Find local highs and lows using rolling window."""
    local_max = series[(series == series.rolling(window, center=True).max())]
    local_min = series[(series == series.rolling(window, center=True).min())]
    return local_max, local_min

def add_elliott_wave_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['elliott_wave_signal'] = False
    df['wave_label'] = 'NA'

    close = df['Close'].values
    n = len(close)
    window = 10

    for i in range(60, n):
        segment = df.iloc[max(0, i-60):i]
        seg_close = segment['Close']

        # Find pivots in the segment
        local_max_idx = []
        local_min_idx = []
        for j in range(window, len(seg_close) - window):
            if seg_close.iloc[j] == seg_close.iloc[j-window:j+window].max():
                local_max_idx.append(j)
            if seg_close.iloc[j] == seg_close.iloc[j-window:j+window].min():
                local_min_idx.append(j)

        if len(local_max_idx) < 1 or len(local_min_idx) < 2:
            continue

        # Wave 1: swing low → swing high
        w1_low_i = local_min_idx[0]
        w1_high_i = next((x for x in local_max_idx if x > w1_low_i), None)
        if w1_high_i is None:
            continue

        w1_low = seg_close.iloc[w1_low_i]
        w1_high = seg_close.iloc[w1_high_i]
        w1_size = w1_high - w1_low
        if w1_size <= 0:
            continue

        # Wave 2: pullback after Wave 1 high
        w2_low_i = next((x for x in local_min_idx if x > w1_high_i), None)
        if w2_low_i is None:
            continue

        w2_low = seg_close.iloc[w2_low_i]
        retrace = (w1_high - w2_low) / w1_size

        # Wave 2 must retrace 38.2% - 61.8% of Wave 1
        if not (0.382 <= retrace <= 0.618):
            continue

        # Wave 2 low must be above Wave 1 low (wave structure intact)
        if w2_low < w1_low:
            continue

        # Current price should be recovering from Wave 2 (potential Wave 3 entry)
        current_price = seg_close.iloc[-1]
        if current_price > w2_low and current_price < w1_high * 1.02:
            df.at[df.index[i], 'elliott_wave_signal'] = True
            df.at[df.index[i], 'wave_label'] = 'W2→W3'

    return df
```

### Indicator 6: Fibonacci (`phase2_indicators/fibonacci.py`)

```python
"""
COPILOT PROMPT:
Calculate Fibonacci retracement levels over a rolling REGRESSION_LOOKBACK window.
Swing high = rolling max over lookback, swing low = rolling min over lookback.
Fibonacci levels: 0.236, 0.382, 0.5, 0.618, 0.786

fibonacci_signal = True when current price is between 38.2% and 61.8% retracement
(the "golden zone" pullback area) — i.e., price has pulled back to a fib support level
but hasn't broken the swing low.

Add columns: fib_high, fib_low, fib_382, fib_618, fibonacci_signal
"""

import pandas as pd
from config import REGRESSION_LOOKBACK, FIB_LEVELS

def add_fibonacci_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['fib_high'] = df['Close'].rolling(REGRESSION_LOOKBACK).max()
    df['fib_low'] = df['Close'].rolling(REGRESSION_LOOKBACK).min()
    fib_range = df['fib_high'] - df['fib_low']

    for level in FIB_LEVELS:
        df[f'fib_{int(level*1000):03d}'] = df['fib_high'] - (fib_range * level)

    # Golden zone: price between 38.2% and 61.8% retracement
    df['fib_382'] = df['fib_high'] - (fib_range * 0.382)
    df['fib_618'] = df['fib_high'] - (fib_range * 0.618)

    df['fibonacci_signal'] = (
        (df['Close'] <= df['fib_382']) &
        (df['Close'] >= df['fib_618']) &
        (df['Close'] > df['fib_low'])  # structure intact
    )
    return df
```

### Indicator 7: Linear Regression (`phase2_indicators/regression.py`)

```python
"""
COPILOT PROMPT:
Calculate a rolling linear regression of Close over REGRESSION_LOOKBACK bars.
For each bar, fit a line to the last N closes and project the current value.
regression_signal = True when current Close > regression line value (price above trend).
Add columns: regression_line, regression_signal
"""

import pandas as pd
import numpy as np
from config import REGRESSION_LOOKBACK

def add_regression_signal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    reg_line = [np.nan] * len(df)
    close = df['Close'].values

    for i in range(REGRESSION_LOOKBACK, len(close)):
        y = close[i - REGRESSION_LOOKBACK:i]
        x = np.arange(REGRESSION_LOOKBACK)
        slope, intercept = np.polyfit(x, y, 1)
        reg_line[i] = slope * (REGRESSION_LOOKBACK - 1) + intercept  # value at current bar

    df['regression_line'] = reg_line
    df['regression_signal'] = df['Close'] > df['regression_line']
    return df
```

### Combiner (`phase2_indicators/combiner.py`)

```python
"""
COPILOT PROMPT:
Combine all 7 indicator functions into a single pipeline.
Return a DataFrame with all signal columns plus:
  - signal_count: sum of all 7 boolean signals
  - mandatory_ok: True when both elliott_wave_signal AND fibonacci_signal are True
  - composite_score: signal_count / 7 (float 0.0 to 1.0)
"""

import pandas as pd
from phase2_indicators.trend import add_trend_signal
from phase2_indicators.momentum import add_rsi_signal
from phase2_indicators.volume import add_volume_signal
from phase2_indicators.volatility import add_atr_signal
from phase2_indicators.elliott_wave import add_elliott_wave_signal
from phase2_indicators.fibonacci import add_fibonacci_signal
from phase2_indicators.regression import add_regression_signal

SIGNAL_COLS = [
    'trend_signal', 'rsi_signal', 'volume_signal',
    'atr_signal', 'elliott_wave_signal', 'fibonacci_signal', 'regression_signal'
]

def build_full_indicator_set(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all 7 indicators and return combined DataFrame."""
    df = add_trend_signal(df)
    df = add_rsi_signal(df)
    df = add_volume_signal(df)
    df = add_atr_signal(df)
    df = add_elliott_wave_signal(df)
    df = add_fibonacci_signal(df)
    df = add_regression_signal(df)

    df['signal_count'] = df[SIGNAL_COLS].sum(axis=1)
    df['mandatory_ok'] = df['elliott_wave_signal'] & df['fibonacci_signal']
    df['composite_score'] = df['signal_count'] / 7
    return df
```

---

## 🟠 PHASE 3 — Backtest Framework

### Engine (`phase3_backtest/engine.py`)

```python
"""
COPILOT PROMPT:
Build a BacktestEngine class that:
1. Takes a DataFrame with all indicator signals
2. Generates buy signals when: mandatory_ok=True AND signal_count >= MIN_SIGNALS_TO_BUY
3. Generates sell signals when: stop loss hit OR take profit hit OR holding_period >= MAX
4. Tracks: entry_date, entry_price, exit_date, exit_price, return_pct, hold_days
5. Returns a trades DataFrame and an equity_curve Series
6. Position sizing: flat (1 trade at a time per ticker for simplicity)
"""

import pandas as pd
import numpy as np
from config import (MIN_SIGNALS_TO_BUY, MANDATORY_SIGNALS,
                    HOLDING_PERIOD_MAX, STOP_LOSS_PCT, TAKE_PROFIT_PCT)

class BacktestEngine:
    def __init__(self):
        self.trades = []

    def run(self, df: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, pd.Series]:
        df = df.dropna(subset=['Close']).copy()
        in_trade = False
        entry_price = 0.0
        entry_date = None
        hold_days = 0

        equity = pd.Series(index=df.index, dtype=float)
        capital = 10_000.0
        equity.iloc[0] = capital

        for i, (date, row) in enumerate(df.iterrows()):
            if i == 0:
                continue

            price = row['Close']

            if in_trade:
                hold_days += 1
                pnl_pct = (price - entry_price) / entry_price

                exit_reason = None
                if pnl_pct <= -STOP_LOSS_PCT:
                    exit_reason = 'stop_loss'
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    exit_reason = 'take_profit'
                elif hold_days >= HOLDING_PERIOD_MAX:
                    exit_reason = 'max_hold'
                # Exit on signal reversal
                elif row['signal_count'] < 3:
                    exit_reason = 'signal_exit'

                if exit_reason:
                    capital *= (1 + pnl_pct)
                    self.trades.append({
                        'ticker': ticker,
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': price,
                        'return_pct': round(pnl_pct * 100, 2),
                        'hold_days': hold_days,
                        'exit_reason': exit_reason,
                        'signal_count': row['signal_count'],
                    })
                    in_trade = False
                    hold_days = 0

            else:
                # Entry conditions
                buy_signal = (
                    row['mandatory_ok'] and
                    row['signal_count'] >= MIN_SIGNALS_TO_BUY
                )
                if buy_signal:
                    in_trade = True
                    entry_price = price
                    entry_date = date
                    hold_days = 0

            equity[date] = capital

        trades_df = pd.DataFrame(self.trades)
        equity = equity.ffill()
        return trades_df, equity
```

### Metrics (`phase3_backtest/metrics.py`)

```python
"""
COPILOT PROMPT:
Calculate these metrics from a trades DataFrame and equity curve:
- total_trades: count
- win_rate: % of trades where return_pct > 0
- avg_return: mean return_pct
- avg_win: mean return of winning trades
- avg_loss: mean return of losing trades
- profit_factor: abs(sum wins / sum losses)
- max_drawdown: maximum peak-to-trough drop in equity curve
- sharpe_ratio: annualized (assume 252 trading days)
- total_return_pct: from equity curve start to end
- compare_voo: equity return minus VOO return for same period
"""

import pandas as pd
import numpy as np

def calculate_metrics(trades: pd.DataFrame, equity: pd.Series,
                       voo_equity: pd.Series) -> dict:
    if trades.empty:
        return {"error": "No trades generated"}

    winners = trades[trades['return_pct'] > 0]
    losers = trades[trades['return_pct'] <= 0]

    equity = equity.dropna()
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_drawdown = drawdown.min()

    daily_returns = equity.pct_change().dropna()
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100

    # VOO comparison (align dates)
    aligned_voo = voo_equity.reindex(equity.index).ffill()
    voo_return = (aligned_voo.iloc[-1] / aligned_voo.iloc[0] - 1) * 100

    return {
        'total_trades': len(trades),
        'win_rate': round(len(winners) / len(trades) * 100, 1),
        'avg_return': round(trades['return_pct'].mean(), 2),
        'avg_win': round(winners['return_pct'].mean(), 2) if not winners.empty else 0,
        'avg_loss': round(losers['return_pct'].mean(), 2) if not losers.empty else 0,
        'profit_factor': round(
            winners['return_pct'].sum() / abs(losers['return_pct'].sum()), 2
        ) if not losers.empty else float('inf'),
        'max_drawdown': round(max_drawdown * 100, 2),
        'sharpe_ratio': round(sharpe, 2),
        'total_return_pct': round(total_return, 2),
        'voo_return_pct': round(voo_return, 2),
        'alpha': round(total_return - voo_return, 2),
    }
```

---

## 🟢 PHASE 4 — Buy/Sell Signal Generator

### `phase4_signals/signal_generator.py`

```python
"""
COPILOT PROMPT:
Build a SignalGenerator class that:
1. Takes the latest N bars of data (default 200)
2. Runs full indicator pipeline
3. Returns today's signal as a dict:
   {
     ticker: str,
     date: str,
     action: 'BUY' | 'SELL' | 'HOLD',
     signal_count: int,
     mandatory_ok: bool,
     confidence: str ('HIGH'|'MEDIUM'|'LOW'),
     signals_active: list[str],
     signals_missing: list[str]
   }
"""

import pandas as pd
from phase2_indicators.combiner import build_full_indicator_set, SIGNAL_COLS
from config import MIN_SIGNALS_TO_BUY

class SignalGenerator:
    def generate(self, df: pd.DataFrame, ticker: str) -> dict:
        df = build_full_indicator_set(df)
        latest = df.iloc[-1]

        active = [s for s in SIGNAL_COLS if latest.get(s, False)]
        missing = [s for s in SIGNAL_COLS if not latest.get(s, False)]

        signal_count = int(latest['signal_count'])
        mandatory_ok = bool(latest['mandatory_ok'])

        if mandatory_ok and signal_count >= MIN_SIGNALS_TO_BUY:
            action = 'BUY'
        elif signal_count <= 2:
            action = 'SELL'
        else:
            action = 'HOLD'

        confidence = 'HIGH' if signal_count >= 6 else 'MEDIUM' if signal_count >= 4 else 'LOW'

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
        }
```

---

## 🔵 PHASE 5 — Review & Rule Adjustment

### `phase5_review/reporter.py`

```python
"""
COPILOT PROMPT:
Build a PerformanceReporter that:
1. Loads all backtest results
2. Prints a comparison table: ticker | total_return | voo_return | alpha | win_rate | trades | sharpe | max_dd
3. Tests 4/7 vs 5/7 threshold — which MIN_SIGNALS_TO_BUY setting wins?
4. Shows which individual signals contributed most to winning trades
5. Saves report to reports/backtest_report_{date}.csv
"""
```

### Signal Contribution Analysis

```python
"""
COPILOT PROMPT:
For each signal in SIGNAL_COLS, calculate:
- How often it was True in winning trades vs losing trades
- Its "lift": P(win | signal=True) / P(win | signal=False)
Sort by lift descending to identify most valuable signals.
"""
```

---

## 🟣 PHASE 6 — Paper Trading

### `phase6_paper_trade/portfolio.py`

```python
"""
COPILOT PROMPT:
Build a PaperPortfolio class that:
1. Loads from/saves to a JSON file (paper_portfolio.json)
2. Has methods: open_position(ticker, price, date), close_position(ticker, price, date)
3. Tracks: cash, positions (ticker → {shares, entry_price, entry_date}), trade_history
4. Calculates: current P&L, portfolio value, % gain vs starting capital
5. POSITION_SIZE_PCT of PAPER_CAPITAL per trade, max MAX_POSITIONS open
"""

import json, os
import pandas as pd
from config import PAPER_CAPITAL, POSITION_SIZE_PCT, MAX_POSITIONS

class PaperPortfolio:
    SAVE_PATH = "phase6_paper_trade/paper_portfolio.json"

    def __init__(self):
        self.cash = PAPER_CAPITAL
        self.positions = {}
        self.trade_history = []
        self._load()

    def open_position(self, ticker: str, price: float, date: str) -> bool:
        if len(self.positions) >= MAX_POSITIONS:
            print(f"[SKIP] Max positions ({MAX_POSITIONS}) reached.")
            return False
        if ticker in self.positions:
            print(f"[SKIP] Already in {ticker}")
            return False
        alloc = PAPER_CAPITAL * POSITION_SIZE_PCT
        shares = alloc / price
        self.positions[ticker] = {
            'shares': shares, 'entry_price': price, 'entry_date': date
        }
        self.cash -= alloc
        self._save()
        print(f"[BUY] {ticker} @ ${price:.2f} | {shares:.2f} shares | Alloc: ${alloc:.0f}")
        return True

    def close_position(self, ticker: str, price: float, date: str) -> float:
        if ticker not in self.positions:
            print(f"[SKIP] No position in {ticker}")
            return 0.0
        pos = self.positions.pop(ticker)
        proceeds = pos['shares'] * price
        cost = pos['shares'] * pos['entry_price']
        pnl = proceeds - cost
        pnl_pct = (pnl / cost) * 100
        self.cash += proceeds
        self.trade_history.append({
            'ticker': ticker, 'entry_date': pos['entry_date'],
            'exit_date': date, 'entry_price': pos['entry_price'],
            'exit_price': price, 'pnl_pct': round(pnl_pct, 2)
        })
        self._save()
        print(f"[SELL] {ticker} @ ${price:.2f} | PnL: {pnl_pct:+.2f}%")
        return pnl_pct

    def portfolio_value(self, current_prices: dict) -> float:
        equity = self.cash
        for ticker, pos in self.positions.items():
            equity += pos['shares'] * current_prices.get(ticker, pos['entry_price'])
        return equity

    def summary(self, current_prices: dict) -> dict:
        pv = self.portfolio_value(current_prices)
        return {
            'portfolio_value': round(pv, 2),
            'cash': round(self.cash, 2),
            'open_positions': len(self.positions),
            'total_return_pct': round((pv / PAPER_CAPITAL - 1) * 100, 2),
            'trades_closed': len(self.trade_history)
        }

    def _save(self):
        os.makedirs(os.path.dirname(self.SAVE_PATH), exist_ok=True)
        with open(self.SAVE_PATH, 'w') as f:
            json.dump({'cash': self.cash, 'positions': self.positions,
                       'trade_history': self.trade_history}, f, indent=2)

    def _load(self):
        if os.path.exists(self.SAVE_PATH):
            with open(self.SAVE_PATH) as f:
                data = json.load(f)
            self.cash = data.get('cash', PAPER_CAPITAL)
            self.positions = data.get('positions', {})
            self.trade_history = data.get('trade_history', [])
```

---

## 📊 DASHBOARD — Streamlit App

### `dashboard/app.py`

```python
"""
COPILOT PROMPT:
Build a Streamlit dashboard with these tabs:
1. 📥 Data — Show data validation table, download button
2. 📈 Indicators — Select ticker, show candlestick + all 7 indicators as plotly subplots
3. 🔁 Backtest — Run backtest, show metrics table + equity curve vs VOO
4. 🚦 Signals — Show current BUY/SELL/HOLD for each ticker with signal breakdown
5. 💼 Portfolio — Paper trade portfolio status, open positions, trade history
6. ⚙️ Config — Sliders to adjust MIN_SIGNALS_TO_BUY, RSI thresholds, etc. (updates config live)

Use st.cache_data for expensive computations.
Use plotly for all charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="7-Signal Trading System",
    page_icon="📈",
    layout="wide"
)

st.title("📈 7-Signal Stock Trading System")
st.caption("Elliott Wave + Fibonacci | Beats VOO by 5%+ Target")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📥 Data", "📊 Indicators", "🔁 Backtest",
    "🚦 Signals", "💼 Portfolio", "⚙️ Config"
])

with tab1:
    st.header("Phase 1 — Data Validation")
    # TODO: Load validator output and display as st.dataframe

with tab2:
    st.header("Phase 2 — Indicator Analysis")
    ticker = st.selectbox("Select Ticker", ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"])
    # TODO: Load indicator data and plot with plotly subplots

with tab3:
    st.header("Phase 3 — Backtest Results")
    min_signals = st.slider("Min Signals Required", 3, 7, 5)
    # TODO: Run backtest with selected threshold and display metrics

with tab4:
    st.header("Phase 4 — Live Signals")
    # TODO: Show current signals for all tickers

with tab5:
    st.header("Phase 6 — Paper Portfolio")
    # TODO: Show portfolio summary and trade history

with tab6:
    st.header("Configuration")
    # TODO: Show editable config parameters
```

---

## 🧪 Tests

### `tests/test_indicators.py`

```python
"""
COPILOT PROMPT:
Write pytest unit tests for each indicator:
1. test_ema_trend: Check that trend_signal is True only when Close > EMA50 > EMA200
2. test_rsi_bounds: RSI must always be between 0 and 100
3. test_volume_signal: volume_signal False when volume = 0
4. test_atr_positive: ATR must always be >= 0
5. test_fibonacci_zone: fibonacci_signal only True when price is in golden zone
6. test_regression_above: regression_signal True when Close > regression_line

Use synthetic data (np.random or hand-crafted series) for deterministic testing.
"""
import pytest
import pandas as pd
import numpy as np
```

---

## 📦 requirements.txt

```
yfinance>=0.2.40
pandas>=2.0.0
numpy>=1.26.0
plotly>=5.18.0
streamlit>=1.32.0
scipy>=1.12.0
ta>=0.11.0
pytest>=8.0.0
```

---

## 🚀 Quick Start Commands

```bash
# 1. Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Run Phase 1 (ALWAYS start here per session)
python run_phase1.py

# 3. Run full pipeline
python run_all.py

# 4. Launch dashboard
streamlit run dashboard/app.py

# 5. Run tests
pytest tests/ -v
```

---

## 🔁 Full Pipeline Runner: `run_all.py`

```python
"""
COPILOT PROMPT:
Build run_all.py that executes all phases in sequence:
1. Phase 1: Download + validate data
2. Phase 2: Calculate all indicators for each valid ticker
3. Phase 3: Run backtest for each ticker, collect metrics
4. Phase 4: Generate current signals
5. Print a final summary report showing:
   - Which tickers have BUY signals today
   - Backtest performance vs VOO
   - Whether any ticker qualifies for scale-up (beating VOO by 5%+)
"""
```

---

## 💡 Copilot Prompting Tips

When using GitHub Copilot with this codebase:

1. **Always open config.py first** — Copilot learns your parameter names
2. **Use the docstring prompts** in each file — they are written as Copilot instructions
3. **After each phase**, ask: *"Does this function handle edge cases: empty DataFrames, NaN values, single-stock universes?"*
4. **For Elliott Wave refinement**, ask Claude: *"Review my pivot detection logic and suggest improvements for noisy daily data"*
5. **For backtest slippage**, ask Copilot: *"Add 0.1% slippage and $5 commission per trade to the BacktestEngine"*

---

## 📋 Session Checklist (paste this reminder each session)

```
[ ] Opened config.py to load parameters into Copilot context
[ ] Phase 1 ran successfully, valid tickers confirmed
[ ] All 7 indicators produce non-NaN values after warmup period
[ ] Backtest mandatory_ok gate enforces Elliott + Fibonacci both True
[ ] VOO benchmark aligned by date index before alpha calculation
[ ] Paper portfolio saved to JSON (persistent across sessions)
[ ] Dashboard running at localhost:8501
```

---

*Generated context for GitHub Copilot + Claude Sonnet trading system project.*
*Last updated: 2025 | Python 3.11+ | Streamlit + Plotly dashboard*
