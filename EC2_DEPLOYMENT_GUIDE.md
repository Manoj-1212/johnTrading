# EC2 DEPLOYMENT GUIDE — JOHN TRADING SYSTEM

## 📋 Quick Deploy (Copy-Paste Commands)

### Pre-requisites
- ✅ AWS EC2 instance running (m7i-flex.large or larger)
- ✅ Instance has internet access to download data
- ✅ Security group allows SSH (port 22)
- ✅ ~20GB free disk space (for data cache)

---

## 🚀 STEP-BY-STEP DEPLOYMENT

### 1. Connect to Your EC2 Instance

```bash
# Using your key pair (replace path and IP)
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip

# OR if using EC2 Instance Connect (easier):
# Just click "Connect" in AWS console
```

---

### 2. Run the Automated Deployment Script

```bash
# Download deployment script directly from GitHub
curl -O https://raw.githubusercontent.com/Manoj-1212/johnTrading/master/deploy_ec2.sh

# Make it executable
chmod +x deploy_ec2.sh

# Run the script
./deploy_ec2.sh
```

This script will:
- ✅ Update system packages
- ✅ Install Python 3.11
- ✅ Clone your repository
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Download stock data (Phase 1)
- ✅ Verify installation

**Expected time:** 5-10 minutes

---

### 3. Activate Virtual Environment

After deployment script finishes:

```bash
cd ~/johntrading
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

---

## 🎯 HOW TO RUN THE TRADING SYSTEM

Choose one of the methods below:

### Option A: Manual Run (One-time)

```bash
cd ~/johntrading
source .venv/bin/activate

# Run all 6 phases
python run_all.py

# OR run individual phases
python run_phase1.py    # Download data
python run_phase2.py    # Calculate indicators
python run_phase3.py    # Run backtest
python run_phase4.py    # Generate signals
python run_phase5.py    # Analysis
python run_phase6.py    # Portfolio status
```

**Output:** Results in console + CSV files in `phase3_backtest/results/`

---

### Option B: Scheduled via Cron (Daily at 4 PM UTC)

Recommended for live trading signals generation.

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 4 PM UTC (after market close):
0 16 * * * cd /home/ubuntu/johntrading && source .venv/bin/activate && python run_all.py >> logs/trading.log 2>&1

# Verify cron job was added
crontab -l
```

The script will:
- Download today's market data
- Calculate all indicators
- Generate buy/sell/hold signals
- Log results to `logs/trading.log`

---

### Option C: Run as Background Service (systemd)

For persistent, monitored execution:

```bash
# Create systemd service file
sudo tee /etc/systemd/system/johntrading.service > /dev/null << 'EOF'
[Unit]
Description=John Trading System
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/johntrading
Environment="PATH=/home/ubuntu/johntrading/.venv/bin"
ExecStart=/home/ubuntu/johntrading/.venv/bin/python /home/ubuntu/johntrading/run_all.py
Restart=on-failure
RestartSec=300

StandardOutput=append:/home/ubuntu/johntrading/logs/trading.log
StandardError=append:/home/ubuntu/johntrading/logs/errors.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable johntrading.service
sudo systemctl start johntrading.service

# Check status
sudo systemctl status johntrading.service

# View logs
tail -f /home/ubuntu/johntrading/logs/trading.log
```

---

### Option D: Run Full Analysis Suite

For parameter optimization and sensitivity testing:

```bash
cd ~/johntrading
source .venv/bin/activate

# Run all improvement analyses
python run_analysis_improvements.py

# This will:
# - Test MIN_SIGNALS_TO_BUY = [3,4,5,6,7]
# - Check indicator correlation
# - Validate Elliott Wave/Fibonacci
# - Compare realistic vs idealistic backtest
# - Test all 20 tickers
# Expected time: 15-30 minutes
```

Output: Complete optimization report

---

## 📊 RUNNING ON A SCHEDULE

### Recommended Schedule

```
4 PM UTC Daily     → python run_all.py (generate signals after market close)
Weekly (Sunday)    → python run_analysis_improvements.py (deep analysis)
Monthly            → Review results, update parameters
```

### Set Up Daily Signals at 4 PM UTC

```bash
# Edit crontab
crontab -e

# Add daily signal generation at 4 PM UTC
0 16 * * * cd /home/ubuntu/johntrading && source .venv/bin/activate && python run_phase4.py >> logs/signals.log 2>&1

# View current cron jobs
crontab -l
```

---

## 🔄 VIEWING RESULTS

### See Today's Signals

```bash
cd ~/johntrading
source .venv/bin/activate

# Generate today's trading signals
python run_phase4.py

# Output example:
# 🟡 HOLD SIGNALS (2):
#    AAPL @ $249.06 | Signal Count: 4/7 | Active: trend, rsi, volume, atr
#    TSLA @ $403.84 | Signal Count: 4/7 | Active: trend, rsi, volume, atr
# 🔴 SELL SIGNALS (3):
#    MSFT @ $417.46 | Signal Count: 1/7 | Active: atr
```

### Check Backtest Results

```bash
# View recent trades
python run_phase3.py

# Output: Backtest metrics table with alpha vs VOO
```

### View Paper Portfolio

```bash
# Check current positions and P&L
python run_phase6.py

# Output: Portfolio status, open positions, closed trades
```

### View Logs

```bash
# If running as cron or service
tail -f logs/trading.log
tail -f logs/errors.log

# Full log history
cat logs/trading.log | grep "SIGNAL\|TRADE\|ERROR"
```

---

## 🐛 TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'yfinance'"

```bash
# Reinstall dependencies
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Issue: "Data download failed"

```bash
# Check internet connectivity
ping google.com

# Try downloading manually
python -c "
import yfinance as yf
data = yf.download('AAPL', start='2023-01-01', end='2024-01-01')
print(f'Downloaded {len(data)} bars')
"
```

### Issue: "Port 22 not accessible"

Check AWS Security Group:
- Inbound rules → SSH (22) must allow your IP
- Edit: Right-click security group → Edit inbound rules

### Issue: "Out of disk space"

Check disk usage:
```bash
df -h

# If full, clear cache (will re-download on next run)
rm -rf /home/ubuntu/johntrading/phase1_data/cache/
```

### Issue: "Python version mismatch"

```bash
# Check installed Python
python3.11 --version

# If not installed, add repository first:
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv
```

---

## 📈 MONITORING

### Real-time Log Monitoring

```bash
# Watch log file live
tail -f ~/johntrading/logs/trading.log

# Search for signals in logs
grep "SIGNAL" ~/johntrading/logs/trading.log

# Count trades per day
grep "TRADE" ~/johntrading/logs/trading.log | wc -l
```

### System Resource Monitoring

```bash
# Check CPU and memory usage
htop

# Check disk space
df -h

# Check specific process
ps aux | grep python

# Kill hung process (if needed)
killall -9 python
```

### AWS CloudWatch Integration (Optional)

```bash
# Install CloudWatch agent
sudo apt install awslogs

# Configure to send logs to CloudWatch
# See AWS documentation for setup
```

---

## 🔐 SECURITY BEST PRACTICES

### 1. Restrict SSH Access

```bash
# Edit SSH config to allow only your IP
sudo nano /etc/ssh/sshd_config

# Add/modify:
# AllowUsers ubuntu@YOUR.IP.ADDRESS
# Port 22
# PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### 2. Set Up Firewall

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS if needed
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verify
sudo ufw status
```

### 3. Store Credentials Securely

```bash
# Never hardcode API keys in code
# If using API keys, store in AWS Secrets Manager or environment variables

# Example: Store GitHub token
export GITHUB_TOKEN="your_token_here"

# Or add to ~/.bashrc for persistence
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Regular Updates

```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📦 BACKUP & MAINTENANCE

### Backup Strategy

```bash
# Backup config and results
tar -czf trading_backup_$(date +%Y%m%d).tar.gz \
  ~/johntrading/config.py \
  ~/johntrading/phase3_backtest/results/ \
  ~/johntrading/phase6_paper_trade/

# Upload to S3
aws s3 cp trading_backup_*.tar.gz s3://your-bucket/backups/
```

### Clean Up Old Data

```bash
# Keep only last 90 days of cache
find ~/johntrading/phase1_data/cache -name "*.csv" -mtime +90 -delete
```

### Update Project Code

```bash
cd ~/johntrading
source .venv/bin/activate

# Pull latest updates from GitHub
git pull origin master

# Update dependencies if requirements.txt changed
pip install --upgrade -r requirements.txt
```

---

## 💾 DATA PERSISTENCE

### Local Storage (Default)

All data stored locally:
- `phase1_data/cache/*.csv` — Stock data
- `phase3_backtest/results/*.csv` — Backtest results
- `phase6_paper_trade/paper_portfolio.json` — Portfolio state

### Optional: S3 Backup

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Auto-backup results to S3
aws s3 sync ~/johntrading/phase3_backtest/results s3://your-bucket/results/
```

---

## 🎯 PRODUCTION CHECKLIST

Before running 24/7:

- [ ] ✅ EC2 instance sized appropriately (m7i-flex.large)
- [ ] ✅ ~20GB disk space available
- [ ] ✅ Python environment verified
- [ ] ✅ All dependencies installed
- [ ] ✅ First test run successful
- [ ] ✅ Cron job or service configured
- [ ] ✅ Monitoring/logging set up
- [ ] ✅ Backups configured
- [ ] ✅ Security groups configured
- [ ] ✅ SSH key secured

---

## 📞 COMMON COMMANDS REFERENCE

```bash
# Navigate to project
cd ~/johntrading

# Activate environment
source .venv/bin/activate

# Run all phases
python run_all.py

# Run specific phase
python run_phase1.py

# Run improvements analysis
python run_analysis_improvements.py

# View logs
tail -f logs/trading.log

# Check status (if running as service)
sudo systemctl status johntrading.service

# Restart service
sudo systemctl restart johntrading.service

# Update from GitHub
git pull origin master

# Check Python packages
pip list

# View current cron jobs
crontab -l

# Check disk usage
df -h

# Check memory
free -m

# See running processes
ps aux | grep python
```

---

## ✅ COMPLETION CHECKLIST

After following this guide:

- [ ] EC2 instance launched and accessible
- [ ] Deployment script executed successfully
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] Phase 1 data downloaded successfully
- [ ] All phases running without errors
- [ ] Scheduled execution configured (cron or service)
- [ ] Logging and monitoring working
- [ ] Results visible and tracked
- [ ] Ready for production

---

## 📚 MORE INFORMATION

For more details, see:
- `README.md` — Project overview
- `PROJECT_DOCUMENTATION.md` — Architecture details
- `IMPROVEMENTS.md` — Optimization parameters
- `config.py` — All tunable parameters

---

**Created:** March 26, 2026  
**Status:** Ready for Production  
**Instance:** AWS m7i-flex.large  
**Repository:** https://github.com/Manoj-1212/johnTrading.git  
