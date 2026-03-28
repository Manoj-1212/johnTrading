# Production Deployment Guide - Automated 24/7 Trading

## Overview

This guide walks you through setting up automated 24/7 trading on your AWS EC2 server. The system will:

✅ Start automatically on boot
✅ Wait until 9:30 AM EST (market open)
✅ Trade automatically during market hours (9:30 AM - 4 PM EST)
✅ Exit gracefully at market close
✅ Restart automatically the next business day
✅ Log all activity for monitoring

---

## Prerequisites

- ✅ Code deployed to `/home/ubuntu/johntrading/`
- ✅ Virtual environment created: `/home/ubuntu/johntrading/.venv/`
- ✅ `.env` file created with Alpaca API keys
- ✅ All dependencies installed

## Step 1: Verify Setup on Server

SSH into your EC2 instance:

```bash
ssh -i your_key.pem ubuntu@your_instance_ip
cd ~/johntrading
```

### Check .env file exists and has correct keys:

```bash
cat ~/.env  # Should show your APCA_API_KEY_ID and APCA_API_SECRET_KEY
```

Example output:
```
APCA_API_KEY_ID=PK_xxx...
APCA_API_SECRET_KEY=xxx...
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### Test broker connection:

```bash
source .venv/bin/activate
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True, debug=True)
print('✓ Connection successful')
"
```

You should see:
```
✓ Connected to Alpaca (PAPER TRADING)
  Account: ...
  Cash: $25,000.00
  Portfolio Value: $25,000.00
```

---

## Step 2: Run One-Time Deployment Script

This sets up systemd service and scheduling:

```bash
cd ~/johntrading
chmod +x deploy_production.sh
./deploy_production.sh
```

This script:
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Copies systemd service file
- ✅ Sets up daily restart cron job (9:30 AM EST, weekdays only)
- ✅ Configures logging

---

## Step 3: Start the Trading Service

### Option A: Start service now

```bash
sudo systemctl start johntrading
```

### Option B: Enable auto-start on boot AND start now

```bash
sudo systemctl enable johntrading  # Auto-start on reboot
sudo systemctl start johntrading   # Start now
```

### Verify it's running:

```bash
sudo systemctl status johntrading
```

Expected output:
```
● johntrading.service - John Trading System - Automated 24/7 Real-Time Trading
     Loaded: loaded (/etc/systemd/system/johntrading.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-03-28 10:15:00 UTC
```

---

## Step 4: Monitor Logs in Real-Time

### Watch logs as they happen (helpful for testing):

```bash
sudo journalctl -u johntrading -f
```

This will show:
- ✅ Service starting
- ✅ Waiting for market open
- ✅ Signals being generated
- ✅ Trades being executed
- ✅ Session closing at 4 PM

### Example real-time output:

```
Mar 28 10:15:00 ip-172-31-0-1 johntrading[12345]: ================================================================================
Mar 28 10:15:00 ip-172-31-0-1 johntrading[12345]: PRODUCTION AUTOMATED TRADING ENGINE (24/7 Mode)
Mar 28 10:15:00 ip-172-31-0-1 johntrading[12345]: ================================================================================
Mar 28 10:15:05 ip-172-31-0-1 johntrading[12345]: ✓ Market is now OPEN - Starting trading
Mar 28 10:15:10 ip-172-31-0-1 johntrading[12345]: Downloading daily baseline data...
Mar 28 10:15:20 ip-172-31-0-1 johntrading[12345]: ✓ Baseline ready for 20 tickers
Mar 28 10:15:25 ip-172-31-0-1 johntrading[12345]: Starting real-time stream...
Mar 28 10:15:30 ip-172-31-0-1 johntrading[12345]: Trade executed: BUY AAPL @ $150.25
Mar 28 10:15:35 ip-172-31-0-1 johntrading[12345]: Trade executed: SELL MSFT @ $380.50
Mar 28 15:55:00 ip-172-31-0-1 johntrading[12345]: ⏹️  Market closing in 300s - stopping trading
Mar 28 16:00:00 ip-172-31-0-1 johntrading[12345]: ================================================================================
Mar 28 16:00:05 ip-172-31-0-1 johntrading[12345]: SESSION SUMMARY
```

---

## Step 5: Use Monitoring Scripts

I've provided convenient monitoring scripts. Copy them to your server:

### View last 50 log lines:

```bash
./trading_monitor.sh -l 50
```

### Follow logs in real-time:

```bash
./trading_monitor.sh -f
```

### Check service status:

```bash
./trading_monitor.sh -s
```

### Show today's logs:

```bash
./trading_monitor.sh -t
```

### Control service:

```bash
./trading_monitor.sh --stop      # Stop trading
./trading_monitor.sh --start     # Start trading
./trading_monitor.sh --restart   # Restart service
./trading_monitor.sh --enable    # Enable auto-start
./trading_monitor.sh --disable   # Disable auto-start
```

---

## Step 6: Understand How It Works

### Daily Operation:

**Before 9:30 AM EST:**
- Service is running but in "wait" mode
- Checking every 1-2 minutes for market open
- Logs: "Waiting for market open... Market opens in X minutes"

**9:30 AM - 4:00 PM EST (Market hours):**
- Service actively trades
- Streams 1-minute bars
- Generates signals every minute
- Executes trades automatically
- Monitors positions
- Logs every action

**After 4:00 PM EST:**
- Service detects market close
- Exits gracefully with summary
- Waits to be restarted by cron/systemd
- Logs: "Market closed - stopping trading session"

**Overnight & Weekends:**
- Service restarts but enters wait mode
- Waiting for next market open
- Next restart: Monday 9:30 AM EST (if Friday close)

---

## Step 7: Configure Auto-Restart Schedule

The deployment script already sets this up via cron, but to verify:

```bash
crontab -l
```

You should see:
```
30 9 * * 1-5 /usr/bin/systemctl restart johntrading
```

This means:
- **30** = 30th minute (9:30)
- **9** = 9 AM
- **\*** = Every month
- **\*** = Every day
- **1-5** = Monday-Friday only

### To add/modify manually:

```bash
crontab -e
# Add this line:
30 9 * * 1-5 /usr/bin/systemctl restart johntrading
```

---

## Step 8: Monitor Trading Activity

### View all logs for today:

```bash
journalctl -u johntrading --since today
```

### View last 100 lines:

```bash
journalctl -u johntrading -n 100
```

### View with timestamps:

```bash
journalctl -u johntrading -o long-iso
```

### Save logs to file:

```bash
journalctl -u johntrading --since today > trading_logs.txt
```

---

## Step 9: Check Account Status

From your server, check current account balance:

```bash
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True, debug=True)
info = broker.get_account_info()
positions = broker.get_positions()
print(f'Cash: \${info[\"cash\"]:.2f}')
print(f'Portfolio: \${info[\"portfolio_value\"]:.2f}')
print(f'Positions: {len(positions)}')
for p in positions:
    print(f'  {p.symbol}: {p.qty} @ \${p.current_price:.2f}')
"
```

---

## Troubleshooting

### Service won't start

**Check status:**
```bash
sudo systemctl status johntrading
```

**Check recent logs:**
```bash
journalctl -u johntrading -n 50
```

**Common issues:**
- `.env` file missing → Create it with your API keys
- Broker not connected → Check API keys in `.env`
- Python not found → Verify `.venv` exists and has correct permissions
- Permission denied → Run `sudo chown -R ubuntu:ubuntu ~/johntrading`

### Service starts but no trades

**Check if it's waiting for market open:**
```bash
journalctl -u johntrading | grep "Waiting for market"
```

If market is closed, service will sleep until next open.

**During market hours, check for errors:**
```bash
journalctl -u johntrading -f
```

Look for "ERROR", "BLOCKED", or "WARNING" messages.

### Check process is running:

```bash
ps aux | grep run_phase9_production
```

Should show the Python process running.

### View system resource usage:

```bash
top -p $(pgrep -f run_phase9_production)
```

Should show Python using < 50% CPU, < 512 MB RAM.

---

## Safe Testing (Recommended)

Before running 24/7, test for at least 1 hour:

```bash
# Run for 1 market hour to verify signals/trades
./johntrading.service  # Or: sudo systemctl start johntrading

# Monitor closely
journalctl -u johntrading -f

# Check one trade executed
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True)
orders = broker.get_orders(status='closed', limit=5)
print(f'Recent trades: {len(orders)}')
for o in orders:
    print(f'  {o.symbol}: {o.side.name} ${o.filled_avg_price:.2f}')
"

# Stop if something looks wrong
sudo systemctl stop johntrading
```

---

## Switching to Live Trading (Advanced)

⚠️ **Only after 2+ weeks of successful paper trading!**

### Update .env file:

```bash
nano ~/.env
# Change APCA_API_BASE_URL from:
APCA_API_BASE_URL=https://paper-api.alpaca.markets
# To:
APCA_API_BASE_URL=https://api.alpaca.markets
```

### Update trading mode:

```bash
sudo nano /etc/systemd/system/johntrading.service
# Change this line:
Environment="TRADING_MODE=paper"
# To:
Environment="TRADING_MODE=live"
```

### Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart johntrading
```

### Verify it's in LIVE mode:

```bash
journalctl -u johntrading | grep "LIVE TRADING"
```

---

## Daily Operations Checklist

**Every Morning (Before 9:30 AM EST):**
- [ ] Check service is running: `systemctl status johntrading`
- [ ] No errors in logs: `journalctl -u johntrading`

**During Market Hours (9:30 AM - 4 PM EST):**
- [ ] Monitor logs for trades: `journalctl -u johntrading -f`
- [ ] Verify signals are generating
- [ ] Check no "ERROR" messages

**After Market Close (After 4 PM EST):**
- [ ] Service should have exited gracefully
- [ ] Check final session summary in logs
- [ ] Note any issues for next day

**Weekly:**
- [ ] Review log files for patterns
- [ ] Check portfolio P&L: `python check_account.py`
- [ ] Verify cron job is scheduled: `crontab -l`

---

## Summary

Your automated trading system is now:

✅ Running 24/7 on EC2
✅ Waiting for market open automatically
✅ Trading during market hours automatically
✅ Closing positions at market close
✅ Restarting automatically next business day
✅ Logging all activity
✅ Self-healing on crashes (auto-restart policy)

**Next:** Monitor logs for 2-3 days to ensure everything works as expected!

```bash
# Watch it in action:
journalctl -u johntrading -f
```

---

**Questions?** Check logs, restart service, or review this guide!
