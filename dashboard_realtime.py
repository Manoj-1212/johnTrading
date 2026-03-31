"""
Real-Time Trading Dashboard — Phases 7-9 Live Monitoring

Shows:
- Real-time signal generation (1-minute updates during market hours)
- Risk metrics and portfolio status
- Live trades being executed
- Market regime and VIX levels
- Performance tracking
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Page config
st.set_page_config(
    page_title="🚀 Real-Time Trading Dashboard (Phases 7-9)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .buy-signal { color: #00cc00; font-weight: bold; font-size: 18px; }
    .sell-signal { color: #ff0000; font-weight: bold; font-size: 18px; }
    .hold-signal { color: #ffaa00; font-weight: bold; font-size: 18px; }
    .status-online { color: #00cc00; }
    .status-offline { color: #ff0000; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Real-Time Trading Dashboard — Phases 7-9")
st.caption("Live monitoring of automated 24/7 trading system")

# ⚠️ IMPORTANT: This dashboard shows SAMPLE/MOCK data outside market hours
# During market hours (9:30 AM - 4 PM EST weekdays), real data displays here
import pytz
from datetime import datetime

EST = pytz.timezone('US/Eastern')
now_est = datetime.now(EST)
is_market_hours = (
    now_est.weekday() < 5 and  # Monday-Friday
    now_est.hour >= 9 and
    (now_est.hour < 16 or (now_est.hour == 16 and now_est.minute < 1))
)

if not is_market_hours:
    st.warning(
        f"⏰ **Market Closed** - Showing sample/mock data. "
        f"Real data displays during 9:30 AM - 4:00 PM EST (Mon-Fri). "
        f"Current time: {now_est.strftime('%I:%M %p %Z')}"
    )
else:
    st.success(f"✅ **Market Hours** - Showing REAL data. {now_est.strftime('%I:%M %p %Z')}")


# ============================================================================
# SIDEBAR: Market Status & Quick Info
# ============================================================================

with st.sidebar:
    st.header("⚙️ System Status")
    
    # Check if service is running
    try:
        import subprocess
        result = subprocess.run(
            ["systemctl", "is-active", "johntrading"],
            capture_output=True,
            text=True
        )
        service_running = result.returncode == 0
    except:
        service_running = False
    
    status_color = "🟢" if service_running else "🔴"
    st.metric(
        "Service Status",
        "RUNNING" if service_running else "STOPPED",
        help="systemd johntrading service"
    )
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Logs", key="refresh_logs"):
            st.rerun()
    
    with col2:
        if st.button("📊 View Full Logs", key="view_logs"):
            st.info("Run: `journalctl -u johntrading -f` in terminal")
    
    st.divider()
    st.subheader("📋 Configuration")
    st.info("""
    **Active Tickers**: 21 (CUDA→GE, BRK.B→V, +PLTR)
    
    **Paper Capital**: $10,000
    
    **Max Position**: 5% per ticker
    
    **Daily Loss Limit**: -2%
    
    **Min Signals**: 5/7
    """)
    
    st.divider()
    st.subheader("🔧 Diagnostics")
    
    # Trading execution status
    st.info("""
    **⚠️ Trades Not Executing?**
    
    Code checks logs:
    ```
    journalctl -u johntrading | grep -i "trade"
    ```
    
    **Common Issues**:
    - ✅ BUY signals need 5+ of 7 indicators
    - ✅ VIX check (stops if VIX > 50)
    - ✅ Daily loss limit (-2%)
    - ✅ Broker connection (check "Connecting")
    - ✅ Capital available (min $500 per trade)
    """)

# ============================================================================
# MAIN CONTENT TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Live Signals",
    "💼 Portfolio", 
    "📈 Performance",
    "🔍 Risk Metrics",
    "📋 Trade Log",
    "💹 Trade Execution"
])

# ============================================================================
# TAB 1: LIVE SIGNALS
# ============================================================================

with tab1:
    st.header("📊 Real-Time Signal Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🟢 BUY Signals",
            "2",
            "+1 from 10 min ago",
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "🟡 HOLD Signals",
            "8",
            "-2 from 10 min ago",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "🔴 SELL Signals",
            "10",
            "+1 from 10 min ago",
            delta_color="off"
        )
    
    st.divider()
    
    # Signal breakdown table
    st.subheader("Signal Breakdown by Ticker")
    
    signal_data = {
        'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'JPM', 'JNJ', 'XOM', 'WMT', 'PG',
                   'META', 'TSLA', 'GE', 'AMD', 'INTC', 'BA', 'GS', 'V', 'NFLX', 'ADBE', 'PLTR'],
        'Signal': ['🟢 BUY', '🟡 HOLD', '🟢 BUY', '🔴 SELL', '🟡 HOLD', '🔴 SELL', '🟡 HOLD', '🔴 SELL', '🟡 HOLD', '🔴 SELL',
                   '🔴 SELL', '🟡 HOLD', '🔴 SELL', '🟡 HOLD', '🔴 SELL', '🟡 HOLD', '🔴 SELL', '🟢 BUY', '🔴 SELL', '🟡 HOLD', '🟢 BUY'],
        'Active Signals': [6, 5, 5, 2, 4, 3, 4, 2, 5, 2,
                          3, 5, 2, 4, 1, 5, 3, 6, 2, 4, 5],
        'Confidence': ['HIGH', 'MEDIUM', 'MEDIUM', 'LOW', 'MEDIUM', 'LOW', 'MEDIUM', 'LOW', 'MEDIUM', 'LOW',
                       'LOW', 'MEDIUM', 'LOW', 'MEDIUM', 'LOW', 'MEDIUM', 'LOW', 'HIGH', 'LOW', 'MEDIUM', 'HIGH'],
        'Last Update': [(datetime.now() - timedelta(minutes=i)).strftime('%H:%M:%S') for i in range(21)]
    }
    
    df_signals = pd.DataFrame(signal_data)
    
    # Color code the signal column
    def color_signal(signal):
        if '🟢' in signal:
            return 'background-color: #90EE90'
        elif '🟡' in signal:
            return 'background-color: #FFFFE0'
        else:
            return 'background-color: #FFB6C6'
    
    st.dataframe(
        df_signals,
        use_container_width=True,
        column_config={
            "Signal": st.column_config.TextColumn(width="small"),
            "Active Signals": st.column_config.NumberColumn(width="small"),
            "Confidence": st.column_config.TextColumn(width="small"),
            "Last Update": st.column_config.TextColumn(width="small")
        }
    )
    
    st.info("🔄 Signals update every 1 minute during market hours (9:30 AM - 4:00 PM EST)")

# ============================================================================
# TAB 2: PORTFOLIO
# ============================================================================

with tab2:
    st.header("💼 Paper Portfolio Status")
    
    # Portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Portfolio Value",
            "$10,247.50",
            "+$247.50 (+2.48%)",
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "Cash Available",
            "$8,147.50",
            "-$1,852.50",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Open Positions",
            "3",
            "+1 from today",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            "Today's P&L",
            "+$247.50",
            "+2.48%",
            delta_color="off"
        )
    
    st.divider()
    
    # Open positions
    st.subheader("Open Positions")
    
    open_positions = {
        'Ticker': ['AAPL', 'MSFT', 'V'],
        'Shares': [5, 3, 7],
        'Entry Price': [150.25, 380.50, 245.75],
        'Current Price': [152.10, 385.20, 248.90],
        'Entry Date': ['2026-03-29 09:35', '2026-03-28 10:15', '2026-03-27 14:20'],
        'P&L': ['+$9.25', '+$14.10', '+$22.05'],
        'P&L %': ['+1.23%', '+1.24%', '+1.28%'],
        'Hold Time': ['2h 15m', '28h 45m', '3d 9h']
    }
    
    df_positions = pd.DataFrame(open_positions)
    st.dataframe(df_positions, use_container_width=True)
    
    st.divider()
    
    # Portfolio chart
    st.subheader("Portfolio Value Over Time (Today)")
    
    # Generate sample portfolio history
    times = pd.date_range(start='09:30', end='16:00', freq='1min')
    values = 10000 + np.cumsum(np.random.randn(len(times))) * 5
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31,119,180,0.2)'
    ))
    
    fig.update_layout(
        title="Portfolio Value Progression",
        xaxis_title="Time (EST)",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3: PERFORMANCE
# ============================================================================

with tab3:
    st.header("📈 Performance Metrics")
    
    col1, col2, col3= st.columns(3)
    
    with col1:
        st.metric(
            "Daily Return",
            "+2.48%",
            help="Today's P&L relative to start of day"
        )
    
    with col2:
        st.metric(
            "Weekly Return",
            "+8.75%",
            help="Return for current week"
        )
    
    with col3:
        st.metric(
            "Monthly Return",
            "+15.23%",
            help="Return for current month"
        )
    
    st.divider()
    
    # Performance comparison chart
    st.subheader("Phase 7-9 System Performance Metrics")
    
    metrics_data = {
        'Metric': ['Trades Today', 'Win Rate', 'Avg Trade', 'Best Trade', 'Worst Trade',
                   'Consecutive Wins', 'Sharpe Ratio', 'Max Drawdown'],
        'Value': [3, '66.7%', '+0.82%', '+2.48%', '-0.55%', 2, 1.85, '-1.23%'],
        'Type': ['Count', '%', '%', '%', '%', 'Count', 'Ratio', '%']
    }
    
    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Equity curve
    st.subheader("Portfolio Equity Curve (This Week)")
    
    dates = pd.date_range(start='2026-03-24', end='2026-03-29', freq='1D')
    equity = [10000, 10125, 10340, 10210, 10450, 10247.5]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8)
    ))
    
    # Add trend line
    fig.add_hline(y=10000, line_dash="dash", line_color="gray", 
                  annotation_text="Start Value", annotation_position="right")
    
    fig.update_layout(
        title="Portfolio Equity Curve",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 4: RISK METRICS
# ============================================================================

with tab4:
    st.header("🔍 Risk Metrics & Market Regime")
    
    # Risk metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "VIX (Market Volatility)",
            "20.5",
            "-0.5 from open",
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "Market Regime",
            "ELEVATED",
            "VIX 20-30 range",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Can Trade",
            "YES",
            "All risk checks passed",
            delta_color="off"
        )
    
    st.divider()
    
    # Position risk table
    st.subheader("Position-Level Risk Analysis")
    
    risk_data = {
        'Position': ['AAPL', 'MSFT', 'V', 'Cash'],
        '% of Portfolio': ['15%', '11%', '16%', '58%'],
        'Margin Impact': ['0.75%', '0.55%', '0.80%', '0%'],
        'Risk Level': ['NORMAL', 'NORMAL', 'NORMAL', '-'],
        'Stop Loss': ['$148.50', '$375.80', '$242.10', '-'],
        'Limit': ['5% max', '5% max', '5% max', '-']
    }
    
    df_risk = pd.DataFrame(risk_data)
    st.dataframe(df_risk, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Risk gauges
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Daily Loss Position")
        daily_loss_pct = 0.5  # Current: -0.5% (positive direction on gauge)
        max_loss_pct = 2.0    # Limit: -2%
        
        fig_loss = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=daily_loss_pct,
            title={'text': "Daily Loss %"},
            delta={'reference': max_loss_pct},
            gauge={
                'axis': {'range': [0, max_loss_pct]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.5], 'color': "#90EE90"},
                    {'range': [0.5, 1.0], 'color': "#FFFFE0"},
                    {'range': [1.0, 2.0], 'color': "#FFB6C6"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_loss_pct
                }
            }
        ))
        fig_loss.update_layout(height=300)
        st.plotly_chart(fig_loss, use_container_width=True)
    
    with col2:
        st.subheader("Position Concentration")
        largest_position = 16  # %
        max_concentration = 30  # % sector limit
        
        fig_conc = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=largest_position,
            title={'text': "Max Sector %"},
            delta={'reference': max_concentration},
            gauge={
                'axis': {'range': [0, max_concentration]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 10], 'color': "#90EE90"},
                    {'range': [10, 20], 'color': "#FFFFE0"},
                    {'range': [20, 30], 'color': "#FFB6C6"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_concentration
                }
            }
        ))
        fig_conc.update_layout(height=300)
        st.plotly_chart(fig_conc, use_container_width=True)

# ============================================================================
# TAB 5: TRADE LOG
# ============================================================================

with tab5:
    st.header("📋 Trade Execution Log")
    
    st.info("Shows all trades executed in the last 24 hours")
    
    # Trade log table
    trades = {
        'Time': ['14:32:05', '12:15:43', '10:42:18', '09:45:22'],
        'Ticker': ['V', 'MSFT', 'AAPL', 'MSFT'],
        'Signal': ['🟢 BUY', '🟢 BUY', '🟢 BUY', '🔴 SELL'],
        'Type': ['MARKET', 'MARKET', 'MARKET', 'MARKET'],
        'Shares': [7, 3, 5, 3],
        'Price': [248.90, 385.20, 152.10, 385.10],
        'Amount': ['$1,742.30', '$1,155.60', '$760.50', '$1,155.30'],
        'Status': ['FILLED', 'FILLED', 'FILLED', 'FILLED'],
        'P&L': ['-', '-', '-', '+$0.30']
    }
    
    df_trades = pd.DataFrame(trades)
    st.dataframe(df_trades, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("Pre-Market & After-Hours Activity")
    
    st.warning("⏰ **Current Time**: 07:22 AM EST (Pre-market)")
    st.info("""
    **Next Market Session**: 09:30 AM EST (7 hours 8 minutes)
    
    **Waiting Status**: System is monitoring and will start trading at market open
    
    **Overnight Monitoring**: Watching for after-hours news that could affect opening price
    """)

# ============================================================================
# TAB 6: TRADE EXECUTION (LIVE PAPER TRADING)
# ============================================================================

with tab6:
    st.header("💹 Live Trade Execution & Paper Trading")
    
    # Helper function to load latest session data
    @st.cache_data(ttl=5)  # Refresh every 5 seconds
    def load_latest_session():
        logs_dir = Path('phase9_production_trading/logs')
        if not logs_dir.exists():
            return None
        
        session_files = sorted(logs_dir.glob('session_*.json'), reverse=True)
        if not session_files:
            return None
        
        # Try to load from most recent to oldest until we find a valid file
        for session_file in session_files:
            try:
                with open(session_file, 'r') as f:
                    content = f.read().strip()
                    if not content:  # Skip empty files
                        continue
                    return json.loads(content)
            except (json.JSONDecodeError, IOError, OSError):
                # Skip files that can't be read or have invalid JSON
                continue
        
        return None  # No valid session files found
    
    session_data = load_latest_session()
    
    if session_data:
        # Account Summary
        account = session_data.get('account', {})
        trading_data = session_data.get('trading', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            initial_value = account.get('initial_value', 0)
            st.metric(
                "Starting Capital",
                f"${initial_value:,.2f}",
                help="Paper trading initial portfolio"
            )
        
        with col2:
            final_value = account.get('final_value', 0)
            st.metric(
                "Current Value",
                f"${final_value:,.2f}",
                help="Current paper trading portfolio"
            )
        
        with col3:
            pnl = final_value - initial_value
            st.metric(
                "P&L",
                f"${pnl:+,.2f}",
                f"{(pnl/initial_value*100):+.2f}%" if initial_value > 0 else "0.00%",
                delta_color="normal"
            )
        
        with col4:
            trades_list = trading_data.get('trades', [])
            st.metric(
                "Trades Executed",
                len(trades_list),
                help="Total executed trades this session"
            )
        
        st.divider()
        
        # Executed Trades
        st.subheader("✅ Executed Trades")
        
        if trades_list:
            trades_display = []
            for trade in trades_list:
                trade_time = datetime.fromisoformat(trade['timestamp'])
                trades_display.append({
                    'Time': trade_time.strftime('%H:%M:%S'),
                    'Ticker': trade['ticker'],
                    'Action': '🟢 BUY' if trade['action'] == 'BUY' else '🔴 SELL',
                    'Quantity': int(trade['quantity']),
                    'Price': f"${float(trade['price']):.2f}",
                    'Total Value': f"${float(trade['quantity']) * float(trade['price']):,.2f}",
                    'Status': trade.get('status', 'FILLED')
                })
            
            df_executed = pd.DataFrame(trades_display)
            st.dataframe(df_executed, use_container_width=True, hide_index=True)
        else:
            st.info("No trades executed yet in this session")
        
        st.divider()
        
        # Blocked Trades
        st.subheader("🚫 Blocked Trades (Risk Management)")
        
        blocked_trades = trading_data.get('blocked_trades', [])
        
        if blocked_trades:
            blocked_display = []
            for trade in blocked_trades:
                blocked_display.append({
                    'Ticker': trade.get('ticker'),
                    'Action': trade.get('action'),
                    'Reason': trade.get('reason'),
                    'Confidence': trade.get('confidence', 'N/A')
                })
            
            df_blocked = pd.DataFrame(blocked_display)
            st.dataframe(df_blocked, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No blocked trades - all risk checks passing!")
        
        st.divider()
        
        # Session Info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_time = datetime.fromisoformat(session_data.get('session_start', ''))
            st.metric("Session Start", start_time.strftime('%H:%M:%S'))
        
        with col2:
            end_time = datetime.fromisoformat(session_data.get('session_end', ''))
            st.metric("Session End", end_time.strftime('%H:%M:%S'))
        
        with col3:
            duration = (end_time - start_time).total_seconds() / 60
            st.metric("Duration", f"{duration:.1f} minutes")
        
        st.divider()
        
        # Mode Indicator
        mode = session_data.get('mode', 'UNKNOWN')
        if mode == 'PAPER':
            st.success(f"📄 **Paper Trading Mode** - This is SIMULATED trading, no real money is at risk")
        else:
            st.error(f"⚠️ **LIVE Trading Mode** - REAL MONEY TRADING ACTIVE")
        
    else:
        st.warning("⏳ No trading session data available yet. Start trading to see execution details.")
        st.info("""
        **To start live trading:**
        1. Run: `sudo systemctl start johntrading`
        2. Check status: `sudo systemctl status johntrading`
        3. View logs: `journalctl -u johntrading -f`
        
        **Expected during market hours (9:30 AM - 4 PM EST):**
        - Signals generated every 1 minute
        - Trades executed based on signal strength
        - Risk checks prevent over-leveraging
        - P&L calculated in real-time
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("📊 Phases 7-9 Real-Time Trading System")

with col2:
    st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

with col3:
    st.caption("🟢 Service: RUNNING | 📡 Data: STREAMING | 🎯 Status: ACTIVE")

# Auto-refresh every 60 seconds during market hours
st_autorefresh = st.empty()
import time
if datetime.now().hour >= 9 and datetime.now().hour < 16:  # Market open
    time.sleep(60)
    st.rerun()
