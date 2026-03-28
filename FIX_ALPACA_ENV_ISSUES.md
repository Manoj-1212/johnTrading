# Fix: Alpaca API & .env Configuration Issues

## Problem Summary

Your deployment encountered two issues:

1. **systemd EnvironmentFile format error**: The `.env` file contains shell syntax (`export`, `$()`) which systemd doesn't support
2. **Alpaca API parameter error**: `TradingClient` doesn't accept `base_url` parameter in current alpaca-py

## Errors You Saw

```
Ignoring invalid environment assignment 'export INSTANCE_TYPE=...': /home/ubuntu/johntrading/.env
Error connecting to Alpaca: TradingClient.__init__() got an unexpected keyword argument 'base_url'
```

## Solution

### Step 1: Fix the `.env` File Format

systemd's `EnvironmentFile` directive **does NOT support**:
- `export` keyword
- Shell variables like `$VAR` or `$(command)`
- Shell commands like `echo`

**Old (wrong):**
```bash
export APCA_API_KEY_ID="YOUR_KEY"
export APCA_API_BASE_URL="https://paper-api.alpaca.markets"
export DEPLOYMENT_DATE=$(date -u +'%Y-%m-%d %H:%M:%S UTC')
```

**New (correct - systemd format):**
```
APCA_API_KEY_ID=YOUR_KEY
APCA_API_SECRET_KEY=YOUR_SECRET
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### Step 2: Update Your `.env` File on EC2

SSH to your EC2 instance and update the file:

```bash
# SSH into your instance
ssh ubuntu@your_instance_ip

# Go to trading directory
cd ~/johntrading

# Backup old .env
cp .env .env.backup

# Create new .env (copy the systemd-compatible format below)
cat > .env << 'EOF'
APCA_API_KEY_ID=your_api_key_here
APCA_API_SECRET_KEY=your_secret_key_here
APCA_API_BASE_URL=https://paper-api.alpaca.markets
MIN_SIGNALS=5
STOP_LOSS=0.07
TAKE_PROFIT=0.15
MAX_HOLDING_DAYS=20
PAPER_CAPITAL=10000
POSITION_SIZE_PCT=20
TICKERS=AAPL,MSFT,NVDA,TSLA,AMZN,GOOGL,NFLX,META,UBER,COIN
BENCHMARK=VOO
LOG_LEVEL=INFO
DEBUG=false
TRADING_MODE=paper
EOF

# Verify file content (no 'export' keywords!)
cat .env

# Fix permissions
chmod 600 .env

# Verify systemd can read it
systemctl cat johntrading | grep EnvironmentFile
```

### Step 3: Restart the Service

```bash
# Stop the service
sudo systemctl stop johntrading

# Reload systemd (reads updated .env)
sudo systemctl daemon-reload

# Start the service
sudo systemctl start johntrading

# Check if it started successfully
sudo systemctl status johntrading

# Monitor logs (should see "Connected to Alpaca" now)
journalctl -u johntrading -f
```

### Step 4: Verify the Fix

You should see logs like:
```
✓ Connected to Alpaca (PAPER TRADING)
Market is OPEN - Starting trading...
```

**NOT** these errors:
```
Ignoring invalid environment assignment 'export ...'
Error connecting to Alpaca: TradingClient.__init__() got an unexpected keyword argument 'base_url'
```

## Key Files Updated

### 1. `phase8_broker_integration/alpaca_broker_interface.py` ✅ FIXED
- Removed: `base_url=base_url` parameter
- Now: Uses `APCA_API_BASE_URL` environment variable automatically
- alpaca-py will read: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `APCA_API_BASE_URL` from environment

### 2. `.env.systemd` ✅ NEW
- Systemd-compatible environment file format
- Copy from: `c:\xampp\htdocs\trading_new\.env.systemd`
- Use as template for your `/home/ubuntu/johntrading/.env`

### 3. `deploy_production.sh` (needs update)
- Should be updated to validate .env format
- Should strip `export` keywords if present

## Environment Variable Reference

These are the ONLY variables systemd will load from `.env`:

```
APCA_API_KEY_ID=your_api_key_id
APCA_API_SECRET_KEY=your_secret_key
APCA_API_BASE_URL=https://paper-api.alpaca.markets  (or https://api.alpaca.markets for live)
```

All other variables (MIN_SIGNALS, STOP_LOSS, etc.) are optional and read by the Python scripts at runtime.

## What NOT to Do

❌ Don't use `export` in the .env file  
❌ Don't use `$()` command substitution  
❌ Don't use shell variable interpolation like `$VAR`  
❌ Don't use `echo` or other commands  

systemd's EnvironmentFile is **NOT a shell script** - it's a simple KEY=VALUE format.

## Paper vs Live Trading

**Paper Trading (Default - Recommended for Testing):**
```
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```
- No real money
- Unlimited practice
- Use this for first 2+ weeks

**Live Trading (Production Only):**
```
APCA_API_BASE_URL=https://api.alpaca.markets
```
- Real money
- Be very careful!
- Verify working in paper mode first

## Next Steps

1. ✅ Code fixed (alpaca-py compatibility)
2. ✅ New .env.systemd template provided
3. → **YOU:** Update `.env` on EC2 (remove `export`, use `KEY=VALUE` format)
4. → **YOU:** Restart service and verify logs

Once you complete step 3-4, your trading system should connect to Alpaca and start trading!

## Testing Checklist

Before live trading, verify each of these in the logs:

- [ ] Service starts without "Ignoring invalid environment assignment" warnings
- [ ] Logs show "✓ Connected to Alpaca (PAPER TRADING)"
- [ ] Logs show "Market is OPEN - Starting trading" during market hours
- [ ] Logs show actual trades: "Trade executed: BUY AAPL @ $150.25"
- [ ] Position P&L is tracked
- [ ] Session summary appears at market close
- [ ] Service restarts correctly next morning

Once all tests pass, you can confidently run in live trading mode.

## Still Having Issues?

### Issue: "Ignoring invalid environment assignment" still appears

**Cause:** Your .env file still has `export` keyword or shell syntax

**Fix:**
```bash
# Check your .env file
cat /home/ubuntu/johntrading/.env

# Should output ONLY:
# APCA_API_KEY_ID=xxx
# APCA_API_SECRET_KEY=xxx
# ... (no 'export' keyword, no $(), etc.)

# If it has 'export', remove them:
sed -i 's/^export //' /home/ubuntu/johntrading/.env

# Reload systemd
sudo systemctl daemon-reload
```

### Issue: "unexpected keyword argument 'base_url'"

**Cause:** Your code still has the old alpaca_broker_interface.py

**Fix:**
```bash
# Pull latest code from GitHub
cd ~/johntrading
git pull origin master

# This brings in the fixed alpaca_broker_interface.py
```

### Issue: "Cannot connect to Alpaca"

**Debug:**
```bash
# Check if environment variables are loaded
grep APCA /home/ubuntu/johntrading/.env

# Check if alpaca-py is installed
pip list | grep alpaca

# Test connection manually
python3 -c "
from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
broker = AlpacaBrokerInterface(paper_trading=True, debug=True)
"
```

## References

- Alpaca API Docs: https://docs.alpaca.markets/
- alpaca-py GitHub: https://github.com/alpacahq/alpaca-py
- systemd EnvironmentFile Docs: https://www.freedesktop.org/software/systemd/man/systemd.exec.html
