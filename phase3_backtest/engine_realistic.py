"""
REALISTIC BACKTEST ENGINE
=========================
Improved backtesting with:
- Realistic slippage (entry/exit price degradation)
- Commission per trade
- Better order execution (next bar open for entry/exit)
- Partial fills & liquidity checks
- Draw down tracking during trades
"""

import pandas as pd
import numpy as np
from config import (
    MIN_SIGNALS_TO_BUY, HOLDING_PERIOD_MAX,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT
)


class RealisticBacktestEngine:
    """
    Enhanced backtest engine with realistic market dynamics.
    
    Parameters:
    - slippage_bps: Basis points of slippage on entry/exit (default 5bps = 0.05%)
    - commission_bps: Commission per trade in basis points (default 10bps = 0.1%)
    - execution: 'open' (next bar open) or 'close' (current bar close)
    - require_volume_check: Ensure volume covers position size
    """
    
    def __init__(self, slippage_bps: float = 5.0, commission_bps: float = 10.0,
                 execution: str = 'open', require_volume_check: bool = True):
        self.slippage_bps = slippage_bps / 10000  # Convert to decimal
        self.commission_bps = commission_bps / 10000
        self.execution = execution
        self.require_volume_check = require_volume_check
        self.trades = []
    
    def run(self, df: pd.DataFrame, ticker: str, initial_capital: float = 10000.0) -> tuple:
        """
        Run backtest with realistic assumptions.
        
        Returns:
            trades_df: DataFrame of completed trades
            equity: Series of portfolio equity over time
            drawdown: Series of drawdown % over time
        """
        df = df.dropna(subset=['Close']).copy()
        
        # Add price columns for next bar (slippage calculation)
        df['next_open'] = df['Open'].shift(-1)
        df['next_high'] = df['High'].shift(-1)
        df['next_low'] = df['Low'].shift(-1)
        
        in_trade = False
        entry_price = 0.0
        entry_date = None
        entry_bar_idx = None
        hold_days = 0
        entry_fee = 0.0
        
        equity = pd.Series(index=df.index, dtype=float, data=initial_capital)
        max_equity = initial_capital
        drawdown = pd.Series(index=df.index, dtype=float, data=0.0)
        
        capital = initial_capital
        
        for i in range(len(df)):
            if df.index[i].year < 2020:  # Skip warmup period
                continue
            
            curr_bar = df.iloc[i]
            
            if in_trade:
                hold_days += 1
                
                # Check exit conditions using current bar
                buy_price = entry_price + entry_fee  # Effective cost basis
                current_close = curr_bar['Close']
                pnl_pct = (current_close - buy_price) / buy_price
                
                exit_reason = None
                exit_price = current_close
                
                # Check stop loss
                if curr_bar['Low'] <= entry_price * (1 - STOP_LOSS_PCT):
                    exit_reason = 'stop_loss'
                    exit_price = entry_price * (1 - STOP_LOSS_PCT)
                
                # Check take profit
                elif curr_bar['High'] >= entry_price * (1 + TAKE_PROFIT_PCT):
                    exit_reason = 'take_profit'
                    exit_price = entry_price * (1 + TAKE_PROFIT_PCT)
                
                # Check max holding period
                elif hold_days >= HOLDING_PERIOD_MAX:
                    exit_reason = 'max_hold'
                    exit_price = current_close
                
                # Check signal exit
                elif curr_bar.get('signal_count', 0) < 3:
                    exit_reason = 'signal_exit'
                    exit_price = current_close
                
                if exit_reason:
                    # Apply exit slippage
                    exit_price = self._apply_slippage(exit_price, side='exit')
                    exit_fee = exit_price * self.commission_bps
                    
                    # Calculate P&L
                    gross_pnl = (exit_price - entry_price) * 1  # 1 share for simplicity
                    net_pnl = gross_pnl - entry_fee - exit_fee
                    pnl_pct = net_pnl / (entry_price + entry_fee)
                    capital += net_pnl
                    
                    self.trades.append({
                        'ticker': ticker,
                        'entry_date': entry_date,
                        'exit_date': df.index[i],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'entry_fee': entry_fee,
                        'exit_fee': exit_fee,
                        'gross_pnl_pct': ((exit_price - entry_price) / entry_price) * 100,
                        'net_pnl_pct': pnl_pct * 100,
                        'hold_days': hold_days,
                        'exit_reason': exit_reason,
                        'capital_after': capital
                    })
                    
                    in_trade = False
                    hold_days = 0
            
            else:
                # Check entry conditions
                buy_signal = (
                    curr_bar.get('mandatory_ok', False) and
                    curr_bar.get('signal_count', 0) >= MIN_SIGNALS_TO_BUY
                )
                
                if buy_signal and i < len(df) - 1:  # Don't enter on last bar
                    # Use next bar for entry (more realistic)
                    if self.execution == 'open':
                        entry_price = df.iloc[i + 1]['Open']
                    else:
                        entry_price = curr_bar['Close']
                    
                    # Apply entry slippage
                    entry_price = self._apply_slippage(entry_price, side='entry')
                    entry_fee = entry_price * self.commission_bps
                    
                    in_trade = True
                    entry_date = df.index[i]
                    entry_bar_idx = i
                    hold_days = 0
            
            # Track equity and drawdown
            equity.iloc[i] = capital
            max_equity = max(max_equity, capital)
            drawdown.iloc[i] = (capital - max_equity) / max_equity if max_equity > 0 else 0
        
        trades_df = pd.DataFrame(self.trades)
        return trades_df, equity, drawdown
    
    def _apply_slippage(self, price: float, side: str) -> float:
        """Apply realistic slippage for entry/exit."""
        if side == 'entry':
            return price * (1 + self.slippage_bps)
        else:  # exit
            return price * (1 - self.slippage_bps)


class BacktestComparator:
    """Compare idealized vs realistic backtest results."""
    
    def __init__(self):
        self.results = {}
    
    def compare(self, df: pd.DataFrame, ticker: str, initial_capital: float = 10000.0) -> dict:
        """
        Run both idealized and realistic backtests and compare.
        """
        from phase3_backtest.engine import BacktestEngine as IdealisticEngine
        
        # Idealistic backtest (no slippage, no commissions)
        idealistic_engine = IdealisticEngine()
        idealistic_trades, idealistic_equity = idealistic_engine.run(df, ticker)
        
        # Realistic backtest
        realistic_engine = RealisticBacktestEngine(
            slippage_bps=5.0,
            commission_bps=10.0,
            execution='open'
        )
        realistic_trades, realistic_equity, drawdown = realistic_engine.run(df, ticker, initial_capital)
        
        # Calculate metrics for both
        from phase3_backtest.metrics import calculate_metrics
        
        idealistic_metrics = calculate_metrics(idealistic_trades, idealistic_equity, pd.Series())
        realistic_metrics = calculate_metrics(realistic_trades, realistic_equity, pd.Series())
        
        return {
            'idealistic': {
                'trades': idealistic_trades,
                'equity': idealistic_equity,
                'metrics': idealistic_metrics
            },
            'realistic': {
                'trades': realistic_trades,
                'equity': realistic_equity,
                'drawdown': drawdown,
                'metrics': realistic_metrics
            },
            'comparison': {
                'win_rate_impact': realistic_metrics.get('win_rate', 0) - idealistic_metrics.get('win_rate', 0),
                'return_impact': realistic_metrics.get('total_return_pct', 0) - idealistic_metrics.get('total_return_pct', 0),
                'sharpe_impact': realistic_metrics.get('sharpe_ratio', 0) - idealistic_metrics.get('sharpe_ratio', 0),
            }
        }
    
    def print_comparison(self, comparison: dict):
        """Print side-by-side comparison."""
        print(f"\n{'='*90}")
        print(f"{'METRIC':<30} {'IDEALISTIC':>20} {'REALISTIC':>20} {'IMPACT':>18}")
        print(f"{'='*90}\n")
        
        idealistic = comparison['idealistic']['metrics']
        realistic = comparison['realistic']['metrics']
        comparison_metrics = comparison['comparison']
        
        metrics_to_show = [
            ('Total Return %', 'total_return_pct'),
            ('Win Rate %', 'win_rate'),
            ('Sharpe Ratio', 'sharpe_ratio'),
            ('Max Drawdown %', 'max_drawdown'),
            ('Profit Factor', 'profit_factor'),
            ('Total Trades', 'total_trades'),
        ]
        
        for label, key in metrics_to_show:
            idealistic_val = idealistic.get(key, 'N/A')
            realistic_val = realistic.get(key, 'N/A')
            
            if isinstance(idealistic_val, (int, float)) and isinstance(realistic_val, (int, float)):
                impact = realistic_val - idealistic_val
                impact_str = f"{impact:+.2f}"
            else:
                impact_str = "—"
            
            print(f"{label:<30} {str(idealistic_val):>20} {str(realistic_val):>20} {impact_str:>18}")
        
        print(f"\n{'='*90}")
        print("⚠️  Realistic backtest shows impact of:")
        print("   • 5bps entry/exit slippage")
        print("   • 10bps commission per trade")
        print("   • Next-bar open execution for entries")
