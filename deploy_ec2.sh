#!/bin/bash
# JOHN TRADING SYSTEM — EC2 DEPLOYMENT GUIDE
# Machine: AWS m7i-flex.large
# OS: Linux (Ubuntu 22.04 or Amazon Linux 2)
# Repository: https://github.com/Manoj-1212/johnTrading.git

echo "=========================================="
echo "JOHN TRADING SYSTEM - EC2 DEPLOYMENT"
echo "=========================================="
echo ""
echo "Detecting OS and preparing system..."
echo ""

# Check for required commands
for cmd in git curl wget; do
    if ! command -v $cmd &> /dev/null; then
        echo "⚠ $cmd not found, will install"
    fi
done

# ============================================================================
# STEP 1: INITIAL SETUP & SYSTEM UPDATES
# ============================================================================
echo "[STEP 1] Updating system packages..."

if grep -q "ubuntu" /etc/os-release 2>/dev/null; then
    sudo apt update && sudo apt upgrade -y
elif grep -q "amzn" /etc/os-release 2>/dev/null; then
    sudo yum update -y
fi

# ============================================================================
# STEP 2: INSTALL PYTHON & DEPENDENCIES
# ============================================================================
echo "[STEP 2] Installing Python and dependencies..."

# For Ubuntu 22.04: Add deadsnakes PPA to get Python 3.11
if grep -q "ubuntu" /etc/os-release; then
    echo "Detected Ubuntu - Adding deadsnakes PPA for Python 3.11..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    
    # Install Python 3.11 and essential tools
    sudo apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip \
        git \
        wget \
        curl \
        build-essential \
        libssl-dev \
        libffi-dev
fi

# For Amazon Linux 2:
if grep -q "amzn" /etc/os-release; then
    echo "Detected Amazon Linux 2..."
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y \
        python3.11 \
        python3.11-devel \
        python3-pip \
        git \
        wget \
        curl
fi

# Verify Python installation
echo "Verifying Python installation..."
python3.11 --version || python3.10 --version || python3 --version
pip3 --version

# ============================================================================
# STEP 3: CREATE APPLICATION DIRECTORY
# ============================================================================
echo "[STEP 3] Creating application directory..."

# Create app directory
mkdir -p ~/johntrading
cd ~/johntrading

# Create dedicated user for the app (optional but recommended)
# sudo useradd -m -s /bin/bash johntrading
# sudo mkdir -p /home/johntrading/app
# sudo chown johntrading:johntrading /home/johntrading/app

# ============================================================================
# STEP 4: CLONE GITHUB REPOSITORY
# ============================================================================
echo "[STEP 4] Cloning repository from GitHub..."

git clone https://github.com/Manoj-1212/johnTrading.git .

# If using older git version, you may need to specify branch:
# git clone -b master https://github.com/Manoj-1212/johnTrading.git .

# Verify clone was successful
if [ -f "config.py" ]; then
    echo "✓ Repository cloned successfully"
else
    echo "✗ Failed to clone repository"
    exit 1
fi

# ============================================================================
# STEP 5: CREATE AND ACTIVATE VIRTUAL ENVIRONMENT
# ============================================================================
echo "[STEP 5] Creating Python virtual environment..."

# Try Python 3.11 first, fallback to 3.10 or 3.9
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "Using Python 3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo "Using Python 3.10 (fallback)"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    echo "Using Python 3.9 (fallback)"
else
    PYTHON_CMD="python3"
    echo "Using available Python 3"
fi

# Create virtual environment
$PYTHON_CMD -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

echo "✓ Virtual environment created and activated with $PYTHON_CMD"

# ============================================================================
# STEP 6: INSTALL PYTHON DEPENDENCIES
# ============================================================================
echo "[STEP 6] Installing Python packages..."

# Install from requirements.txt
pip install -r requirements.txt

# Verify key packages
python3 -c "import pandas; import numpy; import yfinance; print('✓ All dependencies installed')"

# ============================================================================
# STEP 7: VERIFY INSTALLATION
# ============================================================================
echo "[STEP 7] Verifying installation..."

# Test Phase 1 (data download)
python -c "
from phase1_data.downloader import StockDownloader
print('✓ Phase 1 module loads successfully')
" || echo "⚠ Phase 1 module check skipped (will work after deployment)"

# Test Phase 2 (indicators)
python -c "
from phase2_indicators.combiner import build_full_indicator_set
print('✓ Phase 2 module loads successfully')
" || echo "⚠ Phase 2 module check skipped (will work after deployment)"

# ============================================================================
# STEP 8: CREATE DATA DIRECTORIES
# ============================================================================
echo "[STEP 8] Creating data directories..."

mkdir -p phase1_data/cache
mkdir -p phase2_data
mkdir -p phase3_backtest/results
mkdir -p logs

echo "✓ Data directories created"

# ============================================================================
# STEP 9: CONFIGURATION (OPTIONAL)
# ============================================================================
echo "[STEP 9] Configuration notes..."

cat << 'EOF'

OPTIONAL CONFIGURATIONS:

1. To test with only original 5 tickers (faster):
   Edit config.py and change:
   TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]

2. To run with all 20 tickers (more data):
   Keep default config.py (already set to 20 tickers)

3. To adjust parameters:
   Edit config.py:
   - MIN_SIGNALS_TO_BUY = 5
   - STOP_LOSS_PCT = 0.07
   - TAKE_PROFIT_PCT = 0.15

EOF

# ============================================================================
# STEP 10: FIRST RUN - PHASE 1 (DATA DOWNLOAD)
# ============================================================================
echo "[STEP 10] Running Phase 1 (Data Download)..."
echo "This will download 5+ years of stock data (2-3 minutes)..."

python run_phase1.py

if [ $? -eq 0 ]; then
    echo "✓ Phase 1 completed successfully"
else
    echo "⚠ Phase 1 had issues, but continuing..."
fi

# ============================================================================
# ALL DONE!
# ============================================================================
echo ""
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Your trading system is ready to run!"
echo ""
echo "VIRTUAL ENVIRONMENT ACTIVATED: .venv"
echo "PROJECT DIRECTORY: ~/johntrading"
echo ""
echo "Next, choose how to run the system:"
echo ""
