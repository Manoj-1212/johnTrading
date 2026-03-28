"""
Phase 8: Alpaca Broker Integration
Real-time order execution via Alpaca API (paper or live trading)
"""

import os
from datetime import datetime
import json
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest,
        StopOrderRequest,
        LimitOrderRequest,
        TrailingStopOrderRequest,
    )
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, OrderStatus
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestBarRequest
except ImportError:
    print("WARNING: alpaca-py not installed. Install with: pip install alpaca-py")

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    TRAILING_STOP = "trailing_stop"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class AlpacaBrokerInterface:
    """
    Alpaca broker integration for real-time order execution.
    
    Features:
    - Market, limit, stop-loss order placement
    - Position tracking and management
    - Account info and cash balance monitoring
    - Paper trading (free) and live trading (USD required)
    
    Setup:
        1. Create free Alpaca account: https://alpaca.markets
        2. Generate API key at: https://app.alpaca.markets/brokerage/account/keys
        3. Set environment variables:
            export APCA_API_KEY_ID="your_key"
            export APCA_API_SECRET_KEY="your_secret"
            export APCA_API_BASE_URL="https://paper-api.alpaca.markets"  # Paper trading
    """
    
    def __init__(self, paper_trading=True, debug=False):
        """
        Initialize Alpaca broker connection.
        
        Args:
            paper_trading: Use paper trading (free) or live trading
            debug: Enable debug logging
        """
        self.debug = debug
        self.paper_trading = paper_trading
        
        # Get API credentials from environment
        api_key = os.getenv('APCA_API_KEY_ID')
        secret_key = os.getenv('APCA_API_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca API credentials not found. Set environment variables:\n"
                "  APCA_API_KEY_ID='your_key'\n"
                "  APCA_API_SECRET_KEY='your_secret'"
            )
        
        # Set API base URL via environment variable (alpaca-py will read it automatically)
        if paper_trading:
            api_base_url = "https://paper-api.alpaca.markets"
            mode = "PAPER TRADING"
        else:
            api_base_url = "https://api.alpaca.markets"
            mode = "LIVE TRADING"
        
        # Set environment variable if not already set
        if not os.getenv('APCA_API_BASE_URL'):
            os.environ['APCA_API_BASE_URL'] = api_base_url
        
        try:
            # Initialize Alpaca trading client
            # Note: TradingClient reads APCA_API_BASE_URL, APCA_API_KEY_ID, APCA_API_SECRET_KEY from environment
            self.client = TradingClient(api_key, secret_key)
            
            # Verify connection by getting account
            self.account = self.client.get_account()
            
            if self.debug:
                print(f"✓ Connected to Alpaca ({mode})")
                print(f"  Account: {self.account.account_number}")
                print(f"  Cash: ${self.account.cash:.2f}")
                print(f"  Portfolio Value: ${self.account.portfolio_value:.2f}")
            
            self.connected = True
            
        except Exception as e:
            print(f"Error connecting to Alpaca: {e}")
            self.connected = False
    
    def place_buy_order(self, ticker, quantity, order_type='market', limit_price=None, 
                       stop_price=None, trailing_stop=None):
        """
        Place a buy order.
        
        Args:
            ticker: Stock ticker
            quantity: Number of shares
            order_type: 'market', 'limit', 'stop', or 'trailing_stop'
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            trailing_stop: Percentage for trailing stop (e.g., 2 for 2%)
        
        Returns:
            Order object with order_id, status, etc.
        """
        
        if not self.connected:
            print("Not connected to Alpaca")
            return None
        
        try:
            if order_type == 'market':
                order_request = MarketOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'limit' and limit_price:
                order_request = LimitOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    limit_price=limit_price,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'stop' and stop_price:
                order_request = StopOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    stop_price=stop_price,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'trailing_stop' and trailing_stop:
                order_request = TrailingStopOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    trail_percent=trailing_stop,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
            
            else:
                print(f"Invalid order type: {order_type}")
                return None
            
            # Submit order
            order = self.client.submit_order(order_request)
            
            if self.debug:
                print(f"BUY ORDER: {ticker} x{quantity} @ {order_type}")
                print(f"  Order ID: {order.id}")
                print(f"  Status: {order.status}")
                print(f"  Filled: {order.filled_qty}/{order.qty}")
            
            return order
            
        except Exception as e:
            print(f"Error placing buy order for {ticker}: {e}")
            return None
    
    def place_sell_order(self, ticker, quantity, order_type='market', limit_price=None,
                        stop_price=None, trailing_stop=None):
        """
        Place a sell order.
        
        Args:
            ticker: Stock ticker
            quantity: Number of shares to sell
            order_type: 'market', 'limit', 'stop', or 'trailing_stop'
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            trailing_stop: Percentage for trailing stop
        
        Returns:
            Order object
        """
        
        if not self.connected:
            print("Not connected to Alpaca")
            return None
        
        try:
            if order_type == 'market':
                order_request = MarketOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'limit' and limit_price:
                order_request = LimitOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    limit_price=limit_price,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'stop' and stop_price:
                order_request = StopOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    stop_price=stop_price,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'trailing_stop' and trailing_stop:
                order_request = TrailingStopOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    trail_percent=trailing_stop,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            
            else:
                print(f"Invalid order type: {order_type}")
                return None
            
            # Submit order
            order = self.client.submit_order(order_request)
            
            if self.debug:
                print(f"SELL ORDER: {ticker} x{quantity} @ {order_type}")
                print(f"  Order ID: {order.id}")
                print(f"  Status: {order.status}")
                print(f"  Filled: {order.filled_qty}/{order.qty}")
            
            return order
            
        except Exception as e:
            print(f"Error placing sell order for {ticker}: {e}")
            return None
    
    def get_positions(self):
        """Get all current open positions"""
        
        if not self.connected:
            return []
        
        try:
            positions = self.client.get_all_positions()
            
            if self.debug and positions:
                print(f"Current Positions ({len(positions)}):")
                for pos in positions:
                    pnl_pct = (float(pos.unrealized_plpc) * 100) if pos.unrealized_plpc else 0
                    print(f"  {pos.symbol}: {pos.qty} @ ${pos.current_price} "
                          f"(P&L: ${pos.unrealized_pl:.2f}, {pnl_pct:.1f}%)")
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_position(self, ticker):
        """Get specific position"""
        
        if not self.connected:
            return None
        
        try:
            position = self.client.get_open_position(ticker)
            return position
        except:
            return None  # No position for this ticker
    
    def close_position(self, ticker, order_type='market', limit_price=None):
        """
        Close entire position for a ticker.
        
        Args:
            ticker: Stock ticker
            order_type: 'market' or 'limit'
            limit_price: Price for limit order
        
        Returns:
            Order object
        """
        
        if not self.connected:
            return None
        
        try:
            position = self.get_position(ticker)
            if not position:
                print(f"No position for {ticker}")
                return None
            
            qty = int(position.qty)
            
            if order_type == 'market':
                order_request = MarketOrderRequest(
                    symbol=ticker,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            elif order_type == 'limit' and limit_price:
                order_request = LimitOrderRequest(
                    symbol=ticker,
                    qty=qty,
                    limit_price=limit_price,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            else:
                print("Invalid order type")
                return None
            
            order = self.client.submit_order(order_request)
            
            if self.debug:
                print(f"CLOSE POSITION: {ticker} x{qty}")
                print(f"  Order ID: {order.id}")
                print(f"  Status: {order.status}")
            
            return order
            
        except Exception as e:
            print(f"Error closing position for {ticker}: {e}")
            return None
    
    def get_account_info(self):
        """Get account information"""
        
        if not self.connected:
            return None
        
        try:
            self.account = self.client.get_account()
            
            info = {
                'timestamp': datetime.now().isoformat(),
                'cash': float(self.account.cash),
                'portfolio_value': float(self.account.portfolio_value),
                'buying_power': float(self.account.buying_power),
                'multiplier': int(self.account.multiplier),
                'equity': float(self.account.equity),
                'daytrading_buying_power': float(self.account.daytrading_buying_power),
            }
            
            if self.debug:
                print("\nAccount Info:")
                print(f"  Cash: ${info['cash']:.2f}")
                print(f"  Portfolio Value: ${info['portfolio_value']:.2f}")
                print(f"  Buying Power: ${info['buying_power']:.2f}")
            
            return info
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None
    
    def get_orders(self, status='open', limit=10):
        """Get recent orders"""
        
        if not self.connected:
            return []
        
        try:
            orders = self.client.get_orders(status=status, limit=limit)
            return orders
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def cancel_order(self, order_id):
        """Cancel an open order"""
        
        if not self.connected:
            return False
        
        try:
            self.client.cancel_order(order_id)
            if self.debug:
                print(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False


if __name__ == "__main__":
    # Test connection
    print("Testing Alpaca connection...")
    print("Make sure to set environment variables:")
    print("  export APCA_API_KEY_ID='your_key'")
    print("  export APCA_API_SECRET_KEY='your_secret'")
    print()
    
    try:
        broker = AlpacaBrokerInterface(paper_trading=True, debug=True)
        
        if broker.connected:
            # Get account info
            print("\nGetting account info...")
            info = broker.get_account_info()
            
            # Get positions
            print("\nGetting positions...")
            positions = broker.get_positions()
            
            print("\n✓ Alpaca integration working!")
        
    except ValueError as e:
        print(f"Setup Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
