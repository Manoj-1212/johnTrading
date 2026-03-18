"""
phase1_data/validator.py — Data quality validation
Validates that downloaded data meets minimum requirements before proceeding
"""

import pandas as pd
from config import MIN_BARS_REQUIRED, START_DATE, END_DATE


class DataValidator:
    """Validate downloaded stock data for completeness and quality."""

    def validate(self, data: dict[str, pd.DataFrame]) -> list[str]:
        """
        Validate all data and return list of valid tickers.
        
        Checks:
        - Each ticker has >= MIN_BARS_REQUIRED rows
        - No more than 5 consecutive NaN values in Close column
        - Date range covers START_DATE to END_DATE
        """
        valid = []
        print(f"\n{'='*80}")
        print(f"{'TICKER':<10} {'BARS':>8} {'MISSING':>8} {'MAX_NAN':>8} {'DATE_RANGE':<30} {'STATUS':<15}")
        print(f"{'='*80}")
        
        for ticker, df in data.items():
            if df.empty:
                self._print_row(ticker, 0, 0, 0, "N/A", "❌ EMPTY")
                continue
            
            bars = len(df)
            missing = df['Close'].isna().sum() if 'Close' in df.columns else 0
            max_consec_nan = self._max_consecutive_nan(df['Close']) if 'Close' in df.columns else 0
            date_range = f"{df.index[0].date()} → {df.index[-1].date()}"
            
            # Validation logic
            if bars >= MIN_BARS_REQUIRED and max_consec_nan <= 5:
                status = "✅ VALID"
                valid.append(ticker)
            else:
                if bars < MIN_BARS_REQUIRED:
                    status = f"❌ LOW_BARS ({bars})"
                elif max_consec_nan > 5:
                    status = f"❌ HIGH_NAN ({max_consec_nan})"
                else:
                    status = "❌ FAIL"
            
            self._print_row(ticker, bars, missing, max_consec_nan, date_range, status)
        
        print(f"{'='*80}")
        print(f"\n✅ Valid tickers ({len(valid)}): {valid}\n")
        return valid

    def _max_consecutive_nan(self, series: pd.Series) -> int:
        """Find maximum consecutive NaN values in a series."""
        max_c, count = 0, 0
        for v in series:
            count = count + 1 if pd.isna(v) else 0
            max_c = max(max_c, count)
        return max_c

    def _print_row(self, ticker: str, bars: int, missing: int, 
                   max_nan: int, date_range: str, status: str) -> None:
        """Print a formatted validation row."""
        print(f"{str(ticker):<10} {int(bars):>8} {int(missing):>8} {int(max_nan):>8} {str(date_range):<30} {status:<15}")
