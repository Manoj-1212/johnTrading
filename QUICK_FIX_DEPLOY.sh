#!/bin/bash
# Quick deployment of critical indicator fixes
# Run on EC2: bash QUICK_FIX_DEPLOY.sh

set -e

echo "========================================================================"
echo "DEPLOYING CRITICAL INDICATOR FIX (f6cf3a8)"
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
echo "   ✓ Code updated"

echo ""
echo "3️⃣  Restarting trading service..."
sudo systemctl start johntrading
sleep 2
echo "   ✓ Service restarted"

echo ""
echo "4️⃣  Monitoring service (Press Ctrl+C to stop)..."
echo ""
journalctl -u johntrading -f --lines=30
