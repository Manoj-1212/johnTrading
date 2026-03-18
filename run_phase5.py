"""
run_phase5.py — Phase 5 Review & Rule Optimization
Analyzes backtest results and suggests improvements
"""

import pandas as pd
import os
from phase2_indicators.combiner import SIGNAL_COLS
from config import TICKERS


def main():
    print("\n" + "="*100)
    print("🔵 PHASE 5: REVIEW & OPTIMIZATION")
    print("="*100)
    
    # Load backtest results
    results_dir = "phase3_backtest/results"
    if not os.path.exists(results_dir):
        print(f"\n❌ No backtest results found. Run Phase 3 first.")
        return False
    
    print("\n[STEP 1] Analyzing backtest results...\n")
    
    # Load metrics
    metrics_path = os.path.join(results_dir, "backtest_metrics.csv")
    if not os.path.exists(metrics_path):
        print(f"❌ Metrics file not found: {metrics_path}")
        return False
    
    metrics = pd.read_csv(metrics_path)
    
    # Display best performers
    print("="*100)
    print("PERFORMANCE RANKING")
    print("="*100)
    
    if 'alpha' in metrics.columns:
        ranking = metrics.sort_values('alpha', ascending=False, na_position='last')
        print("\n" + ranking[['ticker', 'total_return_pct', 'voo_return_pct', 'alpha', 'win_rate', 'sharpe_ratio']].to_string(index=False))
    
    # Analysis
    print("\n" + "="*100)
    print("ANALYSIS & OBSERVATIONS")
    print("="*100)
    
    print(f"\n📊 Total Tickers Analyzed: {len(metrics)}")
    print(f"   • Avg Alpha: {metrics['alpha'].mean():.2f}%")
    print(f"   • Avg Win Rate: {metrics['win_rate'].mean():.1f}%")
    print(f"   • Avg Total Return: {metrics['total_return_pct'].mean():.2f}%")
    
    # Outperformers
    outperformers = metrics[metrics['alpha'] > 5]
    if not outperformers.empty:
        print(f"\n✅ OUTPERFORMERS (Alpha > 5%):")
        for _, row in outperformers.iterrows():
            print(f"   • {row['ticker']}: +{row['alpha']:.2f}% alpha")
    else:
        print(f"\n⚠️  No tickers beating VOO by 5%+")
    
    # Recommendations
    print("\n" + "="*100)
    print("RECOMMENDATIONS FOR IMPROVEMENT")
    print("="*100)
    
    print("""
1. INDICATOR TUNING
   • Test different EMA periods (40/150, 50/250, etc.)
   • Adjust RSI boundaries (20/80 vs 30/70 vs 45/65)
   • Vary ATR and Volume thresholds

2. ENTRY CRITERIA OPTIMIZATION
   • Current: MIN_SIGNALS_TO_BUY = 5
   • Try: 4/7 or 6/7 to balance sensitivity vs specificity
   • Adjust mandatory signal combinations

3. RISK MANAGEMENT
   • Current: STOP_LOSS_PCT = 7%, TAKE_PROFIT_PCT = 15%
   • Test: 5%/-10% or 10%/-20% strategies
   • Vary HOLDING_PERIOD_MAX (currently 20 days)

4. TECHNICAL PATTERNS
   • Elliott Wave: Needs refinement for noisy daily candles
   • Fibonacci: Consider longer lookback periods
   • Regression: Test different slopes/angles

5. PORTFOLIO STRATEGY
   • Test position sizing: Equal-weight vs Risk-parity
   • Add correlation filtering (don't hold correlated stocks)
   • Implement sector rotation
""")
    
    print("="*100)
    print("✅ Phase 5 complete!")
    print("   Recommendations saved above\n")
    print("="*100 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
