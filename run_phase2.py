"""
run_phase2.py — Phase 2 execution script
Calculate all 7 indicators and generate signal summary
"""

import pandas as pd
from phase1_data.downloader import StockDownloader
from phase2_indicators.combiner import build_full_indicator_set, SIGNAL_COLS


def main():
    print("\n" + "="*100)
    print("🟡 PHASE 2: INDICATOR CALCULATION & SIGNAL GENERATION")
    print("="*100)
    
    # Step 1: Load cached data from Phase 1
    print("\n[STEP 1] Loading data from Phase 1...")
    dl = StockDownloader()
    data = dl.load_from_cache()
    
    valid_tickers = [t for t in data.keys() if not data[t].empty]
    print(f"✅ Loaded {len(valid_tickers)} tickers")
    
    # Step 2: Calculate indicators for each ticker
    print("\n[STEP 2] Calculating all 7 indicators...")
    results = {}
    
    for ticker in valid_tickers:
        print(f"\n   [{ticker}] Processing {len(data[ticker])} bars...")
        
        df = build_full_indicator_set(data[ticker])
        
        # Drop the warmup period (first 100 bars for accuracy)
        df_valid = df.iloc[100:].copy()
        
        results[ticker] = df_valid
        
        # Show sample of indicators at the end
        latest = df_valid.iloc[-1]
        print(f"        Last bar ({df_valid.index[-1].date()}):")
        print(f"        - Signal count: {int(latest['signal_count'])}/7")
        print(f"        - Composite score: {latest['composite_score']:.2f}")
        print(f"        - Mandatory OK (Elliott+Fib): {latest['mandatory_ok']}")
    
    # Step 3: Display summary statistics
    print("\n" + "="*100)
    print("INDICATOR STATISTICS (across all valid tickers, latest bar)")
    print("="*100)
    
    summary_data = []
    for ticker in valid_tickers:
        latest = results[ticker].iloc[-1]
        active_signals = [s for s in SIGNAL_COLS if latest[s]]
        
        summary_data.append({
            'Ticker': ticker,
            'Bars': len(results[ticker]),
            'Signal Count': int(latest['signal_count']),
            'Composite Score': f"{latest['composite_score']:.2f}",
            'Mandatory OK': "✅" if latest['mandatory_ok'] else "❌",
            'Active Signals': ', '.join([s.replace('_signal', '') for s in active_signals])
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Step 4: Show today's signal recommendations
    print("\n" + "="*100)
    print("TODAY'S SIGNAL STATUS")
    print("="*100)
    
    from config import MIN_SIGNALS_TO_BUY
    
    buy_candidates = []
    hold_candidates = []
    sell_candidates = []
    
    for ticker in valid_tickers:
        latest = results[ticker].iloc[-1]
        
        if latest['mandatory_ok'] and latest['signal_count'] >= MIN_SIGNALS_TO_BUY:
            buy_candidates.append((ticker, int(latest['signal_count'])))
        elif latest['signal_count'] <= 2:
            sell_candidates.append((ticker, int(latest['signal_count'])))
        else:
            hold_candidates.append((ticker, int(latest['signal_count'])))
    
    if buy_candidates:
        print(f"\n🟢 BUY SIGNALS ({len(buy_candidates)}):")
        for ticker, sig_count in sorted(buy_candidates, key=lambda x: x[1], reverse=True):
            print(f"   • {ticker}: {sig_count} signals active")
    else:
        print(f"\n🟢 BUY SIGNALS: None")
    
    if hold_candidates:
        print(f"\n🟡 HOLD SIGNALS ({len(hold_candidates)}):")
        for ticker, sig_count in sorted(hold_candidates, key=lambda x: x[1], reverse=True):
            print(f"   • {ticker}: {sig_count} signals active")
    else:
        print(f"\n🟡 HOLD SIGNALS: None")
    
    if sell_candidates:
        print(f"\n🔴 SELL SIGNALS ({len(sell_candidates)}):")
        for ticker, sig_count in sorted(sell_candidates, key=lambda x: x[1]):
            print(f"   • {ticker}: {sig_count} signals active")
    else:
        print(f"\n🔴 SELL SIGNALS: None")
    
    # Step 5: Save results
    print("\n[STEP 3] Saving indicator results...")
    import os
    os.makedirs("phase2_data", exist_ok=True)
    
    for ticker in valid_tickers:
        results[ticker].to_csv(f"phase2_data/{ticker}_indicators.csv")
    
    print(f"✅ Saved {len(valid_tickers)} indicator files to phase2_data/")
    
    print("\n" + "="*100)
    print("✅ Phase 2 complete!")
    print("   Ready to proceed to Phase 3: Backtesting\n")
    print("="*100 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
