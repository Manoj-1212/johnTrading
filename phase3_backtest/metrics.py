"""
phase3_backtest/metrics.py — Backtest Metrics Calculator
Calculates performance metrics from backtest results
"""

import pandas as pd
import numpy as np


def calculate_metrics(trades: pd.DataFrame, equity: pd.Series,
                     voo_equity: pd.Series) -> dict:
    """
    Calculate backtest performance metrics.
    
    Parameters
    ----------
    trades : pd.DataFrame
        DataFrame of executed trades
    equity : pd.Series
        Portfolio value over time
    voo_equity : pd.Series
        VOO benchmark value over time (aligned to equity index)
    
    Returns
    -------
    dict
        Dictionary of performance metrics
    """
    if trades.empty:
        return {"error": "No trades generated", "total_trades": 0}
    
    # Trade statistics
    winners = trades[trades['return_pct'] > 0]
    losers = trades[trades['return_pct'] <= 0]
    
    equity = equity.dropna()
    
    # Calculate drawdown
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_drawdown = drawdown.min()
    
    # Sharpe ratio
    daily_returns = equity.pct_change().dropna()
    if daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    # Total return
    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
    
    # VOO comparison (align dates)
    aligned_voo = voo_equity.reindex(equity.index).ffill()
    if len(aligned_voo) > 0 and not aligned_voo.empty:
        voo_return = (aligned_voo.iloc[-1] / aligned_voo.iloc[0] - 1) * 100
        alpha = total_return - voo_return
    else:
        voo_return = 0
        alpha = 0
    
    # Profit factor
    if not losers.empty and losers['return_pct'].sum() != 0:
        profit_factor = winners['return_pct'].sum() / abs(losers['return_pct'].sum())
    else:
        profit_factor = float('inf') if not winners.empty else 0
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(winners),
        'losing_trades': len(losers),
        'win_rate': round(len(winners) / len(trades) * 100, 1) if len(trades) > 0 else 0,
        'avg_return': round(trades['return_pct'].mean(), 2),
        'avg_win': round(winners['return_pct'].mean(), 2) if not winners.empty else 0,
        'avg_loss': round(losers['return_pct'].mean(), 2) if not losers.empty else 0,
        'profit_factor': round(profit_factor, 2),
        'max_drawdown': round(max_drawdown * 100, 2),
        'sharpe_ratio': round(sharpe, 2),
        'total_return_pct': round(total_return, 2),
        'voo_return_pct': round(voo_return, 2),
        'alpha': round(alpha, 2),
    }
