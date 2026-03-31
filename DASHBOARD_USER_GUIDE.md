# 📊 Real-Time Dashboard Guide

**File**: `dashboard_realtime.py` (533 lines, Streamlit)  
**Purpose**: Monitor Phases 7-9 automated trading in real-time  
**Launch**: `streamlit run dashboard_realtime.py --server.port 8501`  
**Access**: `http://ec2_ip:8501`

---

## 🎯 Dashboard Overview

### What It Shows (5 Complete Tabs)

The dashboard displays live data from your running Phases 7-9 trading system with automatic updates every 60 seconds during market hours (9:30 AM - 4:00 PM EST).

---

## 📊 Tab 1: Live Signals (Primary Tab)

**Purpose**: Real-time trading signal status for all 20 tickers

### Summary Cards (Top)
```
┌──────────────┬──────────────┬──────────────┐
│ 🟢 BUY       │ 🟡 HOLD      │ 🔴 SELL      │
│ Signals: 4   │ Signals: 12  │ Signals: 4   │
└──────────────┴──────────────┴──────────────┘
```

Shows current count of:
- **BUY signals**: How many tickers show strong buy setup (≥5 indicators aligned)
- **HOLD signals**: How many tickers show neutral setup (3-4 indicators)
- **SELL signals**: How many tickers show sell setup (≤2 indicators)

### Signal Table (20 rows - one per ticker)

```
Ticker │ Signal │ Active Signals │ Confidence │ Last Update
────────────────────────────────────────────────────────
AAPL   │ 🟢 BUY │ 6/7            │ HIGH      │ 10:35:12 AM
MSFT   │ 🟡 HOLD│ 4/7            │ MEDIUM    │ 10:35:13 AM
GOOGL  │ 🔴 SELL│ 2/7            │ MEDIUM    │ 10:35:10 AM
...    │ ...    │ ...            │ ...       │ ...
```

**Column Details**:
- **Ticker**: Stock symbol (AAPL, MSFT, etc.)
- **Signal**: Current trading signal
  - 🟢 BUY (≥5/7 indicators say BUY)
  - 🟡 HOLD (3-4 indicators)
  - 🔴 SELL (≤2/7 indicators)
- **Active Signals**: How many of the 7 indicators are triggered (e.g., 6/7)
- **Confidence**: HIGH/MEDIUM/LOW based on signal strength
- **Last Update**: When signal was last calculated (should be within last 60s)

### How to Use

**Ideal Setup for Trading**:
- Look for 🟢 BUY signals with 6-7 active indicators = HIGH confidence
- 6/7 indicators = 85% alignment = safe entry
- 7/7 indicators = 100% alignment = very rare but strongest signal

**Monitor for Changes**:
- Watch for transitions (🟢 → 🟡 → 🔴)
- Signals update every minute during market hours
- Dashboard auto-refreshes every 60 seconds

**Risk Indicator**:
- If most tickers show 🔴 SELL = market may be in downtrend
- If all show 🟡 HOLD = market consolidating
- If many show 🟢 BUY = market in uptrend

---

## 💼 Tab 2: Portfolio (Tracking Tab)

**Purpose**: Current portfolio status, open positions, and P&L

### Summary Metrics (Top)

```
┌──────────────────┬──────────────────┬──────────────────┐
│ Portfolio Value  │ Available Cash   │ Open Positions   │
│ $10,247.50       │ $8,432.75        │ 3                │
├──────────────────┼──────────────────┼──────────────────┤
│ Daily P&L        │                  │                  │
│ +$247.50 (+2.5%) │                  │                  │
└──────────────────┴──────────────────┴──────────────────┘
```

**Key Metrics**:
- **Portfolio Value**: Current cash + position value
  - Starting: $10,000
  - Example after trading: $10,247.50 = +2.47% ROI
  
- **Available Cash**: Capital not in positions (ready for new trades)
  - Example: $8,432.75 = 84% in cash positions
  
- **Open Positions**: How many trades are currently active
  - Example: 3 positions (AAPL, MSFT, V)
  
- **Daily P&L**: Profit/loss today
  - +$247.50 = positive, trading well
  - Resets daily at market close
  - Color changes: Green (+), Red (-)

### Open Positions Table

Shows every active position you're currently holding:

```
Ticker │ Shares │ Entry Price │ Current Price │ P&L    │ Return │ Entry Time       │ Hold Time
────────────────────────────────────────────────────────────────────────────────────────────
AAPL   │ 5      │ $152.30     │ $155.80       │ +$17.50│ +2.30% │ 10:35 AM        │ 2h 15m
MSFT   │ 3      │ $372.10     │ $375.25       │ +$9.45 │ +0.85% │ 11:20 AM        │ 1h 30m
V      │ 7      │ $268.90     │ $271.15       │ +$16.15│ +0.84% │ 12:05 PM        │ 45m
────────────────────────────────────────────────────────────────────────────────────────────
```

**Column Details**:
- **Ticker**: Stock you're holding
- **Shares**: Number of shares in position
- **Entry Price**: Price you bought at
- **Current Price**: Last market price
- **P&L**: Dollar profit/loss on position
- **Return %**: Percentage return
- **Entry Time**: When you opened position
- **Hold Time**: How long you've held it

### Portfolio Value Chart

Visual representation of portfolio value over time (last 7 days shown):

```
$10,500 │                      ╱╲
         │                    ╱  ╲
$10,250 │                   ╱    ╲    ╱╲
         │                 ╱      ╲  ╱  ╲
$10,000 │────────────────╱────────┱─╱────
         │
         └─────────────────────────────────
           Today    Yesterday   2 Days Ago
```

**What It Shows**:
- X-axis: Last 7 days
- Y-axis: Portfolio value in dollars
- Line chart: Upward trend = winning strategy
- Downward trend = losing days

### How to Use

**Monitor During Trading Day**:
- Watch P&L update in real-time
- Every 60 seconds, prices refresh
- See if positions are winning or losing

**Position Management**:
- Exits are automatic when conditions met
- Manual close: Edit `run_phase9_production.py` signal thresholds
- Stop-loss: V1 at 5% position size limit

**Daily Monitoring**:
- At 4 PM EST, system closes all positions
- Daily P&L resets next day at 9:30 AM
- Track cumulative performance weekly

---

## 📈 Tab 3: Performance (Analysis Tab)

**Purpose**: Detailed performance statistics and metrics

### Return Metrics (Top 3 Cards)

```
┌──────────────┬──────────────┬──────────────┐
│ Daily Return │ Weekly Return│ Monthly      │
│ +2.48%       │ +8.75%       │ +15.23%      │
└──────────────┴──────────────┴──────────────┘
```

**Interpretation**:
- **Daily Return**: Today's P&L as % of starting capital
  - +2.48% = great day
  - +0.5-1% = normal good day
  - -1% to -2% = acceptable loss
  
- **Weekly Return**: Last 5 trading days accumulated
  - +8.75% = excellent week
  
- **Monthly Return**: Last 21 trading days accumulated
  - +15.23% = very strong performance

### Trade Statistics Table

Detailed metrics of your trading:

```
Metric               │ Value      │ Interpretation
─────────────────────┼────────────┼─────────────────────────
Trades Today         │ 12         │ Active trading (1-2 per hour)
Winning Trades       │ 8          │ Win rate = 66.7%
Losing Trades        │ 4          │ Loss rate = 33.3%
Best Trade           │ +$52.30    │ Biggest gain today
Worst Trade          │ -$8.50     │ Biggest loss today
Avg Trade Return     │ +$20.63    │ Average profit per trade
Consecutive Wins     │ 4          │ 4 trades in a row profitable
Sharpe Ratio         │ 1.85       │ Risk-adjusted return (>1 = good)
Max Drawdown         │ -$125      │ Worst losing streak
```

**What Each Means**:

- **Trades Today**: Count of all executed trades (BUY + SELL)
- **Win Rate**: Percentage of profitable trades (>50% = good)
- **Best Trade**: Largest single profit (shows potential)
- **Worst Trade**: Largest single loss (shows risk)
- **Avg Return**: Average profit per trade
- **Consecutive Wins**: How many trades in a row were profitable
- **Sharpe Ratio**: Risk-adjusted return (2+ = excellent, 1-2 = good, <1 = poor)
- **Max Drawdown**: Worst peak-to-trough loss (lower = better)

### Equity Curve

Shows portfolio growth over the week:

```
Equity Curve (Last 5 Days)
$10,500 │
         │        ╱╱  ╱╱
$10,250 │      ╱╱  ╱╱
         │    ╱╱  ╱╱
$10,000 │───╱───────
         │
         └─────────────────
           Mon Tue Wed Thu Fri
```

**How to Interpret**:
- Upward trajectory = profitable system
- Downward = losing money
- Flat = breakeven/consolidating
- Steep angle = high daily returns

---

## 🔍 Tab 4: Risk Metrics (Safety Tab)

**Purpose**: Monitor risk exposure and safety controls

### Key Risk Indicators (Top 3)

```
┌──────────────┬──────────────┬──────────────┐
│ VIX Level    │ Market Regime│ Can Trade?   │
│ 20.5         │ NORMAL       │ ✅ YES       │
└──────────────┴──────────────┴──────────────┘
```

**VIX Level** (Volatility Index):
- **10-15**: Low volatility, calm market
- **15-20**: Normal volatility (optimal for trading)
- **20-30**: Elevated volatility, be cautious
- **30-50**: High volatility (Phase 9 limits trading)
- **50+**: Extreme volatility (Phase 9 stops trading)

**Market Regime**:
- 🟢 **NORMAL**: VIX <20, trading as planned
- 🟡 **ELEVATED**: VIX 20-30, add caution
- 🔴 **HIGH**: VIX 30-50, limit new positions
- ⚫ **EXTREME**: VIX >50, stop trading

**Can Trade?**:
- ✅ **YES**: All systems green, ready to trade
- ⚠️ **CAUTION**: Some limits approaching
- ❌ **NO**: Risk limits exceeded, trading halted

### Risk Controls Active

Shows which safety limits are checked:

```
Control                          │ Status      │ Current / Limit
──────────────────────────────────┼─────────────┼─────────────────
Max Position Size Per Ticker     │ ✅ OK       │ NVDA: 4.5% / 5%
Daily Loss Limit                 │ ✅ OK       │ -$127.50 / -$200
Maximum VIX (stop trading)       │ ✅ OK       │ 20.5 / 50
Total Positions (max 10)         │ ✅ OK       │ 3 / 10
Same Ticker Protection           │ ✅ OK       │ 1 position per ticker
Consecutive Trade Limit          │ ✅ OK       │ 8 / 20 per day
```

**What Each Control Does**:
- **Max Position Size**: Limits to 5% per ticker (max)
- **Daily Loss**: Stops trading if down 2% per day
- **VIX Check**: Won't trade if market too volatile
- **Max Positions**: Never more than 10 open trades
- **No Duplicates**: Can't have 2 positions in AAPL
- **Trade Limit**: Max 20 trades per trading day

### Position Risk: Detailed Breakdown

Each position analyzed for risk:

```
Ticker │ Position  │ % of     │ Stop-Loss │ Risk Status
       │ Value     │ Portfolio│ Level     │
────────┼───────────┼──────────┼───────────┼──────────────
AAPL   │ $764.00   │ 7.6%     │ $144.70   │ ✅ Safe
MSFT   │ $1,125.75 │ 11.2%    │ $353.50   │ ✅ Safe
V      │ $1,899.05 │ 18.9%    │ $255.35   │ ⚠️ Watch
────────┴───────────┴──────────┴───────────┴──────────────
```

**Risk Gauges** (Visual):

**Daily Loss Gauge**:
```
Daily Loss Limit: -2% ($200)
├─────────────────────────────────────┤
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└─────────────────────────────────────┘
-127.50 / -200
```
- Green area = safe, -1% or better
- Yellow area = caution, -1% to -1.5%
- Red area = risk, approaching -2%

**Position Concentration Gauge**:
```
Max Position Concentration: 30%
├─────────────────────────────────────┤
│░░░░░░░░░░░░░░░░░░░░    ░░░░░░░░░░│
└─────────────────────────────────────┘
18.9% (MSFT largest) / 30% limit
```
- Green = well diversified
- Yellow = getting concentrated
- Red = too concentrated in one ticker

### How to Use

**Monitor Risks**:
- Watch VIX level during trading hours
- Keep eye on daily loss (orange zone = danger)
- Ensure "Can Trade?" = ✅ YES

**Adjust Limits**:
- Edit `config.py` to change position size limits
- Daily loss limit: 2% (in `risk_manager.py`)
- VIX threshold: 50 (in `risk_manager.py`)

**Act on Warnings**:
- ⚠️ CAUTION: Review positions, be ready to exit
- ❌ NO: Stop trading manually until limits reset

---

## 📋 Tab 5: Trade Log (History Tab)

**Purpose**: See all trades executed in the last 24 hours

### Recent Trades Table

Shows every trade with execution details:

```
Time      │ Ticker │ Signal │ Type    │ Shares │ Price  │ Amount    │ Status
──────────┼────────┼────────┼─────────┼────────┼────────┼───────────┼─────────
10:35 AM  │ AAPL   │ BUY    │ Market  │ 5      │ $152.30│ $761.50   │ FILLED
10:45 AM  │ GOOGL  │ BUY    │ Market  │ 2      │ $139.45│ $278.90   │ FILLED
11:20 AM  │ MSFT   │ BUY    │ Market  │ 3      │ $372.10│ $1,116.30 │ FILLED
12:15 PM  │ AAPL   │ SELL   │ Market  │ 5      │ $155.80│ $779.00   │ FILLED
01:30 PM  │ GOOGL  │ SELL   │ Market  │ 2      │ $141.20│ $282.40   │ FILLED
...
```

**Column Meanings**:
- **Time**: When trade was executed
- **Ticker**: Which stock
- **Signal**: Was it BUY or SELL?
- **Type**: Market (instant) or Limit (conditional)
- **Shares**: Number of shares traded
- **Price**: Execution price
- **Amount**: Total dollars (Shares × Price)
- **Status**: FILLED (done), PENDING (waiting), REJECTED (failed)

### Filter By Signal Type

Buttons to filter trades:
- **All Trades**: Show everything
- **Buy Only**: Show just BUY orders
- **Sell Only**: Show just SELL orders

### Export Options

Download trade history:
- **CSV**: For Excel analysis
- **Excel**: Full spreadsheet format
- **JSON**: For programmatic processing

### Market Hours Indicator

```
Market Status: OPEN (Opens 9:30 AM, Closes 4:00 PM EST)

Pre-Market:   3:00 AM - 9:30 AM EST  (trades not recommended)
Regular:      9:30 AM - 4:00 PM EST  (full liquidity)
After-Hours:  4:00 PM - 8:00 PM EST  (low liquidity, risky)
```

### How to Use

**Daily Review**:
- Check total trades per day (aim for 10-20)
- Review profit factor (wins vs losses)
- Identify best performing entry times

**Troubleshooting**:
- If many rejected trades: Check available capital
- If no trades: Check signal thresholds
- If all losses: Review indicator settings

**Strategy Improvement**:
- Analyze which trades were losers
- Notice patterns (time of day, specific tickers)
- Adjust entry/exit rules based on data

---

## ⚙️ System Status (Sidebar)

Left sidebar shows current system info:

```
┌────────────────────────────────────┐
│  🟢 SYSTEM STATUS                  │
│                                    │
│  Status: TRADING                   │
│  Service: johntrading (✅ Active)  │
│  Tickers: 20/20 online             │
│  Market: OPEN (9:30-16:00 EST)     │
│  Uptime: 4h 32m 15s                │
│                                    │
│  Configuration:                    │
│  ├─ Capital: $10,000               │
│  ├─ Max Position: 5% per ticker    │
│  ├─ Daily Loss Limit: -2%          │
│  ├─ Min Signals: 5/7 indicators    │
│  └─ Order Type: Market             │
│                                    │
│  Latest Metrics:                   │
│  ├─ Portfolio: $10,247.50 (+2.48%)│
│  ├─ Daily Trades: 12               │
│  ├─ Win Rate: 66.7%                │
│  └─ Best Trade: +$52.30            │
│                                    │
└────────────────────────────────────┘
```

**Status Indicators**:
- 🟢 **GREEN**: System running normally
- 🟡 **YELLOW**: Caution (check risk metrics)
- 🔴 **RED**: Error (check logs)

---

## 🔄 Auto-Refresh Behavior

### During Market Hours (9:30 AM - 4:00 PM EST)
- Dashboard refreshes every 60 seconds automatically
- All tabs update with latest data
- Portfolio values, prices, P&L recalculate

### Before/After Market Hours
- Dashboard shows previous session data
- "Market is closed" message appears
- Can still view historical trades from day

### Manual Refresh
- Press **"Refresh Now"** button (if available)
- Or reload browser page (F5)

---

## 🎯 Quick Monitoring Checklist

Use this during each trading day:

### 9:30 AM - Market Open
- [ ] Dashboard loads successfully
- [ ] All 20 tickers show (◆ up to date)
- [ ] Portfolio Value = $10,000 (or previous close)
- [ ] Available Cash = full starting amount
- [ ] Status = "TRADING"

### 10:00 AM - 2:00 PM (During Trading)
- [ ] Live Signals tab: Check for BUY signals
- [ ] Portfolio tab: Monitor open positions
- [ ] Risk Metrics: Verify Can Trade = ✅ YES
- [ ] Trade Log: See your executions live

### 3:30 PM - Market Close Prep
- [ ] Review daily P&L
- [ ] Check for any open positions
- [ ] Note any warning (yellow/red indicators)

### 4:00 PM - Market Closed
- [ ] All positions closed automatically
- [ ] Final daily P&L recorded
- [ ] Review Trade Log for improvements

---

## 📞 Troubleshooting Dashboard

### Dashboard Won't Load

**Problem**: Browser shows "Unable to connect"
```bash
# Check if service is running
sudo systemctl status johntrading

# Verify port 8501 is listening
sudo netstat -tlnp | grep 8501

# Restart dashboard
streamlit run dashboard_realtime.py --server.port 8501
```

### Data Not Updating

**Problem**: Dashboard shows stale data (Last Update = hours ago)
```bash
# Check if trading service is running
journalctl -u johntrading -f

# Ensure we're during market hours
# Dashboard updates 9:30 AM - 4:00 PM EST only
```

### Missing Tickers

**Problem**: Tab shows only 15 tickers instead of 20
```bash
# Check logs for download failures
journalctl -u johntrading | grep "Failed to download"

# Verify all tickers are enabled in config.py
grep "TICKERS =" config.py
```

### Incorrect P&L

**Problem**: Portfolio shows wrong P&L
```bash
# Dashboard may be showing cached data
# Try manual refresh or browser reload

# If persists, check actual execution in logs
journalctl -u johntrading | grep "Trade executed"
```

---

## 🚀 Deploying the Dashboard

### First Time Setup

```bash
# 1. SSH to EC2
ssh -i key.pem ubuntu@ec2_ip

# 2. Navigate to project
cd ~/johntrading
source .venv/bin/activate

# 3. Run dashboard
streamlit run dashboard_realtime.py --server.port 8501

# 4. Get EC2 public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# 5. Open browser
# http://your_ec2_public_ip:8501
```

### Running in Background (Recommended)

```bash
# Using nohup (keeps running after SSH close)
nohup streamlit run dashboard_realtime.py --server.port 8501 > dashboard.log 2>&1 &

# View logs
tail -f dashboard.log

# Kill if needed
pkill -f "streamlit run dashboard_realtime.py"
```

### Running as System Service (Advanced)

Create `/etc/systemd/system/dashboard.service`:
```ini
[Unit]
Description=Trading Dashboard
After=network.target johntrading.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/johntrading
ExecStart=/home/ubuntu/.venv/bin/streamlit run dashboard_realtime.py --server.port 8501
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard
sudo systemctl start dashboard
sudo systemctl status dashboard
```

---

**Last Updated**: March 29, 2026  
**Status**: ✅ Ready for production use  
**Refresh Rate**: Every 60 seconds during market hours

🎯 Use the dashboard to monitor your trading system in real-time!
