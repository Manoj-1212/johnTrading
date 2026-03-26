# 🚀 EC2 DEPLOYMENT - COMPLETE GUIDE

Your John Trading System is ready to run on AWS EC2. Follow these steps to deploy.

---

## 📋 PREREQUISITES

- ✅ AWS Account
- ✅ EC2 instance: **m7i-flex.large** (or larger)
- ✅ OS: **Ubuntu 22.04 LTS** or **Amazon Linux 2**
- ✅ Instance must have **Internet access** (to download stock data)
- ✅ Security Group allows **SSH (port 22)**
- ✅ ~20GB free disk space
- ✅ SSH key pair downloaded

---

## ⚡ FASTEST DEPLOYMENT (5 minutes)

### Step 1: Connect to EC2
```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Run Auto-Deploy Script
```bash
curl -O https://raw.githubusercontent.com/Manoj-1212/johnTrading/master/deploy_ec2.sh && \
chmod +x deploy_ec2.sh && \
./deploy_ec2.sh
```

This automatically:
- Updates system packages
- Installs Python 3.11
- Clones repository from GitHub
- Creates virtual environment
- Installs all dependencies
- Downloads stock data

### Step 3: Activate Environment
```bash
cd ~/johntrading
source .venv/bin/activate
```

**Done! ✓ System is deployed.**

---

## ▶️ RUN THE SYSTEM

### Option 1: Run Everything Now
```bash
python run_all.py
```

This executes all 6 phases in sequence:
1. **Phase 1:** Download 5+ years of stock data
2. **Phase 2:** Calculate 7 technical indicators
3. **Phase 3:** Run 5-year backtest
4. **Phase 4:** Generate today's trading signals
5. **Phase 5:** Performance analysis vs VOO
6. **Phase 6:** Paper portfolio status

**Time:** ~5 minutes  
**Output:** Results logged to console + CSV files

---

### Option 2: Run Individual Phases
```bash
python run_phase1.py            # Download data only
python run_phase2.py            # Calculate indicators
python run_phase3.py            # Run backtest
python run_phase4.py            # Generate signals (outputs today's BUY/SELL/HOLD)
python run_phase5.py            # Analysis
python run_phase6.py            # Portfolio status
```

---

### Option 3: Schedule Daily Execution

#### Method A: Using Cron (Recommended for most users)

```bash
# Open cron editor
crontab -e

# Add this line (runs daily at 4 PM UTC / after market close):
0 16 * * * cd /home/ubuntu/johntrading && source .venv/bin/activate && python run_all.py >> logs/trading.log 2>&1

# Save (Ctrl+X → Y → Enter)

# Verify cron job
crontab -l
```

#### Method B: Using systemd Service (Recommended for always-on)

```bash
# Copy service file to systemd
sudo cp ~/johntrading/johntrading.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable johntrading.service

# Start service
sudo systemctl start johntrading.service

# Check status
sudo systemctl status johntrading.service

# View logs
sudo journalctl -u johntrading -f
```

---

## 📊 VIEW RESULTS

### See Today's Trading Signals
```bash
cd ~/johntrading
source .venv/bin/activate
python run_phase4.py
```

Output:
```
🟢 BUY SIGNALS: 0 (none - all conditions not met)
🟡 HOLD SIGNALS: 2
   AAPL @ $249.06 | Signals: 4/7 | Active: trend, rsi, volume, atr
   TSLA @ $403.84 | Signals: 4/7 | Active: trend, rsi, volume, atr
🔴 SELL SIGNALS: 3
   MSFT @ $417.46 | Signals: 1/7
   NVDA @ $134.25 | Signals: 2/7
   AMZN @ $219.39 | Signals: 2/7
```

### Check Backtest Performance
```bash
python run_phase3.py
```

Output shows alpha, win rate, Sharpe ratio vs VOO

### View Paper Portfolio
```bash
python run_phase6.py
```

Shows P&L, open positions, closed trades

### Monitor Logs
```bash
# If running as cron
tail -f logs/trading.log

# If running as systemd service
sudo journalctl -u johntrading -f
```

---

## 🎯 USING ENVIRONMENT VARIABLES

### Load Custom Configuration

```bash
# Copy example config
cp .env.example ~/.env

# Edit with your settings
nano ~/.env

# Source it
source ~/.env

# Verify
system_status  # This is a helper function (see .env.example)
```

### Create Custom Config

Edit `~/.env` to override defaults:

```bash
export MIN_SIGNALS=4              # Lower = more trades
export STOP_LOSS=0.05             # Tighter stops
export TAKE_PROFIT=0.20           # Larger targets
export PAPER_CAPITAL=20000        # Paper trading budget
export TICKERS="AAPL,MSFT,NVDA"  # Custom stock list
```

---

## 📈 OPTIMIZATION TESTING

### Run Full Analysis (Find Best Parameters)

```bash
source .venv/bin/activate
python run_analysis_improvements.py
```

This tests:
- ✅ MIN_SIGNALS_TO_BUY: [3, 4, 5, 6, 7]
- ✅ Indicator correlation (find redundancy)
- ✅ Elliott Wave/Fibonacci validation
- ✅ Realistic backtest impact
- ✅ All 20 tickers (generalization test)

**Time:** 15-30 minutes  
**Output:** Best configuration + recommendations

---

## 🔧 MAINTENANCE

### Update Code from GitHub

```bash
cd ~/johntrading
git pull origin master

# Reinstall dependencies if changed
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Backup Results

```bash
# Backup locally
tar -czf backup_$(date +%Y%m%d).tar.gz \
  phase3_backtest/results/ \
  phase6_paper_trade/

# Backup to S3 (requires AWS CLI)
aws s3 cp backup_*.tar.gz s3://your-bucket/backups/
```

### Clean Old Data (Keep Storage Efficient)

```bash
# Remove cache older than 90 days
find phase1_data/cache -name "*.csv" -mtime +90 -delete

# Rotate logs
find logs -name "*.log" -mtime +30 -delete
```

---

## 🐛 TROUBLESHOOTING

### Issue: "No module named 'yfinance'"

```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
python -c "import yfinance; print('✓ OK')"
```

### Issue: "Data download failed"

```bash
# Check internet
ping google.com

# Test data download
python run_phase1.py -v  # verbose mode
```

### Issue: "Disk full"

```bash
# Check usage
df -h

# Clear cache (will re-download)
rm -rf phase1_data/cache/*.csv
```

### Issue: "Out of memory"

```bash
# Check RAM
free -h

# Reduce dataset (edit config.py):
TICKERS = ["AAPL", "MSFT", "NVDA"]  # Use fewer stocks
```

### Issue: Service won't start

```bash
# Check logs
sudo journalctl -u johntrading -n 20

# Verify env
source .venv/bin/activate
python -c "print('✓ Python works')"

# Restart
sudo systemctl restart johntrading
```

---

## 🔐 SECURITY

### Restrict SSH Access

```bash
sudo nano /etc/ssh/sshd_config

# Add these lines:
PermitRootLogin no
PasswordAuthentication no
AllowUsers ubuntu@YOUR.IP.ADDRESS

sudo systemctl restart sshd
```

### Enable Firewall

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw status
```

### Regular Security Updates

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Or auto-updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📊 MONITORING COMMANDS

```bash
# View current processes
ps aux | grep python

# Monitor in real-time
htop

# Disk usage
df -h

# Memory usage
free -h

# Network
netstat -tuln

# Service status
sudo systemctl status johntrading.service

# Recent logs
sudo journalctl -u johntrading -n 50

# Search logs for errors
grep ERROR logs/trading.log

# Count signals generated
grep "SIGNAL" logs/trading.log | wc -l
```

---

## 📅 RECOMMENDED SCHEDULE

```
Daily 4 PM UTC  → Full pipeline (signals after market close)
Daily 3 PM UTC  → Health check (verify system working)
Monthly         → Run optimization analysis
Quarterly       → Review & update parameters
```

### Set Up Recommended Schedule

```bash
crontab -e
```

Add:
```bash
# Daily signals at 4 PM UTC
0 16 * * * cd ~/johntrading && source .venv/bin/activate && python run_all.py >> logs/trading.log 2>&1

# Weekly analysis on Sunday
0 18 * * 0 cd ~/johntrading && source .venv/bin/activate && python run_analysis_improvements.py >> logs/analysis.log 2>&1

# Daily backup
0 5 * * * cd ~/johntrading && tar -czf backup_$(date +\%Y\%m\%d).tar.gz phase3_backtest/results/
```

---

## 📁 IMPORTANT FILES

```
~/johntrading/
├── config.py                  ← All parameters
├── run_all.py                 ← Main runner
├── deploy_ec2.sh              ← Deployment script
├── johntrading.service        ← systemd service file
├── crontab.conf               ← Cron schedule templates
├── .env.example               ← Environment config template
├── phase1_data/cache/         ← Stock data cache
├── phase3_backtest/results/   ← Backtest trade logs
├── phase6_paper_trade/        ← Portfolio state
└── logs/
    ├── trading.log            ← Daily signals
    └── errors.log             ← Error log
```

---

## ✅ DEPLOYMENT CHECKLIST

Before considering deployment complete:

- [ ] SSH access working
- [ ] Deployment script ran successfully
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Phase 1 data downloaded
- [ ] All phases run without errors
- [ ] Signals generated correctly
- [ ] Cron job or service configured
- [ ] Logs being written to disk
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Security hardened

---

## 🎓 NEXT STEPS

1. **Run the system:** `python run_all.py`
2. **Review signals:** `python run_phase4.py`
3. **Analyze results:** Review logs and CSVs
4. **Optimize:** Run `python run_analysis_improvements.py`
5. **Schedule:** Set up cron or systemd service
6. **Monitor:** Check logs daily
7. **Backtest:** Review performance vs VOO
8. **Scale:** Increase capital if beating VOO by 5%+

---

## 📚 MORE INFORMATION

- `README.md` — Project overview
- `PROJECT_DOCUMENTATION.md` — Architecture
- `IMPROVEMENTS.md` — Optimization guide
- `EC2_QUICKSTART.md` — Quick reference
- `config.py` — All tunable parameters

---

## 💬 SUPPORT

If issues arise:

1. Check logs: `tail -f logs/trading.log`
2. Read error: `grep ERROR logs/errors.log`
3. Review config: `cat config.py`
4. Test phase: `python run_phase1.py`

---

**Deployment Status: ✅ READY**  
**Instance:** m7i-flex.large  
**Python:** 3.11+  
**Repository:** https://github.com/Manoj-1212/johnTrading.git  

---

*Happy trading! 🚀*
