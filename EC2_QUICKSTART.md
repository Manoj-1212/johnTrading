# EC2 DEPLOYMENT — QUICK COMMANDS

## 🚀 FASTEST DEPLOYMENT (Copy & Paste)

### Step 1: SSH to Your EC2 Instance
```bash
ssh -i /path/to/key.pem ubuntu@YOUR_EC2_IP
```

### Step 2: Run Deployment (Single Command)
```bash
curl -O https://raw.githubusercontent.com/Manoj-1212/johnTrading/master/deploy_ec2.sh && chmod +x deploy_ec2.sh && ./deploy_ec2.sh
```

### Step 3: After Deployment Completes
```bash
cd ~/johntrading
source .venv/bin/activate
```

---

## ▶️ RUN THE SYSTEM

### Option 1: Run Everything Now (3-5 minutes)
```bash
cd ~/johntrading
source .venv/bin/activate
python run_all.py
```

**Output:**
- Phase 1: Downloaded 1,258 bars × 6 tickers
- Phase 2: Calculated 7 indicators
- Phase 3: Backtest results vs VOO
- Phase 4: Today's trading signals (BUY/SELL/HOLD)
- Phase 5: Analysis and recommendations
- Phase 6: Paper portfolio status

---

### Option 2: Run Only Signal Generation (1 minute)
```bash
cd ~/johntrading
source .venv/bin/activate
python run_phase4.py
```

**Output:**
```
🟢 BUY SIGNALS: 0
🟡 HOLD SIGNALS: 2 (AAPL, TSLA)
🔴 SELL SIGNALS: 3 (MSFT, NVDA, AMZN)
```

---

### Option 3: Run Only Individual Phases
```bash
python run_phase1.py    # Download stock data
python run_phase2.py    # Calculate indicators
python run_phase3.py    # Run 5-year backtest
python run_phase4.py    # Generate today's signals
python run_phase5.py    # Performance analysis
python run_phase6.py    # Portfolio status
```

---

## ⏱️ SCHEDULE TO RUN DAILY

### Set Up Daily Signal Generation at 4 PM UTC (After Market Close)

```bash
crontab -e
```

Add this line:
```
0 16 * * * cd /home/ubuntu/johntrading && source .venv/bin/activate && python run_all.py >> logs/trading.log 2>&1
```

Save and exit (Ctrl+X → Y → Enter)

Verify:
```bash
crontab -l
```

---

## 📊 VIEW RESULTS

### See Today's Signals
```bash
cd ~/johntrading
source .venv/bin/activate
python run_phase4.py
```

### Check Backtest Performance
```bash
python run_phase3.py
```

### View Paper Portfolio
```bash
python run_phase6.py
```

### View Logs
```bash
tail -f logs/trading.log
```

---

## 🔧 QUICK DIAGNOSTICS

### Check If Installation Works
```bash
python -c "from phase2_indicators.combiner import build_full_indicator_set; print('✓ Working')"
```

### Check Stock Data Downloaded
```bash
ls -lah phase1_data/cache/
# Should show 6 CSV files (AAPL, MSFT, NVDA, TSLA, AMZN, VOO)
```

### Check Disk Space
```bash
df -h
# Need ~20GB free
```

### Check Memory
```bash
free -h
# m7i-flex.large has 16GB plenty
```

### View Process
```bash
ps aux | grep python
```

---

## 🎯 COMMON ISSUES & FIXES

### "ImportError: No module named 'yfinance'"
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### "Connection refused" / "Cannot download data"
```bash
# Check internet
ping google.com

# Check Python can access internet
python -c "import urllib.request; urllib.request.urlopen('http://google.com'); print('✓ Internet OK')"
```

### "No space left on device"
```bash
# Check disk
df -h

# Clear cache (will re-download)
rm -rf phase1_data/cache/
```

### Data too old or missing
```bash
# Re-download all data
rm -rf phase1_data/cache/
python run_phase1.py
```

---

## 📈 OPTIMIZATION TESTING

### Run Full Analysis (Find Best Parameters)
Takes 20-30 minutes, finds optimal settings:

```bash
source .venv/bin/activate
python run_analysis_improvements.py
```

This will test:
- MIN_SIGNALS_TO_BUY: [3,4,5,6,7]
- STOP_LOSS_PCT: Best value
- TAKE_PROFIT_PCT: Best value
- All 20 tickers for generalization

Output: Best configuration to use

---

## 🔐 SECURITY BASICS

### Lock Down SSH
```bash
sudo nano /etc/ssh/sshd_config
# Change Port 22 to something else (optional)
# Set PermitRootLogin no
# Set PasswordAuthentication no

sudo systemctl restart sshd
```

### Enable Firewall
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw status
```

---

## 💾 BACKUP RESULTS

### Backup All Results
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz \
  ~/johntrading/phase3_backtest/results/ \
  ~/johntrading/phase6_paper_trade/

# Copy to your computer
scp -i /path/to/key.pem ubuntu@YOUR_IP:~/backup_*.tar.gz ~/downloads/
```

---

## 📁 FILE STRUCTURE

```
~/johntrading/
├── config.py                    ← All parameters
├── run_all.py                   ← Run everything
├── run_phase1-6.py              ← Individual phases
├── phase1_data/
│   └── cache/                   ← Stock data (CSVs)
├── phase2_indicators/           ← 7 indicator modules
├── phase3_backtest/
│   └── results/                 ← Trade logs & metrics
├── phase6_paper_trade/
│   └── paper_portfolio.json     ← Current positions
└── logs/
    ├── trading.log              ← Daily signals
    └── errors.log               ← Any errors
```

---

## ✅ SUMMARY

```
1. SSH to EC2
2. Run deployment script (1 command)
3. Wait ~5 minutes
4. Choose: Run now OR Schedule daily
5. Done!
```

Very simple. 

---

## 🆘 NEED HELP?

```bash
# Check README
cat ~/johntrading/README.md

# Check logs
tail -f ~/johntrading/logs/trading.log

# Check config
cat ~/johntrading/config.py

# Test individual phase
python ~/johntrading/run_phase1.py
```

---

**Ready to deploy?**

1. SSH to EC2
2. Run deployment script
3. Enjoy! 🚀
