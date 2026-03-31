#!/bin/bash
# FINAL FIX: Clear old string-type cache and deploy numeric fix
# Run on EC2: bash FINAL_NUMERIC_FIX.sh

set -e

echo "========================================================================"
echo "FINAL NUMERIC FIX DEPLOYMENT"
echo "========================================================================"

REPO_DIR="/home/ubuntu/johntrading"

echo ""
echo "1️⃣  Stopping trading service..."
sudo systemctl stop johntrading
echo "   ✓ Service stopped"

echo ""
echo "2️⃣  Pulling latest code (commit 2984031)..."
cd "$REPO_DIR"
git pull origin master
echo "   ✓ Code updated"

echo ""
echo "3️⃣  Clearing corrupted cache files..."
rm -rf "$REPO_DIR/phase7_realtime_streaming/cache/"*
mkdir -p "$REPO_DIR/phase7_realtime_streaming/cache"
echo "   ✓ Cache cleared"

echo ""
echo "4️⃣  Restarting trading service..."
sudo systemctl start johntrading
sleep 3
echo "   ✓ Service restarted"

echo ""
echo "5️⃣  Service will auto-download fresh data..."
echo "   Monitoring logs (Press Ctrl+C to stop)..."
echo ""
journalctl -u johntrading -f --lines=50
