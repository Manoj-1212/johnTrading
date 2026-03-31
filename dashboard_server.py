"""
Real-Time Trading Dashboard
Displays trading execution, P&L, and risk metrics
"""

from flask import Flask, render_template, jsonify
from pathlib import Path
import json
import os
from datetime import datetime
import glob

app = Flask(__name__, template_folder='templates', static_folder='static')

LOGS_DIR = Path('phase9_production_trading/logs')

def get_latest_session():
    """Get the most recent session log"""
    session_files = sorted(glob.glob(str(LOGS_DIR / 'session_*.json')), reverse=True)
    if not session_files:
        return None
    
    with open(session_files[0], 'r') as f:
        return json.load(f)

def get_all_sessions():
    """Get all session logs"""
    session_files = sorted(glob.glob(str(LOGS_DIR / 'session_*.json')), reverse=True)
    sessions = []
    
    for session_file in session_files:
        with open(session_file, 'r') as f:
            session = json.load(f)
            sessions.append({
                'filename': Path(session_file).name,
                'data': session
            })
    
    return sessions

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/current-session')
def api_current_session():
    """Get current session data"""
    session = get_latest_session()
    if not session:
        return jsonify({'error': 'No session data available'}), 404
    
    return jsonify(session)

@app.route('/api/session-summary')
def api_session_summary():
    """Get session summary for all trades"""
    session = get_latest_session()
    if not session:
        return jsonify({'error': 'No session data available'}), 404
    
    trades = session.get('trading', {}).get('trades', [])
    account = session.get('account', {})
    
    # Calculate summary stats
    total_trades = len(trades)
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    
    return jsonify({
        'total_trades': total_trades,
        'buy_count': len(buy_trades),
        'sell_count': len(sell_trades),
        'account': account,
        'session_start': session.get('session_start'),
        'session_end': session.get('session_end'),
        'mode': session.get('mode')
    })

@app.route('/api/trades')
def api_trades():
    """Get all executed trades"""
    session = get_latest_session()
    if not session:
        return jsonify({'error': 'No session data available'}), 404
    
    trades = session.get('trading', {}).get('trades', [])
    return jsonify({'trades': trades})

@app.route('/api/blocked-trades')
def api_blocked_trades():
    """Get all blocked trades"""
    session = get_latest_session()
    if not session:
        return jsonify({'error': 'No session data available'}), 404
    
    blocked = session.get('trading', {}).get('blocked_trades', [])
    return jsonify({'blocked_trades': blocked})

@app.route('/api/account-history')
def api_account_history():
    """Get account history across sessions"""
    sessions = get_all_sessions()
    history = []
    
    for session_info in sessions:
        session = session_info['data']
        account = session.get('account', {})
        
        history.append({
            'session_start': session.get('session_start'),
            'initial_value': account.get('initial_value'),
            'final_value': account.get('final_value'),
            'pnl': account.get('final_value', 0) - account.get('initial_value', 0),
            'pnl_pct': ((account.get('final_value', 0) - account.get('initial_value', 0)) / account.get('initial_value', 1)) * 100 if account.get('initial_value') else 0,
        })
    
    return jsonify({'history': history})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    session = get_latest_session()
    
    return jsonify({
        'status': 'healthy' if session else 'no_data',
        'last_session': Path(sorted(glob.glob(str(LOGS_DIR / 'session_*.json')), reverse=True)[0]).name if glob.glob(str(LOGS_DIR / 'session_*.json')) else None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Starting Trading Dashboard...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
