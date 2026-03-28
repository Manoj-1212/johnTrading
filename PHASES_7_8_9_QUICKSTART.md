# Phases 7-9 Quick Start

## 5-Minute Setup

### Step 1: Install Requirements
```bash
pip install alpaca-py yfinance pandas numpy scipy
```

### Step 2: Get Alpaca API Keys
1. Go to https://alpaca.markets → Sign up (free)
2. Go to https://app.alpaca.markets → Account → API Keys
3. Create new keys and copy them

### Step 3: Set Environment Variables (Windows PowerShell)
```powershell
$env:APCA_API_KEY_ID = "PK_YOUR_KEY_HERE"
$env:APCA_API_SECRET_KEY = "YOUR_SECRET_HERE"
$env:APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
```

Or (Windows Command Prompt):
```cmd
set APCA_API_KEY_ID=PK_YOUR_KEY_HERE
set APCA_API_SECRET_KEY=YOUR_SECRET_HERE
set APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### Step 4: Test Setup
```bash
python -c "from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface; AlpacaBrokerInterface(paper_trading=True, debug=True)"
```

You should see:
```
✓ Connected to Alpaca (PAPER TRADING)
  Account: YOUR_ACCOUNT_NUMBER
  Cash: $25,000.00
  Portfolio Value: $25,000.00
```

### Step 5: Run System

#### Option A: Test Phase 7 (data streaming)
```bash
python run_phase7.py
# Output: Real-time 1-minute bars for 10 minutes
```

#### Option B: Test Phase 8 (execution)
```bash
python run_phase8.py
# Output: Real-time execution with paper trading
```

#### Option C: Run Full System (Phases 7-9)
```bash
python run_phase9.py
# Output: Complete production-grade trading
```

## What You'll See

### Console Output
```
================================================================================
PRODUCTION-GRADE REAL-TIME TRADING SYSTEM
================================================================================
Mode: PAPER TRADING
Phases: 7 (Data) → 8 (Execution) → 9 (Risk Management)
Start: 2026-03-28 09:30:00
Tickers: 20 stocks
Duration: 10 minutes
================================================================================

Initial Account State:
  Cash: $24,500.00
  Portfolio Value: $25,000.00
  Buying Power: $49,000.00

Phase 7: Downloading daily baseline data...
✓ Baseline data ready for 20 tickers

Phase 7-9: Starting real-time stream...
------------------------------------------------------------------------
[09:30:45] 📈 AAPL | BUY  | HIGH   |  $150.25 | Strength: 4
[09:31:50] 📈 BUY: 10 shares of AAPL @ $150.25
[09:32:15] 📉 MSFT | SELL | MEDIUM |  $380.50 | Strength: 3
[09:33:30] 🚫 MSFT BLOCKED: Sector concentration limit (Technology: 35%)
...
```

### Generated Files
```
phase7_realtime_streaming/
  ├── data_cache/           # Intraday bar cache
  ├── realtime_signals/     # Individual signals (JSON)
  └── logs/                 # Session state logs

phase8_execution/
  ├── trades/               # Individual trade logs
  └── logs/                 # Execution summary

phase9_production_trading/
  ├── trades/               # Combined trade history
  └── logs/
      └── session_20260328_093045.json  # Full session log
```

## Key Configuration

Edit these values in risk manager to adjust behavior:

### Position Sizing
```python
self.max_position_size_pct = 0.05  # Max 5% of portfolio per position
```
→ Decrease to 0.02 for more conservative (2% per position)
→ Increase to 0.10 for more aggressive (10% per position)

### Daily Loss Limit
```python
self.daily_loss_limit_pct = 0.02   # Stop trading after -2% loss
```
→ Decrease to 0.01 for strict (-1% and stop)
→ Increase to 0.05 for lenient (-5% and stop)

### Market Regime
```python
self.max_vix_for_trading = 50      # Don't trade if VIX > 50
```
→ Decrease to 40 if want to trade only in calm markets
→ Increase to 60 if want to trade through volatility

### Update Frequency
```python
engine.run(duration_minutes=390, update_interval=60)
            # 390 = full day (9:30-16:00 EST)
            # 60 = check every 60 seconds
```
→ Change to 30 = check every 30 seconds (faster)
→ Note: yfinance has 15-minute delay anyway

## Common Commands

### Run full market day (390 minutes)
```bash
python run_phase9.py  # Modify duration_minutes=390 in run_phase9.py
```

### Run for just 30 minutes (before market close)
```bash
python -c "
import run_phase9
engine = run_phase9.ProductionTradingSystem()
engine.run(duration_minutes=30)
"
```

### Test paper trading connection only
```bash
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True, debug=True)
print('✓ Connection successful')
"
```

### Check account balance
```bash
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True)
info = broker.get_account_info()
print(f'Cash: \${info[\"cash\"]:.2f}')
print(f'Portfolio Value: \${info[\"portfolio_value\"]:.2f}')
"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No data for ticker" | Ticker doesn't exist or market is closed. Test with AAPL during 9:30-16:00 EST |
| "API key not found" | Re-run `set` or `export` commands for environment variables |
| "No position for TICKER" | Haven't executed BUY for that ticker yet. Signals are only SELL if you have position |
| "Insufficient buying power" | Position too large for current cash. Reduce position size or add more capital |
| "VIX too high" | Market is very volatile (VIX > 50). System automatically pauses trading |

## Real Money Setup (Advanced)

**Only after 2+ weeks of successful paper trading:**

1. **Upgrade Alpaca Account**
   - Go to https://app.alpaca.markets → Account → Settings
   - Switch from Paper to Live trading
   - Fund account (minimum varies)

2. **Update Environment Variable**
   ```bash
   set APCA_API_BASE_URL=https://api.alpaca.markets
   # (removes "paper-" prefix)
   ```

3. **Update Python Code**
   ```python
   # In run_phase9.py, change:
   trading_system = ProductionTradingSystem(
       paper_trading=False  # ← Change to False
   )
   ```

4. **Start Small**
   - Reduce position size to 0.5-1% initially
   - Monitor for full week
   - Gradually increase to 2-5%

## Getting Help

1. **Check logs**: `phase9_production_trading/logs/session_*.json`
2. **Review trades**: `phase9_production_trading/trades/*.json`
3. **Test individually**: Run `run_phase7.py`, `run_phase8.py`, `run_phase9.py` separately
4. **Check Alpaca docs**: https://docs.alpaca.markets/API-references/trading-api

---

**Ready? Run:** `python run_phase9.py` 🚀
