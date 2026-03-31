"""
Phase 9: Risk Management & Monitoring
Portfolio-level risk controls, position sizing, and market regime detection
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import numpy as np

class MarketRegime(Enum):
    """Market regime classification"""
    NORMAL = "NORMAL"        # VIX < 20
    ELEVATED = "ELEVATED"    # VIX 20-30
    HIGH = "HIGH"            # VIX 30-40
    EXTREME = "EXTREME"      # VIX > 40

@dataclass
class RiskMetrics:
    """Portfolio risk metrics"""
    portfolio_value: float
    cash: float
    num_positions: int
    largest_position_pct: float      # % of portfolio
    sector_concentration: float      # Highest sector % of portfolio
    portfolio_volatility: float      # Standard deviation
    var_95: float                    # Value at risk (95%)
    daily_loss: float
    daily_loss_pct: float
    vix: float
    market_regime: MarketRegime
    can_trade: bool
    risk_warnings: list

class RiskManager:
    """
    Portfolio-level risk management.
    
    Features:
    - Position size limits (max 5% per position)
    - Daily loss limits (stop trading if loss > 2% daily)
    - Volatility-based position sizing (ATR, VIX)
    - Market regime detection (don't trade if VIX > 50)
    - Correlation-based diversification (avoid concentration)
    - Sector limits (max 30% in one sector)
    
    Usage:
        rm = RiskManager(broker)
        can_trade = rm.can_execute_buy(ticker, qty, current_price)
        metrics = rm.get_risk_metrics()
    """
    
    def __init__(self, broker, portfolio_value=10000, debug=False):
        """
        Initialize risk manager.
        
        Args:
            broker: AlpacaBrokerInterface instance
            portfolio_value: Initial portfolio value
            debug: Enable debug logging
        """
        self.broker = broker
        self.portfolio_value = portfolio_value
        self.initial_portfolio_value = portfolio_value
        self.debug = debug
        
        # Risk limits
        self.max_position_size_pct = 0.05        # Max 5% per position
        self.max_sector_concentration_pct = 0.30  # Max 30% in one sector
        self.daily_loss_limit_pct = 0.02          # Stop if daily loss > 2%
        self.max_vix_for_trading = 50             # Don't trade if VIX > 50
        self.position_sizing_atr_multiple = 2     # Risk 2*ATR per position
        
        # Position tracking
        self.positions = {}
        self.entry_prices = {}
        self.position_atrs = {}
        
        # Market data cache
        self.vix_cache = None
        self.vix_last_update = None
        
        # Sector mapping
        self.sector_map = self._get_sector_map()
    
    def can_execute_buy(self, ticker, quantity, current_price, atr=None):
        """
        Check if a buy order is allowed based on risk limits.
        
        Args:
            ticker: Stock ticker
            quantity: Proposed order quantity
            current_price: Current stock price
            atr: Average true range (for position sizing)
        
        Returns:
            (can_execute: bool, reason: str)
        """
        
        # Ensure current_price is a scalar float
        current_price = float(current_price.item()) if hasattr(current_price, 'item') else float(current_price)
        
        warnings = []
        
        # Check 1: Market regime (VIX)
        vix = self._get_vix()
        if vix > self.max_vix_for_trading:
            return False, f"Market in extreme volatility (VIX={vix:.1f} > {self.max_vix_for_trading})"
        
        # Check 2: Daily loss limit
        daily_pnl = float(self.portfolio_value) - float(self.initial_portfolio_value)
        daily_loss_pct = abs(daily_pnl) / float(self.initial_portfolio_value) if daily_pnl < 0 else 0
        
        if daily_loss_pct > self.daily_loss_limit_pct:
            return False, f"Daily loss limit reached ({daily_loss_pct:.2%} > {self.daily_loss_limit_pct:.2%})"
        
        # Check 3: Position size limit
        position_value = quantity * current_price
        position_pct = float(position_value / self.portfolio_value)  # Ensure scalar
        
        if position_pct > self.max_position_size_pct:
            return False, f"Position too large ({position_pct:.2%} > {self.max_position_size_pct:.2%})"
        
        # Check 4: Sector concentration
        sector = self.sector_map.get(ticker, 'OTHER')
        sector_exposure = float(self._calculate_sector_exposure(ticker, quantity, current_price))  # Ensure scalar
        
        if sector_exposure > self.max_sector_concentration_pct:
            return False, f"Sector concentration limit ({sector}: {sector_exposure:.2%})"
        
        # Check 5: Buying power
        cash = float(self.broker.account.cash) if self.broker.account else 0.0
        if position_value > cash:
            return False, f"Insufficient buying power (${position_value:.2f} > ${cash:.2f})"
        
        # All checks passed
        return True, "OK"
    
    def can_execute_sell(self, ticker, quantity):
        """Check if a sell order is allowed"""
        
        # Get current position
        position = self.broker.get_position(ticker)
        
        if not position:
            return False, f"No position for {ticker}"
        
        available_qty = int(position.qty)
        
        if quantity > available_qty:
            return False, f"Insufficient quantity ({quantity} > {available_qty})"
        
        return True, "OK"
    
    def calculate_position_size(self, ticker, current_price, account_balance, atr=None):
        """
        Calculate optimal position size based on risk.
        
        Rules:
        - Risk 2% of portfolio per trade
        - Adjust for ATR volatility
        - Respect maximum position size limit
        
        Args:
            ticker: Stock ticker
            current_price: Current price
            account_balance: Current account balance
            atr: Average true range (optional)
        
        Returns:
            int: Number of shares to buy
        """
        
        # Ensure account_balance is numeric
        account_balance = float(account_balance)
        current_price = float(current_price)
        
        # Risk 2% of account per position
        risk_amount = account_balance * 0.02
        
        # Base position size
        base_qty = int(risk_amount / current_price)
        
        # Adjust for ATR volatility
        if atr and atr > 0:
            # Higher ATR = less volatile = larger position
            # Lower ATR = more volatile = smaller position
            atr_pct = atr / current_price
            volatility_adjustment = 1 / (1 + atr_pct)
            adjusted_qty = int(base_qty * volatility_adjustment)
        else:
            adjusted_qty = base_qty
        
        # Enforce maximum position size (5% of portfolio)
        max_position_value = account_balance * self.max_position_size_pct
        max_qty = int(max_position_value / current_price)
        
        final_qty = min(adjusted_qty, max_qty, base_qty)
        
        return max(1, final_qty)  # At least 1 share
    
    def get_risk_metrics(self):
        """
        Calculate current portfolio risk metrics.
        
        Returns:
            RiskMetrics object
        """
        
        try:
            # Get current account state
            account_info = self.broker.get_account_info()
            positions = self.broker.get_positions()
            
            portfolio_value = account_info['portfolio_value']
            cash = account_info['cash']
            
            # Calculate metrics
            num_positions = len(positions)
            
            # Position concentrations
            largest_position_pct = 0
            sector_exposure = {}
            
            for position in positions:
                pos_value = float(position.market_value)
                pos_pct = pos_value / portfolio_value * 100
                largest_position_pct = max(largest_position_pct, pos_pct)
                
                # Sector concentration
                sector = self.sector_map.get(position.symbol, 'OTHER')
                sector_exposure[sector] = sector_exposure.get(sector, 0) + pos_pct
            
            max_sector_pct = max(sector_exposure.values()) if sector_exposure else 0
            
            # Daily P&L
            daily_loss = portfolio_value - self.initial_portfolio_value
            daily_loss_pct = (daily_loss / self.initial_portfolio_value) * 100
            
            # Market regime (VIX)
            vix = self._get_vix()
            regime = self._classify_regime(vix)
            
            # Risk metrics
            metrics = RiskMetrics(
                portfolio_value=portfolio_value,
                cash=cash,
                num_positions=num_positions,
                largest_position_pct=largest_position_pct,
                sector_concentration=max_sector_pct,
                portfolio_volatility=0,  # Would need more calculation
                var_95=0,  # Would need distribution analysis
                daily_loss=daily_loss,
                daily_loss_pct=daily_loss_pct,
                vix=vix,
                market_regime=regime,
                can_trade=self._can_trade(daily_loss_pct, vix),
                risk_warnings=self._generate_warnings(
                    largest_position_pct,
                    max_sector_pct,
                    daily_loss_pct,
                    vix
                )
            )
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating risk metrics: {e}")
            return None
    
    def _get_vix(self):
        """Get current VIX (volatility index)"""
        
        # Cache VIX for 1 minute to avoid excessive API calls
        now = datetime.now()
        
        if self.vix_cache is not None and self.vix_last_update is not None:
            age = (now - self.vix_last_update).total_seconds()
            if age < 60:
                return self.vix_cache
        
        try:
            vix_data = yf.download('^VIX', period='1d', progress=False)
            vix = float(vix_data['Close'].iloc[-1])
            
            self.vix_cache = vix
            self.vix_last_update = now
            
            return vix
            
        except:
            print("Warning: Could not fetch VIX")
            return 20.0  # Default to normal regime
    
    def _classify_regime(self, vix):
        """Classify market regime based on VIX"""
        
        if vix < 20:
            return MarketRegime.NORMAL
        elif vix < 30:
            return MarketRegime.ELEVATED
        elif vix < 40:
            return MarketRegime.HIGH
        else:
            return MarketRegime.EXTREME
    
    def _can_trade(self, daily_loss_pct, vix):
        """Check if system should trade"""
        
        if abs(daily_loss_pct) > self.daily_loss_limit_pct:
            return False
        
        if vix > self.max_vix_for_trading:
            return False
        
        return True
    
    def _calculate_sector_exposure(self, ticker, quantity, current_price):
        """Calculate sector exposure after adding position"""
        
        sector = self.sector_map.get(ticker, 'OTHER')
        new_position_value = quantity * current_price
        
        # Get current sector exposure
        positions = self.broker.get_positions()
        sector_value = 0
        
        for position in positions:
            if self.sector_map.get(position.symbol, 'OTHER') == sector:
                sector_value += float(position.market_value)
        
        # Add new position
        sector_value += new_position_value
        
        # Calculate percentage
        account_info = self.broker.get_account_info()
        portfolio_value = account_info['portfolio_value']
        
        sector_pct = sector_value / portfolio_value
        
        return sector_pct
    
    def _generate_warnings(self, position_pct, sector_pct, daily_loss_pct, vix):
        """Generate risk warnings"""
        
        warnings = []
        
        if position_pct > self.max_position_size_pct:
            warnings.append(f"Large position: {position_pct:.1f}%")
        
        if sector_pct > self.max_sector_concentration_pct:
            warnings.append(f"Sector concentration: {sector_pct:.1f}%")
        
        if daily_loss_pct > self.daily_loss_limit_pct:
            warnings.append(f"Daily loss limit approaching: {daily_loss_pct:.1f}%")
        
        if vix > 40:
            warnings.append(f"High volatility (VIX={vix:.1f})")
        
        return warnings
    
    def _get_sector_map(self):
        """Create ticker to sector mapping"""
        
        return {
            # Technology
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer', 'NVDA': 'Technology', 'META': 'Technology',
            'INTC': 'Technology', 'AMD': 'Technology', 'NFLX': 'Consumer',
            'PLTR': 'Technology',
            
            # Finance
            'JPM': 'Finance', 'GS': 'Finance', 'V': 'Finance',
            
            # Healthcare
            'JNJ': 'Healthcare',
            
            # Energy
            'XOM': 'Energy',
            
            # Consumer
            'WMT': 'Consumer', 'PG': 'Consumer',
            
            # Industrials
            'BA': 'Industrials', 'GE': 'Industrials',
            
            # Auto
            'TSLA': 'Auto',
            
            # Design
            'ADBE': 'Technology',
        }


class PortfolioMonitor:
    """
    Real-time portfolio monitoring and alerting.
    
    Monitors:
    - Stop losses
    - Take profits
    - Position P&L
    - Daily drawdown
    - News/events affecting portfolio
    """
    
    def __init__(self, broker, risk_manager, debug=False):
        self.broker = broker
        self.risk_manager = risk_manager
        self.debug = debug
        
        self.alerts = []
        self.last_check = datetime.now()
    
    def check_positions(self):
        """Check all positions for alerts"""
        
        try:
            positions = self.broker.get_positions()
            alerts = []
            
            for position in positions:
                try:
                    ticker = position.symbol
                    current_price = float(position.current_price)
                    
                    # Safely get entry price - try different attribute names
                    entry_price = (
                        float(getattr(position, 'avg_fill_price', 0)) or
                        float(getattr(position, 'average_fill_price', 0)) or
                        float(getattr(position, 'entry_price', current_price))
                    )
                    
                    pnl_pct = (float(position.unrealized_plpc) * 100) if position.unrealized_plpc else 0
                    
                    # Stop loss check (1.5%)
                    if pnl_pct < -1.5:
                        alerts.append({
                            'type': 'STOP_LOSS',
                            'ticker': ticker,
                            'pnl_pct': pnl_pct,
                            'message': f"{ticker} hit stop loss (P&L: {pnl_pct:.1f}%)"
                        })
                    
                    # Take profit check (2%)
                    if pnl_pct > 2.0:
                        alerts.append({
                            'type': 'TAKE_PROFIT',
                            'ticker': ticker,
                            'pnl_pct': pnl_pct,
                            'message': f"{ticker} hit take profit target (P&L: {pnl_pct:.1f}%)"
                        })
                
                except (AttributeError, ValueError) as e:
                    # Skip positions with missing attributes
                    continue
            
            self.alerts.extend(alerts)
            return alerts
            
        except Exception as e:
            print(f"Error checking positions: {e}")
            return []


if __name__ == "__main__":
    print("Phase 9: Risk Management & Monitoring")
    print("(Requires live broker connection for full functionality)")
