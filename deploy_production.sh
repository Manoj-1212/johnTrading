#!/bin/bash
# Deploy Phase 7-9 on Production Server
# Run this once on your EC2 instance to set up continuous automated trading

set -e  # Exit on any error

echo "=================================================="
echo "Phase 7-9 Production Deployment Script"
echo "=================================================="
echo ""

# Check if running as root (not required but helpful for systemd)
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Running as root - some commands may need sudo"
else
    echo "ℹ️  Running as regular user (home: $HOME)"
    SUDO="sudo"
fi

PROJECT_DIR="$HOME/johntrading"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="johntrading"

echo ""
echo "1️⃣  Checking environment..."
echo "   Project directory: $PROJECT_DIR"
echo "   Virtual environment: $VENV_DIR"

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    echo "   Creating project directory..."
    mkdir -p "$PROJECT_DIR"
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "❌ ERROR: .env file not found at $PROJECT_DIR/.env"
    echo ""
    echo "Please create $PROJECT_DIR/.env with:"
    echo "   APCA_API_KEY_ID=your_key"
    echo "   APCA_API_SECRET_KEY=your_secret"
    echo "   APCA_API_BASE_URL=https://paper-api.alpaca.markets"
    echo ""
    exit 1
else
    echo "   ✓ .env file found"
    
    # Validate and fix .env format for systemd
    echo "   Validating .env format for systemd compatibility..."
    
    # Check if .env has invalid shell syntax (export, $(), etc.)
    if grep -q "^export " "$PROJECT_DIR/.env" || grep -q '\$(' "$PROJECT_DIR/.env"; then
        echo "   ⚠️  .env has shell syntax (export, \$(), etc.) - systemd doesn't support this"
        echo "   Automatically fixing .env format..."
        
        # Remove 'export ' from beginning of lines
        sed -i 's/^export //' "$PROJECT_DIR/.env"
        
        # Remove comment lines that have shell syntax
        sed -i '/^#.*\$()/d' "$PROJECT_DIR/.env"
        
        echo "   ✓ .env format fixed (removed 'export' keywords)"
    fi
    
    # Check if required API keys are present
    if ! grep -q "APCA_API_KEY_ID=" "$PROJECT_DIR/.env" || ! grep -q "APCA_API_SECRET_KEY=" "$PROJECT_DIR/.env"; then
        echo "   ⚠️  WARNING: Required Alpaca API credentials not found in .env"
        echo "   Please add to $PROJECT_DIR/.env:"
        echo "      APCA_API_KEY_ID=your_key_id"
        echo "      APCA_API_SECRET_KEY=your_secret_key"
        echo "   Then run this script again"
        exit 1
    fi
    
    # Add APCA_API_BASE_URL if not present
    if ! grep -q "APCA_API_BASE_URL=" "$PROJECT_DIR/.env"; then
        echo "   Adding default APCA_API_BASE_URL (paper trading)..."
        echo "APCA_API_BASE_URL=https://paper-api.alpaca.markets" >> "$PROJECT_DIR/.env"
    fi
    
    echo "   ✓ .env file validated and compatible with systemd"
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 not found. Install with: sudo apt-get install python3"
    exit 1
fi
echo "   ✓ Python 3 available: $(python3 --version)"

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ ERROR: pip3 not found. Install with: sudo apt-get install python3-pip"
    exit 1
fi
echo "   ✓ pip3 available"

echo ""
echo "2️⃣  Setting up virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "   ✓ Virtual environment exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
echo "   ✓ Virtual environment activated"

echo ""
echo "3️⃣  Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
echo "   Updating pip... ✓"

# Install requirements if they exist
if [ -f "$PROJECT_DIR/requirements-phases-7-9.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements-phases-7-9.txt" > /dev/null 2>&1
    echo "   Installing trading system requirements... ✓"
else
    # Install minimum requirements
    pip install alpaca-py yfinance pandas numpy scipy pytz python-dateutil > /dev/null 2>&1
    echo "   Installing minimum requirements... ✓"
fi

echo ""
echo "4️⃣  Installing systemd service..."

# Check if systemd is available
if command -v systemctl &> /dev/null; then
    # Copy service file to systemd
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ -f "$PROJECT_DIR/trading_automation.service" ]; then
        echo "   Copying service file to $SERVICE_FILE..."
        $SUDO cp "$PROJECT_DIR/trading_automation.service" "$SERVICE_FILE"
        
        # Update paths in service file to use actual project directory
        $SUDO sed -i "s|/home/ubuntu/johntrading|$PROJECT_DIR|g" "$SERVICE_FILE"
        
        echo "   Reloading systemd daemon..."
        $SUDO systemctl daemon-reload
        
        echo "   ✓ Service installed"
    else
        echo "   ⚠️  trading_automation.service not found in $PROJECT_DIR"
    fi
else
    echo "   ⚠️  systemd not available. Skipping systemd service setup."
fi

echo ""
echo "5️⃣  Setting up logging..."

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "   Logs directory: $LOG_DIR"

JOURNAL_LOG="$LOG_DIR/systemd.log"
echo "   Journal logs: $JOURNAL_LOG"
echo "   View with: journalctl -u johntrading -f"

echo ""
echo "6️⃣  Setting up cron schedule..."

# Create cron job for daily restart at market open (9:30 AM EST)
CRON_JOB="30 9 * * 1-5 /usr/bin/systemctl restart johntrading"

# Check if cron job exists
if crontab -l 2>/dev/null | grep -q "systemctl restart johntrading"; then
    echo "   ✓ Cron job already scheduled"
else
    echo "   Adding daily restart at 9:30 AM EST (weekdays only)..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "   ✓ Cron job scheduled"
fi

echo ""
echo "=================================================="
echo "✅ Deployment Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the trading system:"
echo "   sudo systemctl start johntrading"
echo ""
echo "2. Check status:"
echo "   sudo systemctl status johntrading"
echo ""
echo "3. View logs in real-time:"
echo "   journalctl -u johntrading -f"
echo ""
echo "4. Enable auto-start on reboot:"
echo "   sudo systemctl enable johntrading"
echo ""
echo "5. Check if running:"
echo "   ps aux | grep run_phase9"
echo ""
echo "6. Review cron jobs:"
echo "   crontab -l"
echo ""
echo "Useful commands:"
echo "  systemctl stop johntrading        # Stop trading"
echo "  systemctl restart johntrading     # Restart trading"
echo "  systemctl disable johntrading     # Disable auto-start"
echo "  journalctl -u johntrading -n 100  # View last 100 lines"
echo ""
