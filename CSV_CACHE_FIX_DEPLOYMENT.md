## CSV Cache Fix - Deployment Guide

**Problem Identified**: CSV cache files had malformed date formats, causing silent parse failures.
- All signals showing: `HOLD | LOW | Strength: 1 | Price: $0.00`
- Root cause: `pd.read_csv(..., parse_dates=True)` failing silently on line 169

**What Was Fixed**:

### 1. Improved CSV Parsing (realtime_data_streamer.py)
```python
# Now uses:
- parse_dates=True
- infer_datetime_format=True  ← NEW (auto-detects date format)
- Explicit DatetimeIndex validation
- Better error handling with fallback to API
```

### 2. Cache Cleanup Script (fix_data_cache.py)
- Backs up corrupted cache
- Force-downloads fresh 5-year daily data for all 21 tickers
- Verifies all CSV files are readable
- Re-creates cache with proper format

### 3. Deployment Script (deploy_cache_fix.sh)
- Stops trading service
- Pulls latest code
- Clears old cache
- Runs cache cleanup
- Restarts service
- Shows live logs

---

## EC2 Deployment Steps

### Option A: Quick Automated Deploy
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Navigate to trading directory
cd ~/johntrading

# Download and run deployment script
git pull origin master
bash deploy_cache_fix.sh
```

### Option B: Manual Deploy
```bash
# 1. Stop service
sudo systemctl stop johntrading

# 2. Pull latest code
cd ~/johntrading
git pull origin master

# 3. Clear bad cache
rm -rf phase7_realtime_streaming/cache
mkdir -p phase7_realtime_streaming/cache

# 4. Download fresh data
python3 fix_data_cache.py

# 5. Restart service
sudo systemctl start johntrading

# 6. Watch logs for signals
journalctl -u johntrading -f
```

---

## Expected Logs After Fix

### ✅ Before (Broken):
```
[15:27:25] ✓ Downloaded daily data for 21/21 tickers
[15:27:25] ➡️ AAPL | HOLD | LOW | $ 0.00 | Strength: 1
[15:27:25] ➡️ MSFT | HOLD | LOW | $ 0.00 | Strength: 1
Cache read error: Could not infer format, so each element will be parsed individually
```

### ✅ After (Fixed):
```
[15:35:10] ✓ Downloaded daily data for 21/21 tickers
[15:35:12] ✓ Loaded AAPL from cache: 390 bars
[15:35:12] ✓ Loaded MSFT from cache: 390 bars
[15:35:15] ✓ AAPL | BUY | HIGH | $150.25 | Strength: 6/7
[15:35:15] ✓ MSFT | SELL | MEDIUM | $380.00 | Strength: 5/7
[15:35:16] ✓ Executing BUY order: 6 × AAPL @ $150.25
[15:35:18] ✓ Trade executed: BUY AAPL @ $150.25
```

---

## What Changed

### Files Modified:
1. **phase7_realtime_streaming/realtime_data_streamer.py** (Line 169)
   - Enhanced CSV parsing with date format inference

2. **NEW: fix_data_cache.py**
   - Utility to backup and re-download fresh data

3. **NEW: deploy_cache_fix.sh**
   - Automated deployment script for EC2

### Code Changes Summary:
```diff
- cached_df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
+ cached_df = pd.read_csv(
+     cache_file, 
+     index_col=0, 
+     parse_dates=True,
+     infer_datetime_format=True  ← Auto-detect date format
+ )
+ # Ensure index is datetime
+ if not isinstance(cached_df.index, pd.DatetimeIndex):
+     cached_df.index = pd.to_datetime(cached_df.index)
```

---

## GitHub Commits

- **0a432a3**: Fix CSV date parsing and add cache cleanup script
- **b265144**: Add EC2 deployment script for cache fix
- **f6cf3a8**: Fix indicator calculation Series bugs and CSV date parsing (CRITICAL)

Latest: `git log --oneline | head -5`

### Latest Critical Fix (f6cf3a8)
Fixes the "truth value of a Series is ambiguous" error by:
- Fixing Series comparison in volume ratio check
- Fixing RSI calculation dividing Series objects
- Ensuring all calculations use scalar values
- Removing deprecated pandas parameter
- Adding proper CSV date format handling

---

## Troubleshooting

### If trades still don't execute after deploy:

1. **Check cache loaded properly**:
   ```bash
   ls -lah ~/johntrading/phase7_realtime_streaming/cache/
   # Should show 21 .csv files, each 10KB+
   ```

2. **Check CSV file validity**:
   ```bash
   python3 -c "
   import pandas as pd
   df = pd.read_csv('phase7_realtime_streaming/cache/AAPL.csv', index_col=0, parse_dates=True)
   print(f'Rows: {len(df)}, Latest: {df.index[-1]}')
   "
   ```

3. **Check service logs for errors**:
   ```bash
   journalctl -u johntrading -n 50  # Last 50 lines
   ```

4. **Restart with debug enabled**:
   ```bash
   # Edit run_phase9_production.py, set debug=True
   # Then sudo systemctl restart johntrading
   ```

---

## Success Criteria

After deployment, you should see:
- ✅ 21/21 tickers downloading daily
- ✅ Cache loading successfully (messages: "Loaded X from cache: ### bars")
- ✅ Signals with strength > 1 (not all HOLD)
- ✅ Proper prices (not $0.00)
- ✅ BUY/SELL actions (not just HOLD)
- ✅ Trade execution logs

---

## Questions?

- **Logs not showing signals?** → Check `/var/log/syslog` or `journalctl -u johntrading -n 100`
- **Cache still empty?** → Backup directory: `cache_backup_YYYYMMDD_HHMMSS/`
- **API timeouts?** → Fix script has retry logic, wait 5 min and restart

