#!/usr/bin/env python3
"""
Diagnostic script to test if trading system can start
Run on EC2: python3 diagnose_startup.py
"""

import sys
import traceback
from pathlib import Path

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TRADING SYSTEM STARTUP DIAGNOSTIC")
print("=" * 80)

try:
    print("\n1️⃣  Testing imports...")
    
    print("   - Importing RealtimeDataStreamer...", end="", flush=True)
    from phase7_realtime_streaming.realtime_data_streamer import RealtimeDataStreamer
    print(" ✓")
    
    print("   - Importing RealtimeIndicatorCalculator...", end="", flush=True)
    from phase7_realtime_streaming.realtime_indicator_calculator import RealtimeIndicatorCalculator
    print(" ✓")
    
    print("   - Importing RealtimeSignalGenerator...", end="", flush=True)
    from phase7_realtime_streaming.realtime_signal_generator import RealtimeSignalGenerator
    print(" ✓")
    
    print("   - Importing AlpacaBrokerInterface...", end="", flush=True)
    from phase8_broker_integration.alpaca_broker_interface import AlpacaBrokerInterface
    print(" ✓")
    
    print("   - Importing RiskManager...", end="", flush=True)
    from phase9_risk_management.risk_manager import RiskManager, PortfolioMonitor
    print(" ✓")
    
    print("\n2️⃣  Testing indicator calculator...")
    calc = RealtimeIndicatorCalculator()
    print("   ✓ Indicator calculator initialized")
    
    print("\n3️⃣  Testing with sample data...")
    import pandas as pd
    import numpy as np
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Open': np.linspace(150, 160, 100),
        'High': np.linspace(151, 161, 100),
        'Low': np.linspace(149, 159, 100),
        'Close': np.linspace(150.5, 160.5, 100),
        'Volume': np.random.randint(1000000, 5000000, 100)
    })
    
    indicators = calc.calculate_all(sample_data)
    print(f"   ✓ Calculated indicators: {len(indicators)} keys")
    print(f"   ✓ Current price: ${indicators.get('current_price', 0):.2f}")
    print(f"   ✓ EMA50: {indicators.get('ema50', 0):.2f}")
    print(f"   ✓ MACD: {indicators.get('macd', 0):.4f}")
    
    print("\n✅ ALL TESTS PASSED - System should start successfully!")
    
except Exception as e:
    print(f"\n❌ ERROR DETECTED:")
    print(f"\n{type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
