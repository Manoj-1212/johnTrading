# 🚀 Production Deployment Checklist - 24/7 Automated Trading

## What You Need to Do on Your Server

### Current Status:
✅ Code deployed to server
✅ .env file created with API keys
✅ Now: Set up automation

---

## Quick Setup (10 minutes)

### Step 1: SSH to Your Server

```bash
ssh -i your_key.pem ubuntu@your_instance_ip
cd ~/johntrading
```

### Step 2: Run Deployment Script

```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

**What it does:**
- ✅ Installs Python dependencies
- ✅ Sets up systemd service
- ✅ Configures daily restart schedule
- ✅ Creates logging directory

**Output should end with:**
```
✅ Deployment Setup Complete!
```

### Step 3: Start the Service

```bash
sudo systemctl start johntrading
sudo systemctl enable johntrading  # Auto-start on reboot
```

### Step 4: Verify It's Working

```bash
# Check status
sudo systemctl status johntrading

# Watch logs
journalctl -u johntrading -f
```

You should see:
```
Market opens in X hours - sleeping
```

**Done!** 🎉 System is now running and will auto-trade during market hours.

---

## What Happens Next

### Before 9:30 AM EST:
```
Service running → Waiting for market open...
Checking every 1-2 minutes
```

### 9:30 AM - 4 PM EST (Market Hours):
```
✓ Market is OPEN - Starting trading
Downloading daily baseline...
Starting real-time stream...
[BUY signals] [SELL signals] [Risk checks] [Trade execution]
Trade executed: BUY AAPL @ $150.25
Trade executed: SELL MSFT @ $380.50
...
```

### 4 PM EST (Market Close):
```
Market closed - stopping trading session
SESSION SUMMARY
P&L: $X.XX
Service waits for next market open
```

---

## Monitoring Commands

### Watch logs in real-time:
```bash
journalctl -u johntrading -f
```

### Check status:
```bash
sudo systemctl status johntrading
```

### View last 50 lines:
```bash
journalctl -u johntrading -n 50
```

### View today's logs:
```bash
journalctl -u johntrading --since today
```

### Check account:
```bash
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
b = AlpacaBrokerInterface(paper_trading=True)
i = b.get_account_info()
print(f'Cash: \${i[\"cash\"]:.2f}, Portfolio: \${i[\"portfolio_value\"]:.2f}')
"
```

---

## Control Commands

### Stop trading:
```bash
sudo systemctl stop johntrading
```

### Start trading:
```bash
sudo systemctl start johntrading
```

### Restart:
```bash
sudo systemctl restart johntrading
```

### Disable auto-start:
```bash
sudo systemctl disable johntrading
```

### Enable auto-start:
```bash
sudo systemctl enable johntrading
```

---

## Key Files

| File | Purpose |
|------|---------|
| `run_phase9_production.py` | Main automated trading engine (waits for market, trades during hours, exits at close) |
| `johntrading.service` | systemd service configuration (auto-start, restart policy) |
| `deploy_production.sh` | One-time setup script (install deps, configure systemd, setup cron) |
| `trading_monitor.sh` | Simple monitoring tool (check status, view logs, control service) |
| `.env` | Your API keys (created by you) |

---

## How It Works (Technical)

### Automatic Daily Schedule:

**Using cron + systemd:**
```
Cron job (9:30 AM daily):
  └─→ systemctl restart johntrading

Service starts:
  └─→ Python run_phase9_production.py
      ├─→ Check market hours
      ├─→ If market closed: WAIT
      ├─→ If market open: TRADE
      │   ├─→ Stream 1-min bars
      │   ├─→ Calculate indicators
      │   ├─→ Generate signals
      │   ├─→ Check risk limits
      │   └─→ Execute trades via Alpaca
      └─→ At 4 PM: EXIT gracefully
          └─→ systemd will restart service
             (it will then enter WAIT mode)
```

### Recovery:

If service crashes:
- ✅ systemd automatically restarts it
- ✅ If it crashes 5+ times in 1 hour, stops trying
- ✅ Cron will restart it tomorrow at 9:30 AM

---

## Troubleshooting

### "Command not found: systemctl"
- Not available on your system
- Run `sudo apt-get install systemd` if needed
- Or use screen/tmux method instead (see below)

### "Service won't start"
- Check .env file exists: `cat ~/.env`
- Check permissions: `sudo chown -R ubuntu:ubuntu ~/johntrading`
- Check Python path: `which python3`

### "No trades being executed"
- If before 9:30 AM: System is waiting (normal)
- If during 9:30-4 PM: Check for errors in logs
- Check Alpaca API keys in .env are correct

### "Connection refused"
- Broker not connected
- Verify .env has correct API keys
- Test connection: `python test_broker.py`

---

## Alternative: Manual Screen Session (No systemd)

If systemd doesn't work, use screen instead:

```bash
# Create a screen session
screen -S trading

# Inside screen:
cd ~/johntrading
source .venv/bin/activate
python run_phase9_production.py

# Detach from screen: Ctrl+a then d
# Reattach: screen -r trading
# Kill: screen -S trading -X quit
```

---

## Expected Daily Behavior

### Perfect Day:

```
09:30 Market opens
09:31 [LOG] ✓ Market is OPEN - Starting trading
09:32 [LOG] Downloading daily baseline...
09:35 [LOG] Starting real-time stream...
09:36 [LOG] Trade executed: BUY AAPL @ $150.25
10:14 [LOG] Trade executed: SELL MSFT @ $382.50
... more trades ...
15:55 [LOG] ⏹️ Market closing in 300s - stopping trading
16:00 [LOG] SESSION SUMMARY - P&L: $150.00
16:00 [LOG] Service exited gracefully
```

### What to Monitor:

- ✅ Service starts at 9:30 AM (or next market open)
- ✅ Signals generate every minute
- ✅ Trades execute (usually 5-10 per day)
- ✅ No "ERROR" messages in logs
- ✅ Service exits cleanly at 4 PM

---

## Next Steps

1. ✅ **Run deployment script** (5 min)
   ```bash
   ./deploy_production.sh
   ```

2. ✅ **Start service** (1 min)
   ```bash
   sudo systemctl start johntrading
   sudo systemctl enable johntrading
   ```

3. ✅ **Monitor for 1-2 days** (read logs)
   ```bash
   journalctl -u johntrading -f
   ```

4. ✅ **Verify trades are executing** (check Alpaca account)
   ```bash
   # Login to app.alpaca.markets to see trades
   ```

5. ✅ **Consider live trading** (after 2+ weeks of paper trading)
   ```bash
   # Update .env: APCA_API_BASE_URL=https://api.alpaca.markets
   # Update service: TRADING_MODE=live
   ```

---

## Support

### Check Everything Works:

```bash
#!/bin/bash
# Test everything

echo "1. Checking .env file..."
cat ~/.env | grep APCA

echo "2. Checking service..."
systemctl status johntrading

echo "3. Checking logs..."
journalctl -u johntrading -n 5

echo "4. Checking broker connection..."
python -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
try:
    b = AlpacaBrokerInterface(paper_trading=True)
    print('✓ Broker connected')
except Exception as e:
    print(f'✗ Broker error: {e}')
"

echo "5. Checking market hours..."
python -c "
from run_phase9_production import MarketHours
if MarketHours.is_market_open():
    print('✓ Market is OPEN')
else:
    sec = MarketHours.time_to_market_open()
    print(f'Market opens in {sec//3600}h {(sec%3600)//60}m')
"

echo "Done!"
```

Save as `test_everything.sh` and run:
```bash
chmod +x test_everything.sh
./test_everything.sh
```

---

## Summary

**You now have:**

✅ 24/7 automated trading on EC2
✅ Automatic market hours detection
✅ Real-time data streaming (1-min bars)
✅ Automatic signal generation
✅ Automatic trade execution via Alpaca
✅ Portfolio-level risk management
✅ Full logging and monitoring
✅ Auto-restart on crashes
✅ Daily reset via cron

**System Status:** 🟢 Operating

**Your action:** Run deployment script and start service!

---

**Questions? Check logs:** `journalctl -u johntrading -f`
