"""
run_phase3.py — Phase 3 Backtesting Execution
Runs historical backtest for all tickers and compares against VOO
"""

import pandas as pd
import os
from phase1_data.downloader import StockDownloader
from phase2_indicators.combiner import build_full_indicator_set, SIGNAL_COLS
from phase3_backtest.engine import BacktestEngine
from phase3_backtest.metrics import calculate_metrics
from config import TICKERS, BENCHMARK


def main():
    print("\n" + "="*120)
    print("🟠 PHASE 3: BACKTEST FRAMEWORK")
    print("="*120)
    
    # Step 1: Load data
    print("\n[STEP 1] Loading cached data...")
    dl = StockDownloader()
    data = dl.load_from_cache()
    
    valid_tickers = [t for t in data.keys() if not data[t].empty]
    print(f"✅ Loaded {len(valid_tickers)} tickers")
    
    # Step 2: Generate indicators for all tickers
    print("\n[STEP 2] Calculating indicators...")
    indicator_data = {}
    for ticker in valid_tickers:
        df = build_full_indicator_set(data[ticker])
        # Drop warmup period
        indicator_data[ticker] = df.iloc[100:].copy()
    
    print(f"✅ Indicators calculated for {len(indicator_data)} tickers")
    
    # Step 3: Run backtest for each ticker
    print("\n[STEP 3] Running backtest...")
    backtest_results = {}
    
    for ticker in TICKERS:
        if ticker not in indicator_data:
            print(f"   [{ticker}] SKIPPED (no data)")
            continue
        
        print(f"   [{ticker}] Running backtest...")
        engine = BacktestEngine()
        trades_df, equity_curve = engine.run(indicator_data[ticker], ticker)
        
        backtest_results[ticker] = {
            'trades': trades_df,
            'equity': equity_curve,
            'engine': engine
        }
    
    # Step 4: Generate VOO benchmark equity curve
    print("\n[STEP 4] Generating VOO benchmark...")
    if BENCHMARK in indicator_data:
        # Calculate simple buy-and-hold return for VOO
        voo_df = data[BENCHMARK]
        voo_return = voo_df['Close'].iloc[-1] / voo_df['Close'].iloc[0]
        voo_equity = pd.Series(
            index=voo_df.index[100:],
            data=(voo_df['Close'].iloc[100:] / voo_df['Close'].iloc[100]) * 10_000,
            dtype=float
        )
        print(f"✅ VOO buy-and-hold return: {(voo_return-1)*100:.2f}%")
    else:
        voo_equity = pd.Series(dtype=float)
    
    # Step 5: Calculate metrics for each ticker
    print("\n[STEP 5] Calculating metrics...")
    metrics_data = []
    
    for ticker in TICKERS:
        if ticker not in backtest_results:
            continue
        
        result = backtest_results[ticker]
        trades = result['trades']
        equity = result['equity']
        
        metrics = calculate_metrics(trades, equity, voo_equity)
        metrics['ticker'] = ticker
        metrics_data.append(metrics)
    
    # Step 6: Display results table
    print("\n" + "="*120)
    print("BACKTEST RESULTS COMPARISON vs VOO")
    print("="*120)
    
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        
        # Reorder columns for readability
        display_cols = ['ticker', 'total_trades', 'win_rate', 'avg_return', 'total_return_pct', 
                       'voo_return_pct', 'alpha', 'sharpe_ratio', 'max_drawdown']
        display_cols = [c for c in display_cols if c in metrics_df.columns]
        
        print("\n" + metrics_df[display_cols].to_string(index=False))
        
        # Summary by alpha
        print("\n" + "="*120)
        print("RANKING BY ALPHA (Strategy Return - VOO Return)")
        print("="*120)
        ranking = metrics_df.sort_values('alpha', ascending=False)[['ticker', 'total_return_pct', 'voo_return_pct', 'alpha']]
        print("\n" + ranking.to_string(index=False))
        
        # Identify outperformers
        outperformers = metrics_df[metrics_df['alpha'] > 5]
        if not outperformers.empty:
            print(f"\n🎯 OUTPERFORMERS (Alpha > 5%): {outperformers['ticker'].tolist()}")
        else:
            print(f"\n⚠️  No tickers beating VOO by 5%+ yet")
    
    # Step 7: Save detailed results
    print("\n[STEP 6] Saving backtest results...")
    os.makedirs("phase3_backtest/results", exist_ok=True)
    
    for ticker in TICKERS:
        if ticker not in backtest_results:
            continue
        
        trades = backtest_results[ticker]['trades']
        if not trades.empty:
            trades.to_csv(f"phase3_backtest/results/{ticker}_trades.csv", index=False)
    
    # Save metrics summary
    if metrics_data:
        metrics_df.to_csv("phase3_backtest/results/backtest_metrics.csv", index=False)
        print(f"✅ Saved backtest results to phase3_backtest/results/")
    
    print("\n" + "="*120)
    print("✅ Phase 3 complete!")
    print("   Ready to proceed to Phase 4: Signal Generation\n")
    print("="*120 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
