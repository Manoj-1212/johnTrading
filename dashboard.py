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
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------------------
# Alpaca helpers (lazy import — only loaded when the Trade Report page is used)
# ---------------------------------------------------------------------------
def _load_env_file():
    """
    Load KEY=VALUE pairs from .env file into os.environ.
    Handles both bare KEY=VALUE (systemd style) and export KEY=VALUE (bash style).
    Searched: working dir, script dir, /home/ubuntu/johntrading/.env
    """
    candidates = [
        Path('.env'),
        Path(__file__).parent / '.env',
        Path('/home/ubuntu/johntrading/.env'),
    ]
    for env_path in candidates:
        if env_path.exists():
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if line.startswith('export '):
                            line = line[7:].strip()
                        if '=' in line:
                            k, _, v = line.partition('=')
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k and not os.environ.get(k):
                                os.environ[k] = v
                return
            except Exception:
                pass


def _get_alpaca_client():
    """Return a TradingClient or None on failure."""
    # Ensure .env credentials are loaded into this process if not already present
    if not os.getenv('APCA_API_KEY_ID'):
        _load_env_file()
    try:
        from alpaca.trading.client import TradingClient
        api_key    = os.getenv('APCA_API_KEY_ID')
        secret_key = os.getenv('APCA_API_SECRET_KEY')
        if not api_key or not secret_key or api_key == 'your_api_key_here':
            return None
        base_url = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')
        client = TradingClient(api_key, secret_key, url_override=base_url)
        return client
    except Exception:
        return None


@st.cache_data(ttl=60)
def fetch_alpaca_account():
    """Fetch live account info from Alpaca (cached 60 s)."""
    client = _get_alpaca_client()
    if not client:
        return None
    try:
        acct = client.get_account()
        return {
            'portfolio_value': float(acct.portfolio_value),
            'cash':            float(acct.cash),
            'equity':          float(acct.equity),
            'buying_power':    float(acct.buying_power),
            'last_equity':     float(acct.last_equity),
            'account_number':  str(acct.account_number),
        }
    except Exception:
        return None


@st.cache_data(ttl=60)
def fetch_alpaca_positions():
    """Fetch open positions from Alpaca (cached 60 s)."""
    client = _get_alpaca_client()
    if not client:
        return []
    try:
        positions = client.get_all_positions()
        rows = []
        for p in positions:
            rows.append({
                'Symbol':          p.symbol,
                'Side':            str(p.side).upper(),
                'Qty':             float(p.qty),
                'Avg Entry ($)':   float(p.avg_entry_price),
                'Current ($)':     float(p.current_price),
                'Market Value ($)': float(p.market_value),
                'Unrealized P&L ($)': float(p.unrealized_pl),
                'P&L %':           float(p.unrealized_plpc) * 100,
                'Cost Basis ($)':  float(p.cost_basis),
            })
        return rows
    except Exception:
        return []


@st.cache_data(ttl=120)
def fetch_alpaca_filled_orders(days: int = 30):
    """Fetch closed/filled orders from Alpaca (cached 2 min)."""
    client = _get_alpaca_client()
    if not client:
        return []
    try:
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums   import QueryOrderStatus
        import pytz
        since = datetime.now(tz=pytz.UTC) - timedelta(days=days)
        req   = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=500, after=since)
        orders = client.get_orders(filter=req)
        rows = []
        for o in orders:
            if str(o.status) not in ('filled', 'partially_filled'):
                continue
            filled_at = o.filled_at
            if filled_at and hasattr(filled_at, 'strftime'):
                ts = filled_at.strftime('%Y-%m-%d %H:%M:%S')
                date_only = filled_at.strftime('%Y-%m-%d')
            else:
                ts = str(filled_at) if filled_at else ''
                date_only = ts[:10] if ts else ''
            rows.append({
                'Date':            date_only,
                'Time':            ts,
                'Symbol':          o.symbol,
                'Side':            str(o.side).upper(),
                'Qty':             float(o.filled_qty or 0),
                'Avg Fill ($)':    float(o.filled_avg_price or 0),
                'Order Value ($)': float(o.filled_qty or 0) * float(o.filled_avg_price or 0),
                'Type':            str(o.type),
                'Status':          str(o.status),
                'Order ID':        str(o.id)[:8] + '…',
            })
        return rows
    except Exception:
        return []


@st.cache_data(ttl=300)
def fetch_alpaca_portfolio_history(period: str = '1M', timeframe: str = '1D'):
    """Fetch portfolio equity history from Alpaca (cached 5 min)."""
    client = _get_alpaca_client()
    if not client:
        return None
    try:
        from alpaca.trading.requests import GetPortfolioHistoryRequest
        req  = GetPortfolioHistoryRequest(period=period, timeframe=timeframe)
        hist = client.get_portfolio_history(filter=req)
        if not hist or not hist.timestamp:
            return None
        import pytz
        rows = []
        for ts, eq, pnl, pnl_pct in zip(
            hist.timestamp,
            hist.equity,
            hist.profit_loss,
            hist.profit_loss_pct,
        ):
            dt = datetime.fromtimestamp(ts, tz=pytz.UTC).strftime('%Y-%m-%d')
            rows.append({
                'Date':    dt,
                'Equity':  float(eq   or 0),
                'P&L ($)': float(pnl  or 0),
                'P&L (%)': float(pnl_pct or 0) * 100,
            })
        return pd.DataFrame(rows)
    except Exception:
        return None


def _match_round_trips(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match BUY→SELL pairs from filled orders to calculate realised P&L.
    Uses FIFO (first-in-first-out) per symbol.
    """
    if orders_df.empty:
        return pd.DataFrame()

    trips = []
    buys  = {}  # symbol -> list of (qty, price, date)

    for _, row in orders_df.sort_values('Time').iterrows():
        sym   = row['Symbol']
        side  = row['Side'].upper().replace('ORDERSSIDE.', '').strip()
        qty   = float(row['Qty'])
        price = float(row['Avg Fill ($)'])
        date  = row['Date']

        if 'BUY' in side:
            if sym not in buys:
                buys[sym] = []
            buys[sym].append({'qty': qty, 'price': price, 'date': date})

        elif 'SELL' in side and sym in buys and buys[sym]:
            remaining = qty
            while remaining > 0 and buys[sym]:
                lot     = buys[sym][0]
                matched = min(remaining, lot['qty'])
                pnl     = (price - lot['price']) * matched
                pnl_pct = ((price - lot['price']) / lot['price']) * 100 if lot['price'] else 0
                trips.append({
                    'Symbol':      sym,
                    'Buy Date':    lot['date'],
                    'Sell Date':   date,
                    'Qty':         matched,
                    'Entry ($)':   lot['price'],
                    'Exit ($)':    price,
                    'P&L ($)':     round(pnl, 2),
                    'P&L %':       round(pnl_pct, 2),
                    'Result':      '✅ Win' if pnl > 0 else ('⬜ BE' if pnl == 0 else '❌ Loss'),
                })
                lot['qty'] -= matched
                remaining  -= matched
                if lot['qty'] <= 0:
                    buys[sym].pop(0)

    return pd.DataFrame(trips)


def _load_session_logs():
    """Load all local session JSON logs from phase9_production_trading/logs/."""
    log_dir = Path('phase9_production_trading/logs')
    if not log_dir.exists():
        return []
    sessions = []
    for f in sorted(log_dir.glob('session_*.json'), reverse=True):
        try:
            with open(f) as fh:
                data = json.load(fh)
            data['_filename'] = f.name
            sessions.append(data)
        except Exception:
            pass
    return sessions

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
    "🔄 Trade History",
    "🏆 Alpaca Trade Report",
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
# PAGE 6: ALPACA TRADE REPORT
# ============================================================================
elif page == "🏆 Alpaca Trade Report":
    st.title("🏆 Alpaca Trade Report")
    st.caption("Live data pulled from Alpaca Paper Trading API · Refreshes every 60 s")

    # ── Connection check ──────────────────────────────────────────────────
    acct = fetch_alpaca_account()
    connected = acct is not None

    if not connected:
        st.warning(
            "⚠️ Alpaca credentials not found in environment. "
            "Set **APCA_API_KEY_ID** and **APCA_API_SECRET_KEY** to see live data.\n\n"
            "Showing local session logs below (if any).",
            icon="⚠️"
        )

    # ── 1. Daily Summary Row ──────────────────────────────────────────────
    st.subheader("📊 Daily Summary")

    if connected:
        today_pnl_dollar = acct['equity'] - acct['last_equity']
        today_pnl_pct    = (today_pnl_dollar / acct['last_equity'] * 100) if acct['last_equity'] else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("💰 Portfolio Value",  f"${acct['portfolio_value']:,.2f}")
        c2.metric("🏦 Equity",           f"${acct['equity']:,.2f}")
        c3.metric("💵 Cash",             f"${acct['cash']:,.2f}")
        c4.metric("📈 Today's P&L",
                  f"${today_pnl_dollar:+,.2f}",
                  delta=f"{today_pnl_pct:+.2f}%",
                  delta_color="normal")
        c5.metric("⚡ Buying Power",     f"${acct['buying_power']:,.2f}")

        st.caption(f"Account: {acct['account_number']}  |  Mode: PAPER TRADING")
    else:
        st.info("Connect to Alpaca to see live account summary.")

    st.divider()

    # ── 2. Open Positions ─────────────────────────────────────────────────
    st.subheader("📍 Open Positions (Live)")

    if connected:
        positions = fetch_alpaca_positions()
        if positions:
            pos_df = pd.DataFrame(positions)

            # Colour-coded P&L column
            def _pnl_str(v):
                return f"+${v:,.2f}" if v >= 0 else f"-${abs(v):,.2f}"

            total_unreal = pos_df["Unrealized P&L ($)"].sum()
            total_market = pos_df["Market Value ($)"].sum()

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Open Positions", len(pos_df))
            col_b.metric("Total Market Value", f"${total_market:,.2f}")
            col_c.metric("Total Unrealised P&L", _pnl_str(total_unreal),
                         delta_color="normal")

            st.dataframe(
                pos_df.style
                    .format({
                        "Qty":               "{:.2f}",
                        "Avg Entry ($)":     "${:,.2f}",
                        "Current ($)":       "${:,.2f}",
                        "Market Value ($)":  "${:,.2f}",
                        "Unrealized P&L ($)":"${:+,.2f}",
                        "P&L %":             "{:+.2f}%",
                        "Cost Basis ($)":    "${:,.2f}",
                    })
                    .applymap(
                        lambda v: "color: #00cc44" if isinstance(v, (int, float)) and v > 0
                                  else ("color: #ff4444" if isinstance(v, (int, float)) and v < 0 else ""),
                        subset=["Unrealized P&L ($)", "P&L %"]
                    ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No open positions at the moment.")
    else:
        st.info("Connect to Alpaca to see live positions.")

    st.divider()

    # ── 3. Filled Orders (today vs all) ──────────────────────────────────
    st.subheader("✅ Filled Orders")

    days_back = st.slider("Show orders from last N days", 1, 90, 30, key="orders_days")

    if connected:
        all_orders = fetch_alpaca_filled_orders(days=days_back)
        if all_orders:
            orders_df = pd.DataFrame(all_orders)

            # Filter: today only toggle
            show_today = st.checkbox("Today only", value=False, key="today_only")
            if show_today:
                today_str  = datetime.now().strftime('%Y-%m-%d')
                orders_df  = orders_df[orders_df['Date'] == today_str]

            if not orders_df.empty:
                # Summary chips
                buys  = orders_df[orders_df['Side'].str.contains('BUY',  case=False, na=False)]
                sells = orders_df[orders_df['Side'].str.contains('SELL', case=False, na=False)]

                ch1, ch2, ch3 = st.columns(3)
                ch1.metric("Total Filled Orders", len(orders_df))
                ch2.metric("Buy Orders",  len(buys),
                           delta=f"${buys['Order Value ($)'].sum():,.0f} notional")
                ch3.metric("Sell Orders", len(sells),
                           delta=f"${sells['Order Value ($)'].sum():,.0f} notional")

                st.dataframe(
                    orders_df.style.format({
                        "Qty":             "{:.2f}",
                        "Avg Fill ($)":    "${:,.2f}",
                        "Order Value ($)": "${:,.2f}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Side": st.column_config.TextColumn(width="small"),
                        "Type": st.column_config.TextColumn(width="small"),
                    }
                )
            else:
                st.info("No filled orders match the current filter.")
        else:
            st.info("No filled orders found in the selected period.")
    else:
        st.info("Connect to Alpaca to see filled orders.")

    st.divider()

    # ── 4. Completed Round-Trips (Realised P&L) ───────────────────────────
    st.subheader("💰 Completed Trades (Realised P&L)")
    st.caption("BUY → SELL pairs matched via FIFO per symbol")

    if connected:
        all_orders_data = fetch_alpaca_filled_orders(days=days_back)
        if all_orders_data:
            o_df   = pd.DataFrame(all_orders_data)
            rt_df  = _match_round_trips(o_df)

            if not rt_df.empty:
                total_realised = rt_df['P&L ($)'].sum()
                wins   = (rt_df['P&L ($)'] > 0).sum()
                losses = (rt_df['P&L ($)'] < 0).sum()
                win_rate = (wins / len(rt_df) * 100) if len(rt_df) else 0
                avg_win  = rt_df.loc[rt_df['P&L ($)'] > 0, 'P&L ($)'].mean() if wins  else 0
                avg_loss = rt_df.loc[rt_df['P&L ($)'] < 0, 'P&L ($)'].mean() if losses else 0
                profit_factor = abs(rt_df.loc[rt_df['P&L ($)'] > 0, 'P&L ($)'].sum() /
                                    rt_df.loc[rt_df['P&L ($)'] < 0, 'P&L ($)'].sum()) \
                                if losses > 0 else float('inf')

                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("Round-Trips",    len(rt_df))
                m2.metric("Realised P&L",   f"${total_realised:+,.2f}",
                          delta_color="normal")
                m3.metric("Win Rate",        f"{win_rate:.1f}%")
                m4.metric("Avg Win",         f"${avg_win:,.2f}")
                m5.metric("Avg Loss",        f"${avg_loss:,.2f}")
                m6.metric("Profit Factor",
                          f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")

                st.dataframe(
                    rt_df.style
                        .format({
                            "Qty":       "{:.2f}",
                            "Entry ($)": "${:,.2f}",
                            "Exit ($)":  "${:,.2f}",
                            "P&L ($)":   "${:+,.2f}",
                            "P&L %":     "{:+.2f}%",
                        })
                        .applymap(
                            lambda v: "color: #00cc44" if isinstance(v, (int, float)) and v > 0
                                      else ("color: #ff4444" if isinstance(v, (int, float)) and v < 0 else ""),
                            subset=["P&L ($)", "P&L %"]
                        ),
                    use_container_width=True,
                    hide_index=True,
                )

                # P&L waterfall per symbol
                st.markdown("#### P&L by Symbol")
                symbol_pnl = rt_df.groupby('Symbol')['P&L ($)'].sum().reset_index().sort_values('P&L ($)')
                fig_bar = go.Figure(go.Bar(
                    x=symbol_pnl['Symbol'],
                    y=symbol_pnl['P&L ($)'],
                    marker_color=[
                        '#00cc44' if v >= 0 else '#ff4444'
                        for v in symbol_pnl['P&L ($)']
                    ],
                    text=[f"${v:+,.2f}" for v in symbol_pnl['P&L ($)']],
                    textposition='outside',
                ))
                fig_bar.update_layout(
                    title="Realised P&L per Symbol",
                    yaxis_title="P&L ($)",
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            else:
                st.info("No completed round-trip trades yet (need both BUY and corresponding SELL).")
        else:
            st.info("No order data available.")
    else:
        st.info("Connect to Alpaca to see completed trades.")

    st.divider()

    # ── 5. Daily P&L Chart ────────────────────────────────────────────────
    st.subheader("📅 Daily P&L (Portfolio History)")

    if connected:
        hist_period = st.selectbox(
            "History period",
            ["1W", "1M", "3M", "6M", "1A"],
            index=1,
            key="hist_period",
        )
        hist_df = fetch_alpaca_portfolio_history(period=hist_period, timeframe="1D")

        if hist_df is not None and not hist_df.empty:
            # Daily P&L bar
            fig_daily = go.Figure()
            fig_daily.add_trace(go.Bar(
                x=hist_df['Date'],
                y=hist_df['P&L ($)'],
                name='Daily P&L',
                marker_color=[
                    '#00cc44' if v >= 0 else '#ff4444'
                    for v in hist_df['P&L ($)']
                ],
                text=[f"${v:+,.2f}" for v in hist_df['P&L ($)']],
                textposition='outside',
            ))
            fig_daily.update_layout(
                title="Daily P&L",
                xaxis_title="Date",
                yaxis_title="P&L ($)",
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_daily, use_container_width=True)

            # Equity curve
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(
                x=hist_df['Date'],
                y=hist_df['Equity'],
                mode='lines+markers',
                name='Equity',
                line=dict(color='#667eea', width=2),
                fill='tozeroy',
                fillcolor='rgba(102,126,234,0.12)',
            ))
            fig_eq.update_layout(
                title="Equity Curve",
                xaxis_title="Date",
                yaxis_title="Equity ($)",
                height=350,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_eq, use_container_width=True)

            # Compact table
            with st.expander("📋 Daily P&L Table"):
                st.dataframe(
                    hist_df.style.format({
                        'Equity':  '${:,.2f}',
                        'P&L ($)': '${:+,.2f}',
                        'P&L (%)': '{:+.2f}%',
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("Portfolio history unavailable. Alpaca may not return history for brand-new accounts.")
    else:
        st.info("Connect to Alpaca to see daily P&L charts.")

    st.divider()

    # ── 6. Session Logs (local fallback + history) ────────────────────────
    st.subheader("📝 Session Logs")

    sessions = _load_session_logs()
    if sessions:
        log_rows = []
        for s in sessions:
            acct_s = s.get('account', {})
            trade_s = s.get('trading', {})
            init_v  = acct_s.get('initial_value', 0)
            final_v = acct_s.get('final_value', 0)
            pnl_s   = final_v - init_v
            log_rows.append({
                'File':          s['_filename'],
                'Start':         s.get('session_start', '')[:19],
                'End':           s.get('session_end',   '')[:19],
                'Mode':          s.get('mode', ''),
                'Initial ($)':   init_v,
                'Final ($)':     final_v,
                'Session P&L ($)': pnl_s,
                'Trades':        trade_s.get('total_trades', 0),
                'Blocked':       len(trade_s.get('blocked_trades', [])),
            })
        log_df = pd.DataFrame(log_rows)

        total_sessions_pnl = log_df['Session P&L ($)'].sum()
        st.metric("Cumulative Session P&L (all logs)", f"${total_sessions_pnl:+,.2f}")

        st.dataframe(
            log_df.style.format({
                'Initial ($)':     '${:,.2f}',
                'Final ($)':       '${:,.2f}',
                'Session P&L ($)': '${:+,.2f}',
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Drill into a session
        chosen = st.selectbox("Inspect session", [r['File'] for r in log_rows], key="session_select")
        chosen_data = next((s for s in sessions if s['_filename'] == chosen), None)
        if chosen_data:
            with st.expander("Individual trades in this session", expanded=True):
                t_list = chosen_data.get('trading', {}).get('trades', [])
                if t_list:
                    t_df = pd.DataFrame(t_list)
                    st.dataframe(t_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No trades recorded in this session.")

            with st.expander("Blocked (risk) events in this session"):
                b_list = chosen_data.get('trading', {}).get('blocked_trades', [])
                if b_list:
                    st.dataframe(pd.DataFrame(b_list), use_container_width=True, hide_index=True)
                else:
                    st.info("No blocked events in this session.")
    else:
        st.info("No session log files found at `phase9_production_trading/logs/`.")

    # Refresh button
    if st.button("🔄 Refresh Report", key="refresh_report"):
        st.cache_data.clear()
        st.rerun()


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
