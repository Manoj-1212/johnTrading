"""
run_phase4.py — Phase 4 Signal Generation
Generate current trading signals for all tickers
"""

import pandas as pd
from phase1_data.downloader import StockDownloader
from phase4_signals.signal_generator import SignalGenerator
from config import TICKERS


def main():
    print("\n" + "="*100)
    print("🟢 PHASE 4: LIVE SIGNAL GENERATION")
    print("="*100)
    
    # Step 1: Load data
    print("\n[STEP 1] Loading latest data...")
    dl = StockDownloader()
    data = dl.load_from_cache()
    
    # Step 2: Generate signals
    print("\n[STEP 2] Generating signals for all tickers...\n")
    signals = []
    
    for ticker in TICKERS:
        if ticker not in data or data[ticker].empty:
            print(f"   [{ticker}] SKIPPED (no data)")
            continue
        
        signal = SignalGenerator.generate(data[ticker], ticker)
        signals.append(signal)
    
    # Step 3: Display signals organized by action
    print("\n" + "="*100)
    print("TODAY'S TRADING SIGNALS")
    print("="*100)
    
    buy_signals = [s for s in signals if s['action'] == 'BUY']
    hold_signals = [s for s in signals if s['action'] == 'HOLD']
    sell_signals = [s for s in signals if s['action'] == 'SELL']
    
    # BUY SIGNALS
    if buy_signals:
        print(f"\n🟢 BUY SIGNALS ({len(buy_signals)}):")
        for sig in sorted(buy_signals, key=lambda x: x['signal_count'], reverse=True):
            print(f"\n   {sig['ticker']} @ ${sig['price']}")
            print(f"   • Signal Count: {sig['signal_count']}/7")
            print(f"   • Confidence: {sig['confidence']}")
            print(f"   • Active Signals: {', '.join(sig['signals_active'])}")
            if sig['rsi']:
                print(f"   • RSI: {sig['rsi']}")
    else:
        print(f"\n🟢 BUY SIGNALS: None")
    
    # HOLD SIGNALS
    if hold_signals:
        print(f"\n🟡 HOLD SIGNALS ({len(hold_signals)}):")
        for sig in sorted(hold_signals, key=lambda x: x['signal_count'], reverse=True):
            print(f"\n   {sig['ticker']} @ ${sig['price']}")
            print(f"   • Signal Count: {sig['signal_count']}/7")
            print(f"   • Confidence: {sig['confidence']}")
            print(f"   • Active Signals: {', '.join(sig['signals_active'])}")
    else:
        print(f"\n🟡 HOLD SIGNALS: None")
    
    # SELL SIGNALS
    if sell_signals:
        print(f"\n🔴 SELL SIGNALS ({len(sell_signals)}):")
        for sig in sorted(sell_signals, key=lambda x: x['signal_count']):
            print(f"\n   {sig['ticker']} @ ${sig['price']}")
            print(f"   • Signal Count: {sig['signal_count']}/7")
            print(f"   • Confidence: {sig['confidence']}")
            print(f"   • Active Signals: {', '.join(sig['signals_active'])}")
    else:
        print(f"\n🔴 SELL SIGNALS: None")
    
    # Summary table
    print("\n" + "="*100)
    print("SIGNAL SUMMARY TABLE")
    print("="*100)
    
    summary_data = []
    for sig in signals:
        summary_data.append({
            'Ticker': sig['ticker'],
            'Price': f"${sig['price']}",
            'Action': sig['action'],
            'Signals': f"{sig['signal_count']}/7",
            'Confidence': sig['confidence'],
            'Mandatory': "✅" if sig['mandatory_ok'] else "❌",
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    print("\n" + "="*100)
    print("✅ Phase 4 complete! Signals updated\n")
    print("="*100 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
