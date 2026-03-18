"""
phase1_data/downloader.py — Stock data download and caching
Downloads OHLCV data using yfinance with local CSV caching
"""

import yfinance as yf
import pandas as pd
import os
from config import (TICKERS, BENCHMARK, START_DATE, END_DATE,
                    INTERVAL, DATA_CACHE_DIR, MIN_BARS_REQUIRED)


class StockDownloader:
    """Download and cache stock data from yfinance."""
    
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
        """Download or load cached data for a single ticker."""
        cache_path = f"{DATA_CACHE_DIR}/{ticker}.csv"
        
        if not force_refresh and os.path.exists(cache_path):
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                # Remove any non-numeric columns that might be present
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
                print(f"[CACHE] {ticker}: {len(df)} bars loaded")
                return df
            except Exception:
                pass
        
        try:
            df = yf.download(ticker, start=START_DATE, end=END_DATE,
                             interval=INTERVAL, auto_adjust=True, progress=False)
            
            # Handle MultiIndex columns returned by yfinance
            if isinstance(df.columns, pd.MultiIndex):
                # Extract columns for this ticker (columns are (price_type, ticker) tuples)
                ticker_cols = [col for col in df.columns if col[1] == ticker]
                df_single = df[ticker_cols].copy()
                # Flatten MultiIndex columns to single level
                df_single.columns = [col[0] for col in ticker_cols]
                df = df_single
            
            # Ensure we have the standard OHLCV columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                print(f"[WARNING] {ticker}: Missing columns {missing}")
                return pd.DataFrame()
            
            # Select only OHLCV and convert to numeric
            df = df[required_cols].copy()
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove rows with NaN in OHLCV
            df = df.dropna(subset=required_cols)
            
            # Ensure index is proper datetime with name
            df.index.name = 'Date'
            
            df.to_csv(cache_path)
            print(f"[DOWNLOAD] {ticker}: {len(df)} bars saved")
            return df
        except Exception as e:
            print(f"[ERROR] {ticker}: {type(e).__name__}: {e}")
            return pd.DataFrame()

    def load_from_cache(self) -> dict[str, pd.DataFrame]:
        """Load all cached CSVs without downloading."""
        all_tickers = TICKERS + [BENCHMARK]
        for ticker in all_tickers:
            cache_path = f"{DATA_CACHE_DIR}/{ticker}.csv"
            if os.path.exists(cache_path):
                try:
                    self.data[ticker] = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                    print(f"[CACHE] {ticker}: loaded from disk")
                except Exception as e:
                    print(f"[SKIP] {ticker}: error loading - {e}")
            else:
                print(f"[SKIP] {ticker}: no cache file found")
        return self.data
