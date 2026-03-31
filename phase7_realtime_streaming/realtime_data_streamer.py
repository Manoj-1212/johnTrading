"""
Phase 7: Real-Time Data Streaming for Intraday Trading
Streams 1-minute bars during market hours (9:30 AM - 4 PM EST)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import pytz

class RealtimeDataStreamer:
    """
    Streams real-time 1-minute OHLCV data during market hours.
    
    Features:
    - Streams 1-minute bars from market open (9:30 AM EST) to close (4 PM EST)
    - Maintains rolling 200-bar window for indicator calculations
    - Caches intraday data to avoid excessive API calls
    - Automatically switches to previous day's data during pre-market
    
    Usage:
        streamer = RealtimeDataStreamer(config)
        for bar_data in streamer.stream_live(tickers, duration_minutes=180):
            print(f"Received bar: {bar_data}")
    """
    
    def __init__(self, config, debug=False):
        self.config = config
        self.debug = debug
        self.est = pytz.timezone('US/Eastern')
        self.utc = pytz.UTC
        self.cache_dir = Path('phase7_realtime_streaming/data_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tickers_data = {}
        
    def is_market_open(self):
        """Check if US stock market is currently open"""
        now = datetime.now(self.est)
        
        # Market hours: 9:30 AM - 4:00 PM EST, Monday-Friday
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if it's a weekday (0 = Monday, 4 = Friday)
        is_weekday = now.weekday() < 5
        
        is_open = is_weekday and market_open <= now <= market_close
        
        if self.debug:
            print(f"[{now.strftime('%H:%M:%S')}] Market open: {is_open}")
        
        return is_open
    
    def get_next_market_open(self):
        """Get next market open time (9:30 AM EST)"""
        now = datetime.now(self.est)
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # If already past market close today, start tomorrow
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if now > market_close:
            next_open += timedelta(days=1)
        # If before market open today, set to today's open
        elif now < next_open and now.weekday() < 5:
            pass  # Keep today's open time
        else:
            # Weekend or past market hours
            next_open += timedelta(days=1)
        
        # Skip weekends
        while next_open.weekday() > 4:  # 5 = Saturday, 6 = Sunday
            next_open += timedelta(days=1)
        
        return next_open
    
    def download_daily_base(self, tickers):
        """
        Download daily data to establish baseline and previous day's close.
        Used for initial indicator warm-up.
        
        Downloads each ticker individually with retry logic to avoid yfinance API failures.
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading daily data baseline...")
        
        # Get 6 months of daily data for indicators warm-up
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        failed_tickers = []
        successful_tickers = []
        
        # Download each ticker individually with retry logic
        for i, ticker in enumerate(tickers):
            max_retries = 3
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    if self.debug:
                        print(f"  [{i+1}/{len(tickers)}] Downloading {ticker}...")
                    
                    # Download daily data for this ticker
                    data = yf.download(
                        ticker,
                        start=start_date,
                        end=end_date,
                        interval='1d',
                        progress=False
                    )
                    
                    # Verify we got valid data
                    if data is not None and not data.empty and len(data) > 10:
                        # Ensure we have required columns
                        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                        if all(col in data.columns for col in required_cols):
                            self.tickers_data[ticker] = data[required_cols]
                            successful_tickers.append(ticker)
                            success = True
                            if self.debug:
                                print(f"  ✓ {ticker}: {len(data)} bars")
                        else:
                            raise ValueError(f"Missing required columns for {ticker}")
                    else:
                        raise ValueError(f"Empty or insufficient data for {ticker}")
                        
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Wait before retry (exponential backoff)
                        wait_time = 2 ** retry_count  # 2s, 4s, 8s
                        if self.debug:
                            print(f"  ⚠ {ticker} failed (attempt {retry_count}/{max_retries}): {str(e)[:100]}")
                            print(f"    Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        # All retries exhausted
                        failed_tickers.append(ticker)
                        print(f"✗ Failed to download {ticker} after {max_retries} attempts")
            
            # Small delay between requests to avoid rate limiting
            if i < len(tickers) - 1:
                time.sleep(0.5)
        
        # Summary
        print(f"\n✓ Downloaded daily data for {len(successful_tickers)}/{len(tickers)} tickers")
        if failed_tickers:
            print(f"✗ Failed: {failed_tickers}")
            print(f"  Note: System will continue with available tickers. Monitor logs for failures.")
        
        return self.tickers_data
    
    def get_1min_bars_today(self, ticker, num_bars=200):
        """
        Get 1-minute bars from today's session up to current time.
        Returns latest num_bars bars for indicator calculation.
        
        Uses cache when available, with retry logic for API failures.
        """
        # Check cache first
        cache_file = self.cache_dir / f"{ticker}_1min_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if cache_file.exists():
            try:
                # Read CSV without explicit date parsing (to avoid pandas warnings)
                cached_df = pd.read_csv(cache_file, index_col=0)
                
                # Ensure index is datetime
                cached_df.index = pd.to_datetime(cached_df.index, errors='coerce')
                
                # Remove any rows with NaT index (failed parsing)
                cached_df = cached_df[cached_df.index.notna()]
                
                if len(cached_df) > 0:
                    if self.debug:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {ticker} from cache: {len(cached_df)} bars")
                    return cached_df.tail(num_bars)
            except Exception as e:
                if self.debug:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Cache read error for {ticker}: {e}, falling back to API")
        
        # Download today's 1-minute bars with retry logic
        now = datetime.now()
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                data = yf.download(
                    ticker,
                    start=now.date(),
                    interval='1m',
                    progress=False
                )
                
                if data is not None and not data.empty:
                    # Verify data has required columns
                    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if all(col in data.columns for col in required_cols):
                        # Cache the data
                        try:
                            data.to_csv(cache_file)
                        except Exception as cache_err:
                            if self.debug:
                                print(f"  Cache write error for {ticker}: {cache_err}")
                        
                        if self.debug:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloaded {ticker}: {len(data)} bars")
                        
                        return data.tail(num_bars)
                    else:
                        raise ValueError(f"Missing required columns for {ticker}")
                else:
                    # Empty data - maybe market hasn't started today
                    if self.debug:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No 1-min data yet for {ticker}")
                    return pd.DataFrame()
                    
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    if self.debug:
                        print(f"  ⚠ {ticker} 1-min download failed (attempt {retry_count}/{max_retries}): {str(e)[:80]}")
                        print(f"    Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"✗ Failed to get 1-min bars for {ticker} after {max_retries} attempts")
                    return pd.DataFrame()
    
    def stream_live(self, tickers, update_interval_seconds=60, duration_minutes=390):
        """
        Stream 1-minute bars during market hours.
        
        Args:
            tickers: List of stock tickers to stream
            update_interval_seconds: How often to fetch new bars (default 60 = 1 minute)
            duration_minutes: Total duration to stream (390 = full market day)
        
        Yields:
            dict with keys: {'timestamp', 'ticker', 'bars': DataFrame}
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting live stream for {len(tickers)} tickers")
        print(f"Update interval: {update_interval_seconds}s, Duration: {duration_minutes} minutes")
        
        # Download daily baseline data first
        self.download_daily_base(tickers)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        bar_count = 0
        last_update_times = {ticker: None for ticker in tickers}
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now(self.est)
                
                # Check if market is open
                if not self.is_market_open():
                    if self.debug:
                        print(f"[{current_time.strftime('%H:%M:%S')}] Market closed, sleeping...")
                    time.sleep(30)  # Sleep 30 seconds before checking again
                    continue
                
                # Stream data for each ticker
                for ticker in tickers:
                    try:
                        bars = self.get_1min_bars_today(ticker, num_bars=200)
                        
                        if not bars.empty:
                            # Check if we have new data since last update
                            current_last_time = bars.index[-1]
                            
                            if last_update_times[ticker] != current_last_time:
                                last_update_times[ticker] = current_last_time
                                bar_count += 1
                                
                                yield {
                                    'timestamp': current_time,
                                    'ticker': ticker,
                                    'bars': bars,
                                    'current_price': bars['Close'].iloc[-1],
                                    'bar_time': current_last_time,
                                    'bar_count': bar_count
                                }
                                
                                if self.debug:
                                    print(f"[{current_time.strftime('%H:%M:%S')}] {ticker}: "
                                          f"${bars['Close'].iloc[-1]:.2f} (V: {bars['Volume'].iloc[-1]:,.0f})")
                    
                    except Exception as e:
                        print(f"Error streaming {ticker}: {e}")
                        continue
                
                # Sleep before next update
                time.sleep(update_interval_seconds)
                
        except KeyboardInterrupt:
            print(f"\nStream stopped by user")
        except Exception as e:
            print(f"Stream error: {e}")
            raise
        
        print(f"Stream completed. Total bars: {bar_count}")

    def get_previous_day_close(self, ticker):
        """Get yesterday's close price for comparison"""
        try:
            if ticker in self.tickers_data and not self.tickers_data[ticker].empty:
                return self.tickers_data[ticker]['Close'].iloc[-1]
        except:
            pass
        return None


if __name__ == "__main__":
    # Example usage
    from trading_new_config import TICKERS, LOOKBACK
    
    config = {
        'tickers': TICKERS[:3],  # Test with first 3 tickers
        'lookback': LOOKBACK
    }
    
    streamer = RealtimeDataStreamer(config, debug=True)
    
    # Stream for 10 minutes
    count = 0
    for bar_data in streamer.stream_live(config['tickers'], duration_minutes=10):
        count += 1
        print(f"Bar {count}: {bar_data['ticker']} at {bar_data['timestamp']}")
        
        if count >= 10:  # Stop after 10 bars for testing
            break
