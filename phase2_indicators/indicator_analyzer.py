"""
INDICATOR CORRELATION & REDUNDANCY ANALYSIS
============================================
Check if indicators are providing independent information or just confirming each other.

Analysis includes:
1. Signal correlation matrix (which signals activate together?)
2. Information gain analysis (does each signal improve prediction?)
3. Redundancy detection (pairs of highly correlated signals)
4. Recommendation for optimal indicator set
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt


class IndicatorAnalyzer:
    """Analyze indicator independence and information value."""
    
    SIGNAL_COLUMNS = [
        'trend_signal',
        'rsi_signal',
        'volume_signal',
        'atr_signal',
        'elliott_wave_signal',
        'fibonacci_signal',
        'regression_signal'
    ]
    
    def __init__(self):
        self.signal_cols = self.SIGNAL_COLUMNS
    
    def correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation between indicator signals.
        
        High correlation (> 0.7) = signals activate together (possible redundancy)
        Low correlation (< 0.3) = independent signals (good!)
        """
        signals_only = df[self.signal_cols].astype(int)
        corr = signals_only.corr()
        
        return corr
    
    def print_correlation_analysis(self, df: pd.DataFrame):
        """Print correlation matrix with interpretation."""
        corr = self.correlation_matrix(df)
        
        print(f"\n{'='*80}")
        print("INDICATOR CORRELATION MATRIX")
        print(f"{'='*80}\n")
        
        # Print matrix
        print(corr.to_string())
        
        print(f"\n{'='*80}")
        print("REDUNDANCY DETECTION (Correlation > 0.7)")
        print(f"{'='*80}\n")
        
        # Find high correlations
        high_corr_pairs = []
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                col_i = corr.columns[i]
                col_j = corr.columns[j]
                corr_val = corr.iloc[i, j]
                
                if corr_val > 0.7:
                    high_corr_pairs.append((col_i, col_j, corr_val))
        
        if high_corr_pairs:
            high_corr_pairs.sort(key=lambda x: x[2], reverse=True)
            print("⚠️  Potentially redundant signal pairs:\n")
            for sig1, sig2, corr_val in high_corr_pairs:
                print(f"  {sig1:<20} ↔ {sig2:<20} | Correlation: {corr_val:.2f}")
                print(f"     → Consider removing one of these signals\n")
        else:
            print("✓ No highly redundant signals detected!\n")
        
        print(f"{'='*80}")
        print("INDEPENDENCE SCORE")
        print(f"{'='*80}\n")
        
        # Calculate average correlation between each signal and all others
        for signal in self.signal_cols:
            avg_corr = corr[signal].drop(signal).mean()
            independence = 1 - avg_corr
            bar = "█" * int(independence * 20)
            print(f"{signal:<25} Independence: {independence:.2f} {bar}")
    
    def signal_activation_frequency(self, df: pd.DataFrame) -> pd.Series:
        """How often does each signal activate?"""
        signals_only = df[self.signal_cols].astype(int)
        freq = (signals_only.sum() / len(signals_only) * 100).round(2)
        return freq
    
    def print_activation_frequency(self, df: pd.DataFrame):
        """Print signal activation frequencies."""
        freq = self.signal_activation_frequency(df)
        
        print(f"\n{'='*80}")
        print("SIGNAL ACTIVATION FREQUENCY")
        print(f"{'='*80}\n")
        
        freq_sorted = freq.sort_values(ascending=False)
        
        for signal, pct in freq_sorted.items():
            bar_width = int(pct / 2)  # Scale to 50 max
            bar = "█" * bar_width
            print(f"{signal:<25} {pct:>6.1f}% {bar}")
        
        # Flag signals that never activate or always activate
        print()
        for signal, pct in freq.items():
            if pct < 5:
                print(f"⚠️  {signal} activates <5% of time — might be too strict")
            elif pct > 95:
                print(f"⚠️  {signal} activates >95% of time — might be too loose")
    
    def signal_combination_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Show how often signals activate together."""
        print(f"\n{'='*80}")
        print("SIGNAL COMBINATION PATTERNS")
        print(f"{'='*80}\n")
        
        signals_only = df[self.signal_cols].astype(int)
        signal_count = signals_only.sum(axis=1)
        
        print("Distribution of active signals per bar:\n")
        
        for count in range(0, 8):
            pct = (signal_count == count).sum() / len(signal_count) * 100
            bar = "█" * int(pct / 2)
            print(f"  {count}/7 signals: {pct:>5.1f}% {bar}")
        
        print()
        return signal_count.value_counts().sort_index()
    
    def information_gain_analysis(self, df: pd.DataFrame, target_series: pd.Series) -> Dict:
        """
        Calculate information gain for each signal.
        
        Measures: How much does adding each signal improve prediction of target?
        
        Example:
            target = df['Close'].pct_change() > 0.02  # Predict "up moves"
            gains = analyzer.information_gain(df, target)
        """
        print(f"\n{'='*80}")
        print("INFORMATION GAIN ANALYSIS")
        print(f"{'='*80}\n")
        
        if len(target_series) != len(df):
            print("Error: target series length mismatch\n")
            return {}
        
        target_series = target_series.align(df.index)[0]
        
        # Baseline accuracy (always predict most common class)
        baseline_rate = target_series.value_counts().max() / len(target_series)
        print(f"Baseline accuracy (most common class): {baseline_rate:.1%}\n")
        
        gains = {}
        
        for signal in self.signal_cols:
            signal_vals = df[signal].astype(int)
            
            # When signal=1, what's accuracy?
            signal_1_mask = signal_vals == 1
            if signal_1_mask.sum() > 0:
                acc_when_signal_1 = (target_series[signal_1_mask]).mean()
            else:
                acc_when_signal_1 = 0
            
            # Information gain: how much better when signal is active?
            gain = acc_when_signal_1 - baseline_rate
            gains[signal] = {
                'information_gain': gain,
                'accuracy_when_active': acc_when_signal_1,
                'activations': signal_1_mask.sum()
            }
        
        # Sort by gain
        sorted_gains = sorted(gains.items(), key=lambda x: x[1]['information_gain'], reverse=True)
        
        for signal, metrics in sorted_gains:
            gain = metrics['information_gain']
            acc = metrics['accuracy_when_active']
            activations = metrics['activations']
            
            if gain >= 0:
                indicator = "✓ Helpful"
            else:
                indicator = "✗ Harmful"
            
            print(f"{signal:<25} | Gain: {gain:>+6.1%} | "
                  f"Accuracy when active: {acc:>5.1%} | "
                  f"Activations: {activations:>5} | {indicator}")
        
        print()
        return dict(sorted_gains)
    
    def recommendation(self, df: pd.DataFrame, target_series: pd.Series = None) -> str:
        """Generate recommendation for indicator set optimization."""
        print(f"\n{'='*80}")
        print("RECOMMENDATION")
        print(f"{'='*80}\n")
        
        # Correlation
        corr = self.correlation_matrix(df)
        high_corr_count = sum(1 for i in range(len(corr.columns))
                             for j in range(i + 1, len(corr.columns))
                             if corr.iloc[i, j] > 0.7)
        
        # Frequency
        freq = self.signal_activation_frequency(df)
        dead_signals = (freq < 5).sum()
        always_on_signals = (freq > 95).sum()
        
        # Info gain
        if target_series is not None:
            gains = self.information_gain_analysis(df, target_series)
            negative_gain_signals = sum(1 for g in gains.values() if g['information_gain'] < 0)
        else:
            negative_gain_signals = 0
        
        print("ISSUES DETECTED:\n")
        
        if high_corr_count > 0:
            print(f"  • {high_corr_count} pairs of highly correlated signals (>0.7)")
            print(f"    → Consider removing one from each redundant pair\n")
        
        if dead_signals > 0:
            print(f"  • {dead_signals} signals activate <5% of time")
            print(f"    → May be too strict; relax thresholds or remove\n")
        
        if always_on_signals > 0:
            print(f"  • {always_on_signals} signals activate >95% of time")
            print(f"    → May be too loose; tighten thresholds or remove\n")
        
        if negative_gain_signals > 0:
            print(f"  • {negative_gain_signals} signals with negative information gain")
            print(f"    → These signals hurt prediction; consider removing\n")
        
        if high_corr_count == 0 and dead_signals == 0:
            print("  ✓ No major issues detected!")
            print(f"  ✓ All signals appear independent and active")
            print(f"  ✓ Current indicator set appears well-optimized\n")


def run_indicator_analysis(df: pd.DataFrame, target_series: pd.Series = None):
    """Run complete indicator analysis suite."""
    analyzer = IndicatorAnalyzer()
    
    # Correlation
    analyzer.print_correlation_analysis(df)
    
    # Frequency
    analyzer.print_activation_frequency(df)
    
    # Combinations
    analyzer.signal_combination_analysis(df)
    
    # Info gain (if target provided)
    if target_series is not None:
        analyzer.information_gain_analysis(df, target_series)
    
    # Recommendation
    analyzer.recommendation(df, target_series)
