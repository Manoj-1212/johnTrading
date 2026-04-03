"""
run_phase10_train.py — Train the ML Trade Filter
=================================================
Trains XGBoost model on historical data to filter false BUY signals.

Usage:
    python run_phase10_train.py

What it does:
1. Loads historical data for all tickers
2. Calculates all 7 indicators
3. Builds features (RSI, MACD, EMA, BB, volume, price momentum, volatility)
4. Target: Did price go up >1% in next 5 bars?
5. Trains XGBoost with time-series cross-validation
6. Saves model to phase10_ml/model.joblib

Run this BEFORE starting paper trading (run_phase9.py).
Re-run monthly to retrain on latest data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from phase1_data.downloader import StockDownloader
from phase2_indicators.combiner import build_full_indicator_set
from phase10_ml.ml_filter import MLTradeFilter
from config import TICKERS


def main():
    print("\n" + "=" * 80)
    print("PHASE 10: ML TRADE FILTER TRAINING")
    print("=" * 80)
    
    # Step 1: Load cached data
    print("\n[STEP 1] Loading historical data...")
    dl = StockDownloader()
    data = dl.load_from_cache()
    
    valid_tickers = [t for t in TICKERS if t in data and not data[t].empty]
    print(f"Loaded {len(valid_tickers)} tickers")
    
    # Step 2: Calculate indicators
    print("\n[STEP 2] Calculating indicators for all tickers...")
    indicator_data = {}
    for ticker in valid_tickers:
        df = build_full_indicator_set(data[ticker])
        indicator_data[ticker] = df.iloc[200:].copy()  # Drop warmup period
        print(f"  {ticker}: {len(indicator_data[ticker])} bars")
    
    # Step 3: Train ML model
    print("\n[STEP 3] Training ML model...")
    ml_filter = MLTradeFilter()
    avg_auc = ml_filter.train(indicator_data, verbose=True)
    
    if avg_auc and avg_auc > 0.5:
        print(f"\n{'=' * 80}")
        print(f"TRAINING COMPLETE")
        print(f"{'=' * 80}")
        print(f"Average AUC: {avg_auc:.4f}")
        print(f"Model saved. Ready to use in production.")
        print(f"\nNext step: python run_phase9.py")
    else:
        print(f"\nWARNING: Model AUC is low ({avg_auc:.4f}). May not improve performance.")
        print("Consider: more data, different features, or different target definition.")


if __name__ == '__main__':
    main()
