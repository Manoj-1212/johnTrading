#!/usr/bin/env python3
"""
Fix corrupted data cache and re-download fresh data
Run on EC2: python3 fix_data_cache.py
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Tickers
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
           'JPM', 'JNJ', 'XOM', 'WMT', 'PG',
           'META', 'TSLA', 'GE', 'AMD', 'INTC',
           'BA', 'GS', 'V', 'NFLX', 'ADBE', 'PLTR']

cache_dir = Path('phase7_realtime_streaming/cache')

print("=" * 80)
print("FIXING DATA CACHE")
print("=" * 80)

# Step 1: Backup old cache
if cache_dir.exists():
    backup_dir = cache_dir.parent / f'cache_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    print(f"\n1️⃣  Backing up old cache to {backup_dir}...")
    shutil.move(str(cache_dir), str(backup_dir))
    print(f"   ✓ Backup complete")

# Step 2: Create fresh cache directory
cache_dir.mkdir(parents=True, exist_ok=True)
print(f"\n2️⃣  Created fresh cache directory: {cache_dir}")

# Step 3: Download fresh daily data for each ticker
print(f"\n3️⃣  Downloading fresh daily data (5 years)...")
successful = 0
failed = []

for i, ticker in enumerate(TICKERS, 1):
    try:
        print(f"   [{i}/{len(TICKERS)}] Downloading {ticker}...", end='', flush=True)
        
        # Download 5 years of daily bars
        data = yf.download(
            ticker,
            start='2021-01-01',
            end=datetime.now().strftime('%Y-%m-%d'),
            interval='1d',
            progress=False,
            timeout=10
        )
        
        if data.empty:
            print(f" ✗ (no data)")
            failed.append(ticker)
        else:
            # Ensure proper format
            data.index = pd.to_datetime(data.index)
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            # Save to cache
            cache_file = cache_dir / f'{ticker}.csv'
            data.to_csv(cache_file)
            print(f" ✓ ({len(data)} bars)")
            successful += 1
            
    except Exception as e:
        print(f" ✗ ({str(e)[:30]})")
        failed.append(ticker)

print(f"\n4️⃣  Download Summary:")
print(f"   ✓ Successful: {successful}/{len(TICKERS)}")
if failed:
    print(f"   ✗ Failed: {', '.join(failed)}")

# Step 5: Verify cache
print(f"\n5️⃣  Verifying cache...")
cache_files = list(cache_dir.glob('*.csv'))
print(f"   ✓ Cache files: {len(cache_files)}")

for cache_file in sorted(cache_files)[:5]:  # Show first 5
    try:
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        print(f"      - {cache_file.name}: {len(df)} bars, latest: {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"      - {cache_file.name}: ERROR - {e}")

print("\n" + "=" * 80)
print("✅ CACHE FIX COMPLETE!")
print("=" * 80)
print("\nNext steps:")
print("1. Restart service: sudo systemctl restart johntrading")
print("2. Check logs: journalctl -u johntrading -f")
print("3. Signals should now work properly!")
print("=" * 80)
