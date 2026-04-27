"""
phase2_indicators/liquidity_sweep.py — Liquidity Sweep Signal
==============================================================
Detects when price spikes through a swing high/low by a small margin
and then immediately reverses back inside — a "stop hunt" pattern.

Logic:
  1. Establish swing_high and swing_low from the pivot window (N bars back,
     excluding the sweep zone)
  2. Check if the last 1-3 candles (sweep zone) wicked through a level
     by 0.1%-0.3% (beyond the level but not a full breakout)
  3. If current bar closes back inside the level → confirmed sweep

Signal:
  - liquidity_sweep_signal = True when a LONG sweep is confirmed
    (bullish: swept below swing_low then closed back above)
  - liquidity_sweep_direction = 'LONG' | 'SHORT' | 'NONE'
  - swing_high, swing_low reference levels stored for plotting
"""

import pandas as pd
import numpy as np
from config import (
    LIQUIDITY_SWEEP_LOOKBACK,
    LIQUIDITY_SWEEP_MIN_PCT,
    LIQUIDITY_SWEEP_MAX_PCT,
    LIQUIDITY_SWEEP_CANDLES,
)


def add_liquidity_sweep_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorised liquidity sweep detection.

    Columns added
    -------------
    liquidity_sweep_signal : bool
        True on a confirmed LONG sweep (bullish reversal entry).
        Used by the backtest engine's signal_count (BUY side only).
    liquidity_sweep_direction : str  ('LONG' | 'SHORT' | 'NONE')
        Full directional label — used by the real-time scoring system
        where SHORT sweeps contribute +2 sell_signals.
    swing_high : float   — pivot reference high used for detection
    swing_low  : float   — pivot reference low used for detection
    """
    df = df.copy()

    lk = LIQUIDITY_SWEEP_LOOKBACK
    mx = LIQUIDITY_SWEEP_CANDLES
    s_min = LIQUIDITY_SWEEP_MIN_PCT
    s_max = LIQUIDITY_SWEEP_MAX_PCT

    # ── Pivot reference levels ────────────────────────────────────────────────
    # At bar i, pivot window = bars [i - mx - lk  …  i - mx - 1]
    # Achieved with: shift(mx + 1).rolling(lk)
    #   shift(mx+1) at i  → series at i-(mx+1)
    #   rolling(lk) then spans [i-(mx+1)-lk+1 … i-(mx+1)]
    #                         = [i-mx-lk    … i-mx-1]  ✓
    swing_high = df['High'].shift(mx + 1).rolling(lk).max()
    swing_low  = df['Low'].shift(mx + 1).rolling(lk).min()

    # ── Sweep zone extremes ───────────────────────────────────────────────────
    # At bar i, sweep zone = last mx bars: [i-mx+1 … i]
    zone_low  = df['Low'].rolling(mx).min()   # min low of last mx bars
    zone_high = df['High'].rolling(mx).max()  # max high of last mx bars

    close = df['Close']

    # ── Bullish (LONG) sweep ──────────────────────────────────────────────────
    # Zone wicked at least 0.1 % below swing_low …
    long_swept = zone_low  <  swing_low  * (1 - s_min)
    # … but not more than 0.3 % (no full breakdown) …
    long_depth = zone_low  >= swing_low  * (1 - s_max)
    # … and current bar closed back above swing_low.
    long_rev   = close     >  swing_low

    long_sweep = long_swept & long_depth & long_rev

    # ── Bearish (SHORT) sweep ─────────────────────────────────────────────────
    short_swept = zone_high >  swing_high * (1 + s_min)
    short_depth = zone_high <= swing_high * (1 + s_max)
    short_rev   = close     <  swing_high

    short_sweep = short_swept & short_depth & short_rev

    # ── Assign columns ────────────────────────────────────────────────────────
    # liquidity_sweep_signal = True only for LONG (backtest engine counts BUYs)
    df['liquidity_sweep_signal'] = long_sweep.fillna(False)

    direction = pd.Series('NONE', index=df.index)
    direction[long_sweep]  = 'LONG'
    direction[short_sweep] = 'SHORT'
    df['liquidity_sweep_direction'] = direction

    df['swing_high_ref'] = swing_high
    df['swing_low_ref']  = swing_low

    return df
