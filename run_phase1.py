"""
run_phase1.py — Phase 1 execution script
Downloads and validates stock data
Run this first before proceeding to Phase 2
"""

from phase1_data.downloader import StockDownloader
from phase1_data.validator import DataValidator


def main():
    print("\n" + "="*80)
    print("📥 PHASE 1: DATA DOWNLOAD & VALIDATION")
    print("="*80)
    
    # Step 1: Download data
    print("\n[STEP 1] Downloading stock data...")
    dl = StockDownloader()
    data = dl.download_all(force_refresh=True)
    
    # Step 2: Validate data
    print("\n[STEP 2] Validating data quality...")
    validator = DataValidator()
    valid_tickers = validator.validate(data)
    
    # Step 3: Report results
    print("\n[RESULT]")
    if len(valid_tickers) < 2:
        print("❌ Not enough valid data. Please check data sources and try again.")
        print("   Hint: Try force_refresh=True to re-download all data")
        return False
    else:
        print(f"✅ Phase 1 complete!")
        print(f"   Valid tickers: {valid_tickers}")
        print(f"   Ready to proceed to Phase 2: Indicator Calculation\n")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
