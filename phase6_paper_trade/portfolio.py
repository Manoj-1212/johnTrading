"""
phase6_paper_trade/portfolio.py — Paper Trading Portfolio Manager
Tracks paper trading positions and calculates P&L
"""

import json
import os
import pandas as pd
from config import PAPER_CAPITAL, POSITION_SIZE_PCT, MAX_POSITIONS


class PaperPortfolio:
    """Manages paper trading portfolio."""
    
    SAVE_PATH = "phase6_paper_trade/paper_portfolio.json"
    
    def __init__(self):
        self.cash = PAPER_CAPITAL
        self.positions = {}
        self.trade_history = []
        self._ensure_dir()
        self._load()
    
    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.SAVE_PATH), exist_ok=True)
    
    def open_position(self, ticker: str, price: float, date: str) -> bool:
        """
        Open a new position.
        
        Parameters
        ----------
        ticker : str
            Ticker symbol
        price : float
            Entry price
        date : str
            Entry date
        
        Returns
        -------
        bool
            True if position opened, False otherwise
        """
        if len(self.positions) >= MAX_POSITIONS:
            print(f"[SKIP] Max positions ({MAX_POSITIONS}) reached.")
            return False
        
        if ticker in self.positions:
            print(f"[SKIP] Already have position in {ticker}")
            return False
        
        alloc = PAPER_CAPITAL * POSITION_SIZE_PCT
        if self.cash < alloc:
            print(f"[SKIP] Insufficient cash (have ${self.cash:.0f}, need ${alloc:.0f})")
            return False
        
        shares = alloc / price
        self.positions[ticker] = {
            'shares': shares,
            'entry_price': price,
            'entry_date': date
        }
        self.cash -= alloc
        self._save()
        print(f"[BUY] {ticker} @ ${price:.2f} | {shares:.2f} shares | Alloc: ${alloc:.0f}")
        return True
    
    def close_position(self, ticker: str, price: float, date: str) -> float:
        """
        Close an existing position.
        
        Parameters
        ----------
        ticker : str
            Ticker symbol
        price : float
            Exit price
        date : str
            Exit date
        
        Returns
        -------
        float
            Profit/loss percentage, 0 if no position
        """
        if ticker not in self.positions:
            print(f"[SKIP] No position in {ticker}")
            return 0.0
        
        pos = self.positions.pop(ticker)
        proceeds = pos['shares'] * price
        cost = pos['shares'] * pos['entry_price']
        pnl = proceeds - cost
        pnl_pct = (pnl / cost) * 100
        
        self.cash += proceeds
        self.trade_history.append({
            'ticker': ticker,
            'entry_date': pos['entry_date'],
            'exit_date': date,
            'entry_price': pos['entry_price'],
            'exit_price': price,
            'pnl_pct': round(pnl_pct, 2)
        })
        
        self._save()
        print(f"[SELL] {ticker} @ ${price:.2f} | PnL: {pnl_pct:+.2f}%")
        return pnl_pct
    
    def portfolio_value(self, current_prices: dict) -> float:
        """Calculate total portfolio value."""
        equity = self.cash
        for ticker, pos in self.positions.items():
            equity += pos['shares'] * current_prices.get(ticker, pos['entry_price'])
        return equity
    
    def summary(self, current_prices: dict) -> dict:
        """Get portfolio summary."""
        pv = self.portfolio_value(current_prices)
        return {
            'portfolio_value': round(pv, 2),
            'cash': round(self.cash, 2),
            'open_positions': len(self.positions),
            'total_return_pct': round((pv / PAPER_CAPITAL - 1) * 100, 2),
            'trades_closed': len(self.trade_history)
        }
    
    def _save(self):
        """Save portfolio to JSON."""
        self._ensure_dir()
        with open(self.SAVE_PATH, 'w') as f:
            json.dump({
                'cash': self.cash,
                'positions': self.positions,
                'trade_history': self.trade_history
            }, f, indent=2)
    
    def _load(self):
        """Load portfolio from JSON."""
        if os.path.exists(self.SAVE_PATH):
            with open(self.SAVE_PATH) as f:
                data = json.load(f)
            self.cash = data.get('cash', PAPER_CAPITAL)
            self.positions = data.get('positions', {})
            self.trade_history = data.get('trade_history', [])
