"""
COMPREHENSIVE ANALYSIS RUNNER
=============================
Runs all improvement analyses:
1. Sensitivity analysis (threshold impacts)
2. Indicator correlation analysis (redundancy check)
3. Elliott Wave/Fibonacci validation
4. Realistic vs Idealistic backtest comparison
5. Expanded universe validation
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TICKERS, BENCHMARK, MIN_SIGNALS_TO_BUY
from phase1_data.downloader import StockDownloader
from phase1_data.validator import DataValidator
from phase2_indicators.combiner import build_full_indicator_set
from phase2_indicators.sensitivity_analyzer import SensitivityAnalyzer
from phase2_indicators.indicator_analyzer import IndicatorAnalyzer
from phase3_backtest.engine_realistic import BacktestComparator


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n\n{'='*100}")
    print(f"{'║':>50} {title}")
    print(f"{'='*100}\n")


def run_sensitivity_analysis(data: dict):
    """Test parameter sensitivity."""
    print_header("PHASE A: SENSITIVITY ANALYSIS")
    
    analyzer = SensitivityAnalyzer()
    
    print("Testing MIN_SIGNALS_TO_BUY threshold impact...\n")
    results = analyzer.run_parameter_sweep(
        data, 'MIN_SIGNALS_TO_BUY', [3, 4, 5, 6, 7]
    )
    
    print("\n\nTesting STOP_LOSS_PCT threshold impact...\n")
    results = analyzer.run_parameter_sweep(
        data, 'STOP_LOSS_PCT', [0.03, 0.05, 0.07, 0.10, 0.15]
    )
    
    print("\n\nTesting TAKE_PROFIT_PCT threshold impact...\n")
    results = analyzer.run_parameter_sweep(
        data, 'TAKE_PROFIT_PCT', [0.10, 0.15, 0.20, 0.25, 0.30]
    )
    
    print("\n\nGrid search: MIN_SIGNALS × STOP_LOSS × TAKE_PROFIT...\n")
    grid = {
        'MIN_SIGNALS_TO_BUY': [4, 5, 6],
        'STOP_LOSS_PCT': [0.05, 0.07, 0.10],
        'TAKE_PROFIT_PCT': [0.15, 0.20, 0.25],
    }
    best_config = analyzer.run_threshold_grid(data, grid)
    
    return best_config


def run_indicator_analysis(data: dict):
    """Check indicator overlap and redundancy."""
    print_header("PHASE B: INDICATOR CORRELATION & REDUNDANCY ANALYSIS")
    
    # Combine data for analysis
    all_data = pd.DataFrame()
    
    for ticker in [t for t in TICKERS if t in data]:
        df = data[ticker].copy()
        if df.empty:
            continue
        
        df = build_full_indicator_set(df)
        all_data = pd.concat([all_data, df])
    
    analyzer = IndicatorAnalyzer()
    
    print("Analyzing indicator correlation matrix...\n")
    analyzer.print_correlation_analysis(all_data)
    
    print("\n\nAnalyzing signal activation frequencies...\n")
    analyzer.print_activation_frequency(all_data)
    
    print("\n\nAnalyzing signal combinations...\n")
    analyzer.signal_combination_analysis(all_data)
    
    # Create a target: did price go up 1%+ in next 5 bars?
    target = all_data['Close'].pct_change(5) > 0.01
    
    print("\n\nAnalyzing information gain (predicting +1% moves in next 5 bars)...\n")
    analyzer.information_gain_analysis(all_data, target)
    
    print("\n\nFinal recommendation...\n")
    analyzer.recommendation(all_data, target)


def run_pattern_validation(data: dict):
    """Validate Elliott Wave and Fibonacci patterns."""
    print_header("PHASE C: PATTERN VALIDATION (Elliott Wave & Fibonacci)")
    
    from phase2_indicators.elliott_wave_improved import add_elliott_wave_signal_improved
    from phase2_indicators.fibonacci_improved import add_fibonacci_signal_improved
    
    for ticker in ['AAPL', 'MSFT', 'NVDA'][:1]:  # Test on first ticker
        if ticker not in data:
            continue
        
        print(f"\nAnalyzing {ticker} patterns...\n")
        
        df = data[ticker].copy()
        df = add_elliott_wave_signal_improved(df)
        df = add_fibonacci_signal_improved(df)
        
        # Find recent signals
        recent_signals = df[
            (df['elliott_wave_signal'] == True) |
            (df['fibonacci_signal'] == True)
        ].tail(20)
        
        if not recent_signals.empty:
            print(f"Recent pattern signals (last 20 bars):\n")
            for idx, row in recent_signals.iterrows():
                ew_signal = "✓ EW" if row['elliott_wave_signal'] else "  "
                fib_signal = "✓ FIB" if row['fibonacci_signal'] else "    "
                print(f"  {idx.date()} | {ew_signal} {fib_signal} | "
                      f"Price: ${row['Close']:.2f}")
        else:
            print("No recent pattern signals detected.")


def run_realistic_backtest(data: dict):
    """Compare realistic vs idealistic backtest results."""
    print_header("PHASE D: REALISTIC vs IDEALISTIC BACKTEST COMPARISON")
    
    comparator = BacktestComparator()
    
    results_by_ticker = {}
    
    for ticker in ['AAPL', 'MSFT', 'AMZN'][:2]:  # Test on first 2 tickers
        if ticker not in data:
            continue
        
        print(f"Comparing backtest for {ticker}...\n")
        
        df = data[ticker].copy()
        df = build_full_indicator_set(df)
        
        comparison = comparator.compare(df, ticker)
        results_by_ticker[ticker] = comparison
        
        comparator.print_comparison(comparison)
    
    # Summary
    print(f"\n\n{'='*100}")
    print("SUMMARY: Realistic Backtest Impact")
    print(f"{'='*100}\n")
    
    for ticker, comparison in results_by_ticker.items():
        impact = comparison['comparison']['return_impact']
        print(f"{ticker}: {impact:+.2f}% impact from slippage + commissions")


def run_expanded_universe_test(data: dict):
    """Validate strategy on expanded stock universe."""
    print_header("PHASE E: EXPANDED UNIVERSE VALIDATION")
    
    from phase3_backtest.engine import BacktestEngine
    from phase3_backtest.metrics import calculate_metrics
    
    print(f"Testing strategy on {len(TICKERS)} tickers (expanded universe)\n")
    print(f"{'='*80}\n")
    
    results = []
    
    for ticker in TICKERS:
        if ticker not in data or data[ticker].empty:
            print(f"⊘ {ticker:<10} - No data")
            continue
        
        df = data[ticker].copy()
        if len(df) < 300:
            print(f"⊘ {ticker:<10} - Insufficient data ({len(df)} bars)")
            continue
        
        df = build_full_indicator_set(df)
        
        engine = BacktestEngine()
        trades, equity = engine.run(df, ticker)
        
        voo_data = data.get(BENCHMARK, pd.Series())
        aligned_voo = voo_data.reindex(df.index).ffill()
        
        metrics = calculate_metrics(trades, equity, aligned_voo)
        
        result = {
            'ticker': ticker,
            'total_trades': metrics.get('total_trades', 0),
            'win_rate': metrics.get('win_rate', 0),
            'total_return': metrics.get('total_return_pct', 0),
            'voo_return': metrics.get('voo_return_pct', 0),
            'alpha': metrics.get('alpha', 0),
            'sharpe': metrics.get('sharpe_ratio', 0),
        }
        results.append(result)
        
        status = "✓" if result['alpha'] > 0 else "✗"
        print(f"{status} {ticker:<10} | Trades: {result['total_trades']:>3} | "
              f"Return: {result['total_return']:>7.2f}% | "
              f"Alpha: {result['alpha']:>+7.2f}%")
    
    # Summary stats
    results_df = pd.DataFrame(results)
    
    if not results_df.empty:
        print(f"\n{'='*80}\n")
        print(f"UNIVERSE STATISTICS\n")
        print(f"Average alpha:       {results_df['alpha'].mean():+.2f}%")
        print(f"Median alpha:        {results_df['alpha'].median():+.2f}%")
        print(f"Positive alpha:      {(results_df['alpha'] > 0).sum()}/{len(results_df)} tickers")
        print(f"Average win rate:    {results_df['win_rate'].mean():.1f}%")
        print(f"Average return:      {results_df['total_return'].mean():+.2f}%")


def main():
    """Run all analyses."""
    print("\n")
    print("╔" + "="*98 + "╗")
    print("║" + " "*20 + "COMPREHENSIVE TRADING SYSTEM IMPROVEMENTS" + " "*37 + "║")
    print("║" + " "*15 + "Sensitivity Analysis | Pattern Validation | Universe Expansion" + " "*18 + "║")
    print("╚" + "="*98 + "╝")
    
    # Phase 0: Load data
    print("\nLoading and validating data...\n")
    downloader = StockDownloader()
    data = downloader.download_all(force_refresh=False)
    
    validator = DataValidator()
    valid_tickers = validator.validate(data)
    
    if len(valid_tickers) < 2:
        print("❌ Not enough valid data. Exiting.")
        return
    
    # Phase A: Sensitivity Analysis
    try:
        best_config = run_sensitivity_analysis(data)
        print("\n✓ Sensitivity analysis complete")
    except Exception as e:
        print(f"\n⚠️  Sensitivity analysis error: {e}")
    
    # Phase B: Indicator Analysis
    try:
        run_indicator_analysis(data)
        print("\n✓ Indicator analysis complete")
    except Exception as e:
        print(f"\n⚠️  Indicator analysis error: {e}")
    
    # Phase C: Pattern Validation
    try:
        run_pattern_validation(data)
        print("\n✓ Pattern validation complete")
    except Exception as e:
        print(f"\n⚠️  Pattern validation error: {e}")
    
    # Phase D: Realistic Backtest
    try:
        run_realistic_backtest(data)
        print("\n✓ Realistic backtest complete")
    except Exception as e:
        print(f"\n⚠️  Realistic backtest error: {e}")
    
    # Phase E: Expanded Universe
    try:
        run_expanded_universe_test(data)
        print("\n✓ Expanded universe validation complete")
    except Exception as e:
        print(f"\n⚠️  Expanded universe error: {e}")
    
    # Final summary
    print_header("ANALYSIS COMPLETE")
    print("All improvement analyses have been run.")
    print("\nNext steps:")
    print("  1. Review sensitivity analysis results for optimal parameters")
    print("  2. Consider removing redundant indicators per correlation analysis")
    print("  3. Validate Elliott Wave & Fibonacci patterns on your chart")
    print("  4. Compare realistic vs idealistic performance")
    print("  5. Test on expanded universe of tickers")
    print("\nUpdate config.py with best-performing parameters and re-run run_all.py\n")


if __name__ == "__main__":
    main()
