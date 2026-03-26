# 📊 PORTFOLIO DASHBOARD GUIDE

Your John Trading System now includes a **web-based portfolio dashboard** for real-time visualization of trades, signals, and analysis.

---

## 🚀 QUICK START

### Step 1: Install Dependencies
```bash
source .venv/bin/activate
pip install streamlit plotly
```

### Step 2: Run the Trading System
```bash
# This generates the data for the dashboard
python run_all.py
```

### Step 3: Launch Dashboard
```bash
# Option A: Using startup script (recommended)
chmod +x start_dashboard.sh
./start_dashboard.sh

# Option B: Direct command
streamlit run dashboard.py
```

### Step 4: Open in Browser
```
http://localhost:8501
```

---

## 📋 DASHBOARD PAGES

### 1. 📈 **Overview** (Main Dashboard)
Shows:
- 💰 Portfolio Value
- 📈 Total P&L (profit/loss)
- 📍 Number of open positions
- ✅ Closed trades count
- 🎯 Today's signals (Buy/Sell/Hold breakdown)
- 📍 Current open positions with entry/exit prices

**Use this for:** Quick status check every morning

---

### 2. 💼 **Portfolio**
Shows:
- Portfolio summary (initial capital, current value, cash, invested)
- 🥧 Sector allocation pie chart
- Detailed position breakdown by:
  - Ticker & sector
  - Entry/current prices
  - Position size & value
  - Unrealized P&L
  - Days held

**Use this for:** Portfolio rebalancing decisions

---

### 3. 🎯 **Today's Signals**
Shows:
- All trading signals generated today
- 🟢 **BUY signals** with confidence scores
- 🟡 **HOLD signals** with active indicators
- 🔴 **SELL signals** with reasoning

**Use this for:** Trading execution decisions

---

### 4. 📉 **Performance Analysis**
Shows:
- Win rate, average wins/losses
- 📊 Equity curve (portfolio value over time)
- Monthly P&L breakdown
- Return metrics vs strategy

**Use this for:** Strategy evaluation

---

### 5. 🔄 **Trade History**
Shows:
- All closed trades with entry/exit details
- Filters: by ticker, trade type (winners/losers), min P&L
- Trade statistics: total trades, winners, losers
- Each trade: entry price, exit price, profit, return %

**Use this for:** Trade analysis & learning

---

## 🔧 SETUP & CONFIGURATION

### Option A: Manual Dashboard (One-time)
```bash
source .venv/bin/activate
streamlit run dashboard.py
```
- Opens at `http://localhost:8501`
- Stop with Ctrl+C

### Option B: Scheduled Dashboard (Background Service)

#### Using systemd (Recommended for EC2):
```bash
# Create service file
sudo tee /etc/systemd/system/johntrading-dashboard.service > /dev/null << 'EOF'
[Unit]
Description=John Trading Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/johntrading
ExecStart=/home/ubuntu/johntrading/.venv/bin/streamlit run dashboard.py --server.port=8501 --logger.level=warning
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable & start
sudo systemctl daemon-reload
sudo systemctl enable johntrading-dashboard.service
sudo systemctl start johntrading-dashboard.service

# Check status
sudo systemctl status johntrading-dashboard.service
```

#### Using Screen (Simple alternative):
```bash
# Start in background
screen -S dashboard -d -m bash -c 'source .venv/bin/activate && streamlit run dashboard.py'

# View
screen -r dashboard

# Detach (keep running)
Ctrl+A, D

# Kill
screen -S dashboard -X quit
```

#### Using Nohup (Simplest):
```bash
# Start
nohup streamlit run dashboard.py > dashboard.log 2>&1 &

# Check
cat dashboard.log

# Kill
pkill -f "streamlit run dashboard.py"
```

---

## 📱 ACCESSING DASHBOARD

### Local Machine
```
http://localhost:8501
```

### Remote EC2
```
http://YOUR-EC2-IP:8501
```

### Through SSH Tunnel (Secure)
```bash
# On your local machine:
ssh -i your-key.pem -L 8501:localhost:8501 ubuntu@YOUR-EC2-IP

# Then visit:
http://localhost:8501
```

---

## 🔄 AUTO-REFRESH DASHBOARD

The dashboard automatically detects changes to:
- `phase6_paper_trade/paper_portfolio.json` (portfolio state)
- `phase4_signals/latest_signals.json` (today's signals)
- Trade history in portfolio JSON

### For Real-time Updates:
1. **Run trading system on schedule** (cron or systemd)
2. **Dashboard refreshes** when portfolio changes
3. **Use browser refresh** for manual updates

### Example: Daily Auto-Update
```bash
# Schedule trading system at 4 PM UTC
crontab -e

# Add:
0 16 * * * cd ~/johntrading && source .venv/bin/activate && python run_all.py
0 17 * * * pkill -f "streamlit run dashboard.py"  # Restart to reload data
```

---

## 📊 DATA SOURCES

Dashboard pulls from:

| Page | Data Source | File |
|------|------------|------|
| Overview | Portfolio + Signals | `phase6_paper_trade/paper_portfolio.json` |
| Portfolio | Portfolio positions | `phase6_paper_trade/paper_portfolio.json` |
| Today's Signals | Trading signals | `phase4_signals/latest_signals.json` |
| Performance | Closed trades | `phase6_paper_trade/paper_portfolio.json` |
| Trade History | Trade logs | `phase6_paper_trade/paper_portfolio.json` |

---

## 🎨 CUSTOMIZATION

### Change Dashboard Port
```bash
streamlit run dashboard.py --server.port=9000
```

### Change Colors/Theme
Edit `dashboard.py` CSS section (lines 35-56):
```python
# Change these colors to customize
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
```

### Add Favicon/Title
Already configured! Shows "📊 John Trading Dashboard"

---

## 🐛 TROUBLESHOOTING

### Issue: "Portfolio data not found"
```bash
# First, run the trading system
python run_all.py

# Then reload dashboard (Ctrl+R in browser)
```

### Issue: "ImportError: No module named 'streamlit'"
```bash
source .venv/bin/activate
pip install streamlit plotly
```

### Issue: Port already in use
```bash
# Find process using port 8501
lsof -i :8501

# Kill it
kill -9 <PID>

# Or use different port
streamlit run dashboard.py --server.port=8502
```

### Issue: Dashboard doesn't refresh
```bash
# Clear browser cache
Ctrl+Shift+Delete

# Option 2: Hard refresh
Ctrl+Shift+R

# Option 3: Incognito mode
Ctrl+Shift+N
```

### Issue: Charts not showing
```bash
# Reinstall plotly
pip install --upgrade plotly

# Restart dashboard
```

---

## 📈 DASHBOARD WORKFLOW

### Morning (9 AM)
1. Open dashboard
2. Check "Overview" for overnight signals
3. Review portfolio allocation on "Portfolio"
4. Check "Today's Signals" for trading opportunities

### Pre-Market (3 PM UTC)
1. Review "Performance Analysis" for strategy health
2. Check open positions on "Portfolio"
3. Plan trades based on signals

### Afternoon (After Market Close)
1. Trading system runs at 4 PM UTC (automated)
2. New signals appear in "Today's Signals"
3. Closed trades appear in "Trade History"
4. Review equity curve in "Performance Analysis"

### Weekly
1. Review "Trade History" for lessons learned
2. Check win rate and average trade size
3. Compare "Performance Analysis" metrics

---

## 🔌 INTEGRATION WITH TRADING SYSTEM

### Real-time Usage
```bash
# Terminal 1: Trading pipeline (runs daily)
while true; do
  python run_all.py
  sleep 86400  # Wait 24 hours
done

# Terminal 2: Dashboard (always on)
streamlit run dashboard.py
```

### With Cron Scheduling
```bash
# Add to crontab
# 4 PM UTC: Run trading system
0 16 * * * cd ~/johntrading && source .venv/bin/activate && python run_all.py

# Dashboard: Runs constantly via systemd
sudo systemctl start johntrading-dashboard.service
```

---

## 📱 Mobile Access

### From Mobile Phone on Same Network
```
http://YOUR-EC2-IP:8501
```

### From Anywhere (via SSH Tunnel)
```bash
# On your phone, use SSH client to local machine
# Then access http://localhost:8501
```

### Mobile-Friendly View
Dashboard is responsive! Use browser zoom to fit to screen.

---

## ⚡ PERFORMANCE NOTES

- **First load:** 2-3 seconds (reads JSON files)
- **Subsequent loads:** <500ms (browser cache)
- **With large trade history (1000+ trades):** 5-10 seconds

**To speed up:**
- Clear browser cache regularly
- Use "Trade History" filters to reduce data
- Archive old trades (separate JSON file)

---

## 🔐 SECURITY

### Dashboard is NOT password protected by default

To add password protection:
```bash
# Use SSH tunnel (recommended)
ssh -i your-key.pem -L 8501:localhost:8501 ubuntu@YOUR-EC2-IP

# Only expose port 8501 to specific IPs
sudo ufw allow from YOUR.IP.ADDRESS to any port 8501
```

### Don't expose port 8501 to the internet!

---

## 📚 NEXT STEPS

1. **Run full pipeline:** `python run_all.py`
2. **Start dashboard:** `./start_dashboard.sh`
3. **Open browser:** `http://localhost:8501`
4. **Explore pages:** Overview → Portfolio → Signals → Analysis
5. **Set up auto-refresh:** Use systemd or cron
6. **Monitor daily:** Check Overview page each morning

---

## 🆘 NEED HELP?

Check dashboard logs:
```bash
# If running as service
sudo journalctl -u johntrading-dashboard.service -f

# If running in screen
screen -r dashboard
```

Check trading system logs:
```bash
tail -f logs/trading.log
tail -f logs/errors.log
```

---

**Dashboard Ready! 🚀**

Start with: `streamlit run dashboard.py`
