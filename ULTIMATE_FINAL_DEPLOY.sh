#!/bin/bash
# ULTIMATE FINAL DEPLOYMENT: All fixes applied (commit 050d76d)
# Clears cache, pulls latest code, restarts service
# Run on EC2: bash ULTIMATE_FINAL_DEPLOY.sh

set -e

echo "=========================================================================="
echo "ULTIMATE FINAL DEPLOYMENT - All Trading System Fixes (commit 050d76d)"
echo "=========================================================================="

REPO_DIR="/home/ubuntu/johntrading"

echo ""
echo "1️⃣  Stopping trading service..."
sudo systemctl stop johntrading
sleep 2
echo "   ✓ Service stopped"

echo ""
echo "2️⃣  Pulling latest code from GitHub..."
cd "$REPO_DIR"
git pull origin master
LATEST_COMMIT=$(git log -1 --pretty=format:%h)
echo "   ✓ Code updated to commit $LATEST_COMMIT"

echo ""
echo "3️⃣  Clearing corrupted cache files (critical!)..."
rm -rf "$REPO_DIR/phase7_realtime_streaming/cache/"*
mkdir -p "$REPO_DIR/phase7_realtime_streaming/cache"
echo "   ✓ Cache cleared - fresh download will begin"

echo ""
echo "4️⃣  Restarting trading service..."
sudo systemctl start johntrading
sleep 3
echo "   ✓ Service restarted"

echo ""
echo "5️⃣  Monitoring logs (Press Ctrl+C to stop)..."
echo "=========================================================================="
echo "Expected output within 30 seconds:"
echo "  ✓ Downloaded daily data for 21/21 tickers"
echo "  ✓ Loaded [TICKER] from cache: ### bars"
echo "  ✓ [TICKER] | BUY/SELL/HOLD | HIGH/MEDIUM/LOW | $### | Strength: #/7"
echo "  ✓ Executing trade order..."
echo "=========================================================================="
echo ""

journalctl -u johntrading -f --lines=50
