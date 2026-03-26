#!/bin/bash
# JOHN TRADING DASHBOARD - STARTUP SCRIPT
# Starts the Streamlit web dashboard for portfolio visualization

echo "=========================================="
echo "JOHN TRADING - PORTFOLIO DASHBOARD"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found."
    echo "Please run deploy_ec2.sh first or create venv with:"
    echo "  python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "⚠ Streamlit not found. Installing..."
    pip install streamlit plotly -q
fi

# Check if data exists
if [ ! -f "phase6_paper_trade/paper_portfolio.json" ]; then
    echo "⚠ Portfolio data not found."
    echo "Please run the trading system first:"
    echo "  python run_all.py"
    echo ""
fi

echo "✓ Starting Dashboard..."
echo ""
echo "📊 Dashboard will open at: http://localhost:8501"
echo "   (Ctrl+C to stop)"
echo ""
echo "Tips:"
echo "  - Refresh your browser to see latest data"
echo "  - Use Ctrl+Shift+R for hard refresh"
echo "  - Check 'Auto-refresh' in sidebar for real-time updates"
echo ""

# Start streamlit dashboard
streamlit run dashboard.py --logger.level=warning
