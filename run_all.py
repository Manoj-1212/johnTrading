"""
run_all.py — Master Pipeline Runner
Executes all 6 phases of the trading system in sequence
"""

import subprocess
import sys


def run_phase(phase_num: int, script: str, description: str) -> bool:
    """Run a phase script and handle errors."""
    print(f"\n{'='*120}")
    print(f"Running: {description}")
    print(f"{'='*120}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd=".",
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Phase {phase_num} failed: {e}")
        return False


def main():
    print("\n" + "="*120)
    print("🚀 MULTI-SIGNAL STOCK TRADING SYSTEM - FULL PIPELINE")
    print("="*120)
    print(f"""
This script executes all 6 phases:
  1️⃣  Phase 1: Data Download & Validation
  2️⃣  Phase 2: Indicator Calculation
  3️⃣  Phase 3: Backtesting
  4️⃣  Phase 4: Signal Generation
  5️⃣  Phase 5: Review & Optimization
  6️⃣  Phase 6: Paper Trading Status
""")
    
    phases = [
        (1, "run_phase1.py", "Phase 1 - Data Download & Validation"),
        (2, "run_phase2.py", "Phase 2 - Indicator Calculation"),
        (3, "run_phase3.py", "Phase 3 - Backtesting"),
        (4, "run_phase4.py", "Phase 4 - Signal Generation"),
        (5, "run_phase5.py", "Phase 5 - Review & Optimization"),
        (6, "run_phase6.py", "Phase 6 - Paper Trading Status"),
    ]
    
    for phase_num, script, description in phases:
        if not run_phase(phase_num, script, description):
            print(f"\n⚠️  Phase {phase_num} encountered issues")
            user_input = input("Continue to next phase? (y/n): ").strip().lower()
            if user_input != 'y':
                print(f"\n❌ Pipeline stopped at Phase {phase_num}")
                return False
    
    print("\n" + "="*120)
    print("✅ ALL PHASES COMPLETE!")
    print("="*120)
    print("""
📊 Results Summary:
  • Phase 1: Data downloaded and validated
  • Phase 2: Indicators calculated for all tickers
  • Phase 3: Backtest complete vs VOO benchmark
  • Phase 4: Today's trading signals generated
  • Phase 5: Analysis and recommendations provided
  • Phase 6: Paper portfolio status displayed

📁 Output Files:
  • phase2_data/: Indicator calculations for each ticker
  • phase3_backtest/results/: Backtest trades and metrics
  • phase6_paper_trade/paper_portfolio.json: Paper trading positions

Next Steps:
  1. Review Phase 3 backtest results to assess strategy performance
  2. Implement recommendations from Phase 5
  3. Monitor Phase 4 signals for trading opportunities
  4. Track Phase 6 paper portfolio growth toward 5%+ alpha target
""")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
