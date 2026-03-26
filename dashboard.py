"""
JOHN TRADING SYSTEM - PORTFOLIO DASHBOARD
Real-time visualization of trades, signals, and analysis

Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="John Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .profit-positive {
        color: #00cc00;
        font-weight: bold;
    }
    .profit-negative {
        color: #ff3333;
        font-weight: bold;
    }
    .signal-buy {
        background: #00cc00;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .signal-sell {
        background: #ff3333;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .signal-hold {
        background: #ffaa00;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def load_portfolio_data():
    """Load portfolio from JSON"""
    portfolio_file = "phase6_paper_trade/paper_portfolio.json"
    if os.path.exists(portfolio_file):
        try:
            with open(portfolio_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def load_signals():
    """Load today's trading signals"""
    signals_file = "phase4_signals/latest_signals.json"
    if os.path.exists(signals_file):
        try:
            with open(signals_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def load_backtest_results():
    """Load backtest performance metrics"""
    results_file = "phase3_backtest/results/final_report.csv"
    if os.path.exists(results_file):
        try:
            return pd.read_csv(results_file)
        except:
            return None
    return None


def load_trade_history():
    """Load closed trades from portfolio"""
    portfolio = load_portfolio_data()
    if portfolio and 'closed_trades' in portfolio:
        trades = portfolio['closed_trades']
        if trades:
            return pd.DataFrame(trades)
    return None


def format_currency(value):
    """Format number as currency"""
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return value


def format_percent(value):
    """Format number as percentage"""
    if isinstance(value, (int, float)):
        color = "green" if value >= 0 else "red"
        return f"<span style='color:{color}'>{value:.2f}%</span>"
    return value


# ============================================================================
# SIDEBAR - NAVIGATION & SETTINGS
# ============================================================================
st.sidebar.title("📊 Trading Dashboard")
page = st.sidebar.radio("Navigation", [
    "📈 Overview",
    "💼 Portfolio",
    "🎯 Today's Signals",
    "📉 Performance Analysis",
    "🔄 Trade History"
])

# Refresh interval
refresh_interval = st.sidebar.selectbox(
    "Auto-refresh interval",
    ["Off", "Every 1 min", "Every 5 min", "Every 15 min"],
    index=0
)

st.sidebar.divider()

# System status
st.sidebar.subheader("System Status")
portfolio = load_portfolio_data()
if portfolio:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Portfolio Value", format_currency(portfolio.get('total_value', 0)))
    with col2:
        cash = portfolio.get('cash', 0)
        st.metric("Available Cash", format_currency(cash))
    
    last_update = portfolio.get('last_update', 'Unknown')
    st.sidebar.caption(f"Last updated: {last_update}")
else:
    st.sidebar.warning("Portfolio data not found. Run Phase 6 first.")

st.sidebar.divider()

# Quick links
st.sidebar.subheader("Quick Links")
if st.sidebar.button("🔄 Refresh All Data"):
    st.rerun()

if st.sidebar.button("📡 Run Full Pipeline"):
    st.info("To run the full pipeline, execute: `python run_all.py`")


# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================
if page == "📈 Overview":
    st.title("📊 Trading Dashboard Overview")
    
    portfolio = load_portfolio_data()
    signals = load_signals()
    
    if not portfolio:
        st.error("Portfolio data not found. Please run Phase 6 first.")
        st.stop()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_value = portfolio.get('total_value', 0)
        st.metric(
            "💰 Portfolio Value",
            format_currency(total_value),
            delta=None
        )
    
    with col2:
        initial = portfolio.get('initial_capital', 10000)
        pnl = total_value - initial
        pnl_pct = (pnl / initial * 100) if initial > 0 else 0
        st.metric(
            "📈 Total P&L",
            format_currency(pnl),
            delta=f"{pnl_pct:.2f}%"
        )
    
    with col3:
        positions = len(portfolio.get('positions', []))
        st.metric(
            "📍 Open Positions",
            positions
        )
    
    with col4:
        total_trades = len(portfolio.get('closed_trades', []))
        st.metric(
            "✅ Closed Trades",
            total_trades
        )
    
    st.divider()
    
    # Today's signals summary
    if signals:
        st.subheader("🎯 Today's Trading Signals")
        
        buy_signals = signals.get('buy', [])
        sell_signals = signals.get('sell', [])
        hold_signals = signals.get('hold', [])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"### 🟢 Buy Signals: {len(buy_signals)}")
            for signal in buy_signals[:5]:
                st.success(f"**{signal.get('ticker')}** @ ${signal.get('price', 0):.2f}")
        
        with col2:
            st.markdown(f"### 🟡 Hold Signals: {len(hold_signals)}")
            for signal in hold_signals[:5]:
                st.warning(f"**{signal.get('ticker')}** @ ${signal.get('price', 0):.2f}")
        
        with col3:
            st.markdown(f"### 🔴 Sell Signals: {len(sell_signals)}")
            for signal in sell_signals[:5]:
                st.error(f"**{signal.get('ticker')}** @ ${signal.get('price', 0):.2f}")
    
    st.divider()
    
    # Open positions
    st.subheader("📍 Current Positions")
    positions = portfolio.get('positions', {})
    if positions:
        pos_data = []
        # Positions is a dict: {ticker: {shares, entry_price, entry_date, ...}}
        for ticker, pos in positions.items():
            entry_price = float(pos.get('entry_price', 0))
            shares = float(pos.get('shares', 0))
            current_price = float(pos.get('current_price', entry_price))  # Use entry_price as fallback
            
            pnl = (current_price - entry_price) * shares
            pnl_pct = (pnl / (entry_price * shares) * 100) if entry_price > 0 else 0
            
            pos_data.append({
                'Ticker': ticker,
                'Entry Price': f"${entry_price:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Shares': f"{shares:.2f}",
                'Position Value': f"${current_price * shares:.2f}",
                'P&L': f"${pnl:.2f}",
                'P&L %': f"{pnl_pct:+.2f}%",
                'Entry Date': pos.get('entry_date', 'N/A')
            })
        
        df_positions = pd.DataFrame(pos_data)
        st.dataframe(df_positions, use_container_width=True, hide_index=True)
    else:
        st.info("No open positions currently.")


# ============================================================================
# PAGE 2: PORTFOLIO
# ============================================================================
elif page == "💼 Portfolio":
    st.title("💼 Portfolio Details")
    
    portfolio = load_portfolio_data()
    if not portfolio:
        st.error("Portfolio data not found.")
        st.stop()
    
    # Portfolio summary
    st.subheader("Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Initial Capital", format_currency(portfolio.get('initial_capital', 0)))
    with col2:
        st.metric("Current Value", format_currency(portfolio.get('total_value', 0)))
    with col3:
        cash = portfolio.get('cash', 0)
        st.metric("Cash on Hand", format_currency(cash))
    with col4:
        invested = portfolio.get('total_value', 0) - cash
        st.metric("Invested", format_currency(invested))
    
    st.divider()
    
    # Position breakdown
    st.subheader("Position Breakdown by Sector")
    positions = portfolio.get('positions', {})
    
    if positions:
        # Create sector summary
        sector_data = {}
        for ticker, pos in positions.items():
            sector = pos.get('sector', 'Unknown')
            current_price = float(pos.get('current_price', pos.get('entry_price', 0)))
            shares = float(pos.get('shares', 0))
            value = current_price * shares
            if sector not in sector_data:
                sector_data[sector] = 0
            sector_data[sector] += value
        
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(sector_data.keys()),
            values=list(sector_data.values()),
            marker=dict(colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe'])
        )])
        fig.update_layout(height=400, title="Sector Allocation")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Detailed positions table
    st.subheader("All Positions")
    if positions:
        pos_data = []
        for ticker, pos in positions.items():
            entry_price = float(pos.get('entry_price', 0))
            shares = float(pos.get('shares', 0))
            current_price = float(pos.get('current_price', entry_price))
            
            pnl = (current_price - entry_price) * shares
            pnl_pct = (pnl / (entry_price * shares) * 100) if entry_price > 0 else 0
            
            pos_data.append({
                'Ticker': ticker,
                'Sector': pos.get('sector', 'N/A'),
                'Shares': f"{shares:.2f}",
                'Entry Price': f"${entry_price:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Position Value': f"${current_price * shares:.2f}",
                'Unrealized P&L': f"${pnl:.2f}",
                'Return %': f"{pnl_pct:+.2f}%",
                'Entry Date': pos.get('entry_date', 'N/A'),
                'Days Held': pos.get('days_held', 0)
            })
        
        df = pd.DataFrame(pos_data)
        
        # Color code the return column
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Return %": st.column_config.TextColumn(width="medium"),
                "Unrealized P&L": st.column_config.TextColumn(width="medium"),
            }
        )


# ============================================================================
# PAGE 3: TODAY'S SIGNALS
# ============================================================================
elif page == "🎯 Today's Signals":
    st.title("🎯 Today's Trading Signals")
    
    signals = load_signals()
    if not signals:
        st.warning("No signals found. Run Phase 4 first.")
        st.stop()
    
    # Signal summary
    buy_signals = signals.get('buy', [])
    sell_signals = signals.get('sell', [])
    hold_signals = signals.get('hold', [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🟢 Buy Signals", len(buy_signals))
    with col2:
        st.metric("🟡 Hold Signals", len(hold_signals))
    with col3:
        st.metric("🔴 Sell Signals", len(sell_signals))
    with col4:
        total = len(buy_signals) + len(hold_signals) + len(sell_signals)
        st.metric("Total Signals", total)
    
    st.divider()
    
    # Buy signals
    if buy_signals:
        st.subheader("🟢 BUY SIGNALS")
        buy_data = []
        for signal in buy_signals:
            buy_data.append({
                'Ticker': signal.get('ticker'),
                'Price': f"${signal.get('price', 0):.2f}",
                'Confidence': str(signal.get('confidence', 'MEDIUM')),
                'Active Indicators': f"{signal.get('active_indicators', [])}",
                'Strength': signal.get('signal_strength', 'Medium'),
            })
        df_buy = pd.DataFrame(buy_data)
        st.dataframe(df_buy, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Hold signals
    if hold_signals:
        st.subheader("🟡 HOLD SIGNALS")
        hold_data = []
        for signal in hold_signals:
            hold_data.append({
                'Ticker': signal.get('ticker'),
                'Price': f"${signal.get('price', 0):.2f}",
                'Confidence': str(signal.get('confidence', 'MEDIUM')),
                'Active Indicators': f"{signal.get('active_indicators', [])}",
                'Reason': signal.get('reason', 'Monitoring'),
            })
        df_hold = pd.DataFrame(hold_data)
        st.dataframe(df_hold, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Sell signals
    if sell_signals:
        st.subheader("🔴 SELL SIGNALS")
        sell_data = []
        for signal in sell_signals:
            sell_data.append({
                'Ticker': signal.get('ticker'),
                'Price': f"${signal.get('price', 0):.2f}",
                'Confidence': str(signal.get('confidence', 'MEDIUM')),
                'Active Indicators': f"{signal.get('active_indicators', [])}",
                'Reason': signal.get('reason', 'Sell condition triggered'),
            })
        df_sell = pd.DataFrame(sell_data)
        st.dataframe(df_sell, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 4: PERFORMANCE ANALYSIS
# ============================================================================
elif page == "📉 Performance Analysis":
    st.title("📉 Performance Analysis")
    
    portfolio = load_portfolio_data()
    if not portfolio:
        st.error("Portfolio data not found.")
        st.stop()
    
    # Performance metrics
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    initial = portfolio.get('initial_capital', 10000)
    current = portfolio.get('total_value', 0)
    total_pnl = current - initial
    total_pnl_pct = (total_pnl / initial * 100) if initial > 0 else 0
    
    trades = portfolio.get('closed_trades', [])
    
    if trades:
        win_count = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = (win_count / len(trades) * 100) if trades else 0
        avg_win = sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]) / max(win_count, 1)
        avg_loss = sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]) / max(len(trades) - win_count, 1)
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
    
    with col1:
        st.metric("Total Return", f"{total_pnl_pct:.2f}%", f"${total_pnl:.2f}")
    with col2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Avg Win", format_currency(avg_win))
    with col4:
        st.metric("Avg Loss", format_currency(avg_loss))
    
    st.divider()
    
    # Equity curve
    st.subheader("Equity Curve")
    if trades:
        equity_values = [initial]
        for trade in sorted(trades, key=lambda x: x.get('close_date', '')):
            equity_values.append(equity_values[-1] + trade.get('pnl', 0))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=equity_values,
            mode='lines',
            name='Portfolio Value',
            fill='tozeroy',
            line=dict(color='#667eea', width=2)
        ))
        fig.add_hline(y=initial, line_dash="dash", line_color="gray", annotation_text="Initial Capital")
        fig.update_layout(
            title="Portfolio Performance Over Time",
            xaxis_title="Trade #",
            yaxis_title="Portfolio Value ($)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Monthly performance
    st.subheader("Performance by Month")
    if trades:
        monthly_data = {}
        for trade in trades:
            date_str = trade.get('close_date', '')
            if date_str:
                month = date_str[:7]  # YYYY-MM
                if month not in monthly_data:
                    monthly_data[month] = {'count': 0, 'pnl': 0}
                monthly_data[month]['count'] += 1
                monthly_data[month]['pnl'] += trade.get('pnl', 0)
        
        months = sorted(monthly_data.keys())
        counts = [monthly_data[m]['count'] for m in months]
        pnls = [monthly_data[m]['pnl'] for m in months]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=months, y=pnls, name='Monthly P&L', marker_color='#667eea'))
        fig.update_layout(
            title="Monthly P&L",
            xaxis_title="Month",
            yaxis_title="P&L ($)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# PAGE 5: TRADE HISTORY
# ============================================================================
elif page == "🔄 Trade History":
    st.title("🔄 Trade History")
    
    trade_df = load_trade_history()
    portfolio = load_portfolio_data()
    
    if trade_df is None or len(trade_df) == 0:
        st.info("No closed trades yet.")
        st.stop()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker_filter = st.multiselect(
            "Filter by Ticker",
            options=trade_df['ticker'].unique() if 'ticker' in trade_df.columns else [],
            default=[]
        )
    
    with col2:
        min_pnl = st.number_input("Minimum P&L ($)", value=0)
    
    with col3:
        trade_type_filter = st.selectbox(
            "Trade Type",
            ["All", "Winners", "Losers"]
        )
    
    # Apply filters
    filtered_df = trade_df.copy()
    
    if ticker_filter:
        filtered_df = filtered_df[filtered_df['ticker'].isin(ticker_filter)]
    
    if trade_type_filter == "Winners":
        filtered_df = filtered_df[filtered_df['pnl'] > 0]
    elif trade_type_filter == "Losers":
        filtered_df = filtered_df[filtered_df['pnl'] < 0]
    
    st.divider()
    
    # Trade statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Trades", len(filtered_df))
    with col2:
        winners = len(filtered_df[filtered_df['pnl'] > 0])
        st.metric("Winners", winners)
    with col3:
        losers = len(filtered_df[filtered_df['pnl'] < 0])
        st.metric("Losers", losers)
    with col4:
        total_pnl = filtered_df['pnl'].sum()
        st.metric("Total P&L", format_currency(total_pnl))
    with col5:
        if len(filtered_df) > 0:
            avg_pnl = filtered_df['pnl'].mean()
            st.metric("Avg Trade P&L", format_currency(avg_pnl))
    
    st.divider()
    
    # Trade table
    st.subheader("Closed Trades")
    
    display_df = filtered_df[[
        'ticker', 'entry_price', 'exit_price', 'shares',
        'entry_date', 'close_date', 'pnl', 'return_pct'
    ]].copy()
    
    # Format columns
    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.2f}")
    display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:.2f}")
    display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:.2f}")
    display_df['return_pct'] = display_df['return_pct'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.85em; margin-top: 30px;'>
    <p>John Trading System Dashboard | Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    <p>For more info: <a href='https://github.com/Manoj-1212/johnTrading' target='_blank'>GitHub Repository</a></p>
</div>
""", unsafe_allow_html=True)
