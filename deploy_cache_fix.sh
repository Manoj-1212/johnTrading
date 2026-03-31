#!/bin/bash
# Deploy CSV cache fix on EC2
# Run as: bash deploy_cache_fix.sh

set -e

echo "========================================================================"
echo "DEPLOYING CSV CACHE FIX TO EC2"
echo "========================================================================"

REPO_DIR="/home/ubuntu/johntrading"

echo ""
echo "1️⃣  Stopping trading service..."
sudo systemctl stop johntrading
echo "   ✓ Service stopped"

echo ""
echo "2️⃣  Pulling latest code..."
cd "$REPO_DIR"
git pull origin master
echo "   ✓ Code updated (commit 0a432a3)"

echo ""
echo "3️⃣  Clearing old cache..."
rm -rf "$REPO_DIR/phase7_realtime_streaming/cache"
mkdir -p "$REPO_DIR/phase7_realtime_streaming/cache"
echo "   ✓ Old cache cleared"

echo ""
echo "4️⃣  Downloading fresh daily data..."
python3 fix_data_cache.py
echo "   ✓ Daily data downloaded and cached"

echo ""
echo "5️⃣  Restarting trading service..."
sudo systemctl start johntrading
sleep 2
echo "   ✓ Service restarted"

echo ""
echo "6️⃣  Monitoring service..."
echo "   (Press Ctrl+C to stop monitoring)"
echo ""
journalctl -u johntrading -f --lines=20

