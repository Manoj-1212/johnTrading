"""
run_phase6.py — Phase 6 Paper Trading Status
Display current paper trading portfolio status and performance
"""

import pandas as pd
from phase1_data.downloader import StockDownloader
from phase4_signals.signal_generator import SignalGenerator
from phase6_paper_trade.portfolio import PaperPortfolio
from config import TICKERS


def main():
    print("\n" + "="*100)
    print("💼 PHASE 6: PAPER TRADING STATUS")
    print("="*100)
    
    # Load data
    print("\n[STEP 1] Loading latest data...")
    dl = StockDownloader()
    data = dl.load_from_cache()
    
    # Load portfolio
    print("[STEP 2] Loading paper portfolio...")
    portfolio = PaperPortfolio()
    
    # Get current prices
    current_prices = {}
    for ticker in TICKERS:
        if ticker in data and not data[ticker].empty:
            current_prices[ticker] = float(data[ticker]['Close'].iloc[-1])
    
    # Display portfolio summary
    summary = portfolio.summary(current_prices)
    
    print("\n" + "="*100)
    print("PORTFOLIO SUMMARY")
    print("="*100)
    print(f"\nStarting Capital: ${10_000:.2f}")
    print(f"Current Value: ${summary['portfolio_value']:.2f}")
    print(f"Total Return: {summary['total_return_pct']:+.2f}%")
    print(f"Available Cash: ${summary['cash']:.2f}")
    print(f"Open Positions: {summary['open_positions']}")
    print(f"Closed Trades: {summary['trades_closed']}")
    
    # Display open positions
    if portfolio.positions:
        print("\n" + "="*100)
        print("OPEN POSITIONS")
        print("="*100)
        
        positions_data = []
        for ticker, pos in portfolio.positions.items():
            current_price = current_prices.get(ticker, pos['entry_price'])
            unrealized_pnl = (current_price - pos['entry_price']) / pos['entry_price'] * 100
            
            positions_data.append({
                'Ticker': ticker,
                'Shares': f"{pos['shares']:.2f}",
                'Entry': f"${pos['entry_price']:.2f}",
                'Current': f"${current_price:.2f}",
                'Unrealized P&L': f"{unrealized_pnl:+.2f}%",
            })
        
        positions_df = pd.DataFrame(positions_data)
        print("\n" + positions_df.to_string(index=False))
    else:
        print(f"\n💤 No open positions")
    
    # Display trade history
    if portfolio.trade_history:
        print("\n" + "="*100)
        print("TRADE HISTORY (Last 10 closed trades)")
        print("="*100)
        
        trades = portfolio.trade_history[-10:]
        trades_df = pd.DataFrame(trades)
        print("\n" + trades_df.to_string(index=False))
    else:
        print(f"\n📝 No closed trades yet")
    
    # Generate current signals and EXECUTE TRADES
    print("\n" + "="*100)
    print("TODAY'S SIGNALS - EXECUTING TRADES")
    print("="*100)
    
    today_date = str(pd.Timestamp.now().date())
    executions = []
    
    for ticker in TICKERS:
        if ticker not in data or data[ticker].empty:
            continue
        
        signal = SignalGenerator.generate(data[ticker], ticker)
        current_price = float(data[ticker]['Close'].iloc[-1])
        
        # EXECUTE BUY SIGNALS
        if signal['action'] == 'BUY' and ticker not in portfolio.positions:
            result = portfolio.open_position(ticker, current_price, today_date, current_prices)
            if result:
                executions.append(('BUY', ticker, current_price, "✅ EXECUTED"))
        
        # EXECUTE SELL SIGNALS
        elif signal['action'] == 'SELL' and ticker in portfolio.positions:
            pnl_pct = portfolio.close_position(ticker, current_price, today_date, current_prices)
            executions.append(('SELL', ticker, current_price, f"✅ EXECUTED ({pnl_pct:+.1f}%)"))
    
    # Display executions
    if executions:
        print(f"\n📊 TRADES EXECUTED ({len(executions)}):")
        for action, ticker, price, status in executions:
            emoji = "🟢" if action == "BUY" else "🔴"
            print(f"   {emoji} {action} {ticker} @ ${price:.2f} | {status}")
    else:
        print(f"\n📊 TRADES EXECUTED: None")
    
    # Show any pending open signals
    buy_signals = []
    for ticker in TICKERS:
        if ticker not in data or data[ticker].empty:
            continue
        
        signal = SignalGenerator.generate(data[ticker], ticker)
        if signal['action'] == 'BUY' and ticker not in portfolio.positions:
            buy_signals.append((ticker, signal['signal_count'], signal['price']))
    
    if buy_signals:
        print(f"\n🟢 OPEN SIGNALS (Monitoring - no new positions yet) ({len(buy_signals)}):")
        for ticker, sig_count, price in sorted(buy_signals, key=lambda x: x[1], reverse=True):
            print(f"   • {ticker} @ ${price:.2f} ({sig_count} signals)")
    
    print("\n" + "="*100)
    print("✅ Phase 6 complete!")
    print("   Trades executed | Portfolio updated\n")
    print("="*100 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
