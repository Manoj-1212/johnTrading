"""
SENSITIVITY ANALYSIS MODULE
============================
Test how results change with different parameter combinations.
Identifies which thresholds have the biggest impact on strategy performance.
"""

import pandas as pd
import numpy as np
import os
import itertools
from typing import Dict, List, Tuple
from config import (
    TICKERS, BENCHMARK, START_DATE, END_DATE,
    EMA_FAST, EMA_SLOW, RSI_PERIOD, RSI_LOW, RSI_HIGH,
    VOLUME_LOOKBACK, VOLUME_THRESHOLD,
    ATR_PERIOD, ATR_LOOKBACK,
    MIN_SIGNALS_TO_BUY, HOLDING_PERIOD_MAX,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT
)
from phase1_data.downloader import StockDownloader
from phase2_indicators.combiner import build_full_indicator_set
from phase3_backtest.engine import BacktestEngine
from phase3_backtest.metrics import calculate_metrics


class SensitivityAnalyzer:
    """
    Test variations of key parameters and measure impact on:
    - Win rate
    - Total return
    - Sharpe ratio
    - Max drawdown
    - Alpha vs benchmark
    """
    
    def __init__(self):
        self.results = []
        self.baseline_metrics = {}
        
    def run_parameter_sweep(self, data: Dict[str, pd.DataFrame],
                           param_name: str, param_values: List) -> pd.DataFrame:
        """
        Test different values of a single parameter and return results table.
        
        Example:
            analyzer.run_parameter_sweep(data, 'MIN_SIGNALS_TO_BUY', [3, 4, 5, 6, 7])
        """
        print(f"\n{'='*80}")
        print(f"SENSITIVITY ANALYSIS: {param_name}")
        print(f"{'='*80}\n")
        
        results = []
        
        for value in param_values:
            print(f"Testing {param_name} = {value}...", end=" ", flush=True)
            
            # Run backtest with this parameter
            metrics_summary = self._backtest_with_param(data, param_name, value)
            
            # Store results
            metrics_summary['param_value'] = value
            results.append(metrics_summary)
            
            print(f"✓ Alpha: {metrics_summary['avg_alpha']:+.2f}%")
        
        results_df = pd.DataFrame(results)
        self._print_results_table(results_df, param_name)
        
        return results_df
    
    def run_threshold_grid(self, data: Dict[str, pd.DataFrame],
                          param_grid: Dict[str, List]) -> pd.DataFrame:
        """
        Test combinations of multiple parameters.
        
        Example:
            grid = {
                'MIN_SIGNALS_TO_BUY': [4, 5, 6],
                'STOP_LOSS_PCT': [0.05, 0.07, 0.10],
                'TAKE_PROFIT_PCT': [0.10, 0.15, 0.20]
            }
            results = analyzer.run_threshold_grid(data, grid)
        """
        print(f"\n{'='*80}")
        print(f"MULTI-PARAMETER GRID SEARCH")
        print(f"{'='*80}\n")
        
        param_names = list(param_grid.keys())
        param_combinations = itertools.product(*param_grid.values())
        
        results = []
        combo_count = np.prod([len(v) for v in param_grid.values()])
        
        for i, combo in enumerate(param_combinations, 1):
            param_dict = dict(zip(param_names, combo))
            print(f"[{i:3d}/{combo_count}] Testing {param_dict}...", end=" ", flush=True)
            
            metrics_summary = self._backtest_with_multiple_params(data, param_dict)
            metrics_summary.update(param_dict)
            results.append(metrics_summary)
            
            print(f"✓ Alpha: {metrics_summary['avg_alpha']:+.2f}%")
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('avg_alpha', ascending=False)
        
        print(f"\n{'='*80}")
        print(f"TOP 10 CONFIGURATIONS (by Alpha)")
        print(f"{'='*80}\n")
        
        for idx, row in results_df.head(10).iterrows():
            print(f"Alpha: {row['avg_alpha']:+6.2f}% | "
                  f"Win Rate: {row['avg_win_rate']:5.1f}% | "
                  f"{row}\n")
        
        return results_df
    
    def calculate_elasticity(self, data: Dict[str, pd.DataFrame],
                            param_name: str, baseline_value: float,
                            test_range: Tuple[float, float],
                            num_points: int = 5) -> Dict:
        """
        Calculate elasticity: % change in metric per 1% change in parameter.
        
        measure_elasticity(
            data, 'MIN_SIGNALS_TO_BUY', 5,
            test_range=(3, 7), num_points=5
        )
        """
        print(f"\n{'='*80}")
        print(f"ELASTICITY ANALYSIS: {param_name}")
        print(f"{'='*80}\n")
        
        test_values = np.linspace(test_range[0], test_range[1], num_points)
        
        baseline_metrics = self._backtest_with_param(data, param_name, baseline_value)
        baseline_alpha = baseline_metrics['avg_alpha']
        
        elasticity_results = []
        
        for value in test_values:
            if value == baseline_value:
                continue
                
            test_metrics = self._backtest_with_param(data, param_name, value)
            test_alpha = test_metrics['avg_alpha']
            
            # Elasticity = (% change in alpha) / (% change in parameter)
            pct_change_param = ((value - baseline_value) / baseline_value) * 100
            pct_change_alpha = ((test_alpha - baseline_alpha) / baseline_alpha) * 100
            
            elasticity = pct_change_alpha / pct_change_param if pct_change_param != 0 else 0
            
            elasticity_results.append({
                'parameter_value': value,
                'alpha': test_alpha,
                'pct_change_param': pct_change_param,
                'pct_change_alpha': pct_change_alpha,
                'elasticity': elasticity
            })
        
        results_df = pd.DataFrame(elasticity_results)
        
        print(f"Baseline ({param_name}={baseline_value}): Alpha = {baseline_alpha:+.2f}%\n")
        print(results_df.to_string(index=False))
        print(f"\nHigh elasticity = sensitive to changes (need careful tuning)")
        print(f"Low elasticity = robust to changes (good thresholds)")
        
        return results_df.to_dict('records')
    
    def _backtest_with_param(self, data: Dict[str, pd.DataFrame],
                            param_name: str, param_value) -> Dict:
        """Run backtest with a single parameter override."""
        import sys
        sys.modules['config'].param_name = param_value
        
        metrics_by_ticker = {}
        all_trades = []
        
        for ticker in list(data.keys()):
            if ticker not in [t for t in TICKERS] + [BENCHMARK]:
                continue
                
            df = data[ticker].copy()
            if df.empty or len(df) < 200:
                continue
            
            df = build_full_indicator_set(df)
            
            engine = BacktestEngine()
            trades, equity = engine.run(df, ticker)
            
            if not trades.empty:
                all_trades.append(trades)
            
            voo_equity = data.get(BENCHMARK, pd.Series()).copy()
            aligned_voo = voo_equity.reindex(df.index).ffill()
            
            metrics = calculate_metrics(trades, equity, aligned_voo)
            metrics_by_ticker[ticker] = metrics
        
        # Aggregate metrics
        alphas = [m.get('alpha', 0) for m in metrics_by_ticker.values()]
        win_rates = [m.get('win_rate', 0) for m in metrics_by_ticker.values()]
        sharpes = [m.get('sharpe_ratio', 0) for m in metrics_by_ticker.values()]
        
        return {
            'avg_alpha': np.mean(alphas) if alphas else 0,
            'avg_win_rate': np.mean(win_rates) if win_rates else 0,
            'avg_sharpe': np.mean(sharpes) if sharpes else 0,
            'num_tickers_traded': sum(1 for m in metrics_by_ticker.values() if m.get('total_trades', 0) > 0)
        }
    
    def _backtest_with_multiple_params(self, data: Dict[str, pd.DataFrame],
                                      params: Dict) -> Dict:
        """Run backtest with multiple parameter overrides."""
        # Temporarily update config
        import config as cfg
        original_values = {}
        
        for param_name, param_value in params.items():
            original_values[param_name] = getattr(cfg, param_name)
            setattr(cfg, param_name, param_value)
        
        try:
            metrics_by_ticker = {}
            
            for ticker in list(data.keys()):
                if ticker not in [t for t in TICKERS] + [BENCHMARK]:
                    continue
                    
                df = data[ticker].copy()
                if df.empty or len(df) < 200:
                    continue
                
                df = build_full_indicator_set(df)
                
                engine = BacktestEngine()
                trades, equity = engine.run(df, ticker)
                
                voo_equity = data.get(BENCHMARK, pd.Series()).copy()
                aligned_voo = voo_equity.reindex(df.index).ffill()
                
                metrics = calculate_metrics(trades, equity, aligned_voo)
                metrics_by_ticker[ticker] = metrics
            
            alphas = [m.get('alpha', 0) for m in metrics_by_ticker.values()]
            win_rates = [m.get('win_rate', 0) for m in metrics_by_ticker.values()]
            
            return {
                'avg_alpha': np.mean(alphas) if alphas else 0,
                'avg_win_rate': np.mean(win_rates) if win_rates else 0,
                'num_tickers_traded': sum(1 for m in metrics_by_ticker.values() if m.get('total_trades', 0) > 0)
            }
        finally:
            # Restore original values
            for param_name, param_value in original_values.items():
                setattr(cfg, param_name, param_value)
    
    def _print_results_table(self, results_df: pd.DataFrame, param_name: str):
        """Pretty print results table."""
        print(f"\n{'Param Value':<15} {'Avg Alpha':<12} {'Avg Win%':<12} {'Avg Sharpe':<12} {'Trades':<8}")
        print("-" * 60)
        
        for _, row in results_df.iterrows():
            print(f"{row['param_value']:<15.3f} "
                  f"{row['avg_alpha']:>+10.2f}% "
                  f"{row['avg_win_rate']:>10.1f}% "
                  f"{row['avg_sharpe']:>10.2f} "
                  f"{row['num_tickers_traded']:>7}")
        
        print()
