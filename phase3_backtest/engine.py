"""
phase3_backtest/engine.py — Backtest Engine
Simulates trading based on indicator signals with position and trade tracking
"""

import pandas as pd
import numpy as np
from config import (MIN_SIGNALS_TO_BUY, MANDATORY_SIGNALS,
                    HOLDING_PERIOD_MAX, STOP_LOSS_PCT, TAKE_PROFIT_PCT)


class BacktestEngine:
    """Backtests trading strategy using indicator signals."""
    
    def __init__(self):
        self.trades = []

    def run(self, df: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, pd.Series]:
        """
        Run backtest on a single ticker.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with indicator signals (including signal_count, mandatory_ok columns)
        ticker : str
            Ticker symbol for logging
        
        Returns
        -------
        tuple[pd.DataFrame, pd.Series]
            trades_df: DataFrame of all closed trades with metrics
            equity: Series of portfolio value over time
        """
        df = df.dropna(subset=['Close']).copy()
        
        in_trade = False
        entry_price = 0.0
        entry_date = None
        hold_days = 0
        
        # Track equity curve
        equity = pd.Series(index=df.index, dtype=float)
        capital = 10_000.0
        equity.iloc[0] = capital
        
        for i, (date, row) in enumerate(df.iterrows()):
            if i == 0:
                continue
            
            price = row['Close']
            
            if in_trade:
                hold_days += 1
                pnl_pct = (price - entry_price) / entry_price
                
                exit_reason = None
                
                # Check exit conditions
                if pnl_pct <= -STOP_LOSS_PCT:
                    exit_reason = 'stop_loss'
                elif pnl_pct >= TAKE_PROFIT_PCT:
                    exit_reason = 'take_profit'
                elif hold_days >= HOLDING_PERIOD_MAX:
                    exit_reason = 'max_hold'
                elif row['signal_count'] < 3:
                    exit_reason = 'signal_exit'
                
                if exit_reason:
                    # Exit trade
                    capital *= (1 + pnl_pct)
                    self.trades.append({
                        'ticker': ticker,
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': price,
                        'return_pct': round(pnl_pct * 100, 2),
                        'hold_days': hold_days,
                        'exit_reason': exit_reason,
                        'signal_count': int(row['signal_count']),
                    })
                    in_trade = False
                    hold_days = 0
            
            else:
                # Check entry conditions
                signal_count = int(row.get('signal_count', 0))
                mandatory_ok = bool(row.get('mandatory_ok', False))
                
                buy_signal = (
                    mandatory_ok and
                    signal_count >= MIN_SIGNALS_TO_BUY
                )
                
                if buy_signal:
                    in_trade = True
                    entry_price = price
                    entry_date = date
                    hold_days = 0
            
            equity[date] = capital
        
        # Close any open trade at the end
        if in_trade:
            final_price = df['Close'].iloc[-1]
            final_pnl = (final_price - entry_price) / entry_price
            capital *= (1 + final_pnl)
            self.trades.append({
                'ticker': ticker,
                'entry_date': entry_date,
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'return_pct': round(final_pnl * 100, 2),
                'hold_days': hold_days,
                'exit_reason': 'end_of_data',
                'signal_count': int(df['signal_count'].iloc[-1]),
            })
        
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        equity = equity.ffill()
        
        return trades_df, equity
