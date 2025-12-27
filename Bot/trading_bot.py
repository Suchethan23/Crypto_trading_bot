"""
High-level trading bot with automated operations
"""
from api import DeltaAPI
from typing import Optional


class TradingBot:
    """Automated trading bot for Delta Exchange"""
    
    def __init__(self, client: Optional[DeltaAPI] = None):
        self.client = client or DeltaAPI()
        self.running = False
    
    def get_product_id(self, symbol: str) -> Optional[int]:
        """Get product ID from symbol"""
        products = self.client.get_products()
        for product in products.get('result', []):
            if product['symbol'] == symbol:
                return product['id']
        return None
    
    def execute_simple_trade(self, symbol: str, side: str, size: float):
        """Execute a simple market order trade"""
        print(f"\n=== Executing {side.upper()} order for {symbol} ===")
        
        product_id = self.get_product_id(symbol)
        if not product_id:
            print(f"Error: Product {symbol} not found")
            return None
        
        try:
            order = self.client.place_market_order(
                product_id=product_id,
                size=size,
                side=side
            )
            print(f"Order placed successfully: {order}")
            return order
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
    
    def execute_limit_trade(self, symbol: str, side: str, size: float, 
                           limit_price: float):
        """Execute a limit order trade"""
        print(f"\n=== Executing {side.upper()} limit order for {symbol} ===")
        
        product_id = self.get_product_id(symbol)
        if not product_id:
            print(f"Error: Product {symbol} not found")
            return None
        
        try:
            order = self.client.place_limit_order(
                product_id=product_id,
                size=size,
                side=side,
                limit_price=limit_price
            )
            print(f"Limit order placed: {order}")
            return order
        except Exception as e:
            print(f"Error placing limit order: {e}")
            return None
    
    def set_stop_loss(self, symbol: str, side: str, size: float, stop_price: float):
        """Set a stop loss order"""
        print(f"\n=== Setting stop loss for {symbol} ===")
        
        product_id = self.get_product_id(symbol)
        if not product_id:
            print(f"Error: Product {symbol} not found")
            return None
        
        try:
            order = self.client.place_stop_order(
                product_id=product_id,
                size=size,
                side=side,
                stop_price=stop_price
            )
            print(f"Stop loss set: {order}")
            return order
        except Exception as e:
            print(f"Error setting stop loss: {e}")
            return None
    
    def exit_position(self, symbol: str, percentage: float = 100.0):
        """Exit a position (partial or full)"""
        print(f"\n=== Exiting {percentage}% of {symbol} position ===")
        
        product_id = self.get_product_id(symbol)
        if not product_id:
            print(f"Error: Product {symbol} not found")
            return None
        
        try:
            position_data = self.client.get_position(product_id)
            
            if not position_data or 'result' not in position_data:
                print("No position found to exit")
                return None
            
            position = position_data['result']
            current_size = float(position.get('size', 0))
            
            if current_size == 0:
                print("No open position to close")
                return None
            
            close_size = abs(current_size * (percentage / 100.0))
            close_side = 'sell' if current_size > 0 else 'buy'
            
            print(f"Current position size: {current_size}")
            print(f"Closing {close_size} contracts ({percentage}%)")
            
            order = self.client.place_market_order(
                product_id=product_id,
                size=close_size,
                side=close_side,
                reduce_only=True
            )
            
            print(f"Exit order placed successfully: {order}")
            return order
            
        except Exception as e:
            print(f"Error exiting position: {e}")
            return None
    
    def exit_all_positions(self):
        """Exit all open positions"""
        print("\n=== Exiting ALL positions ===")
        
        try:
            positions = self.client.get_positions()
            
            if not positions or 'result' not in positions:
                print("No positions to exit")
                return []
            
            result = positions.get('result', [])
            if isinstance(result, dict):
                result = [result]
            
            closed_positions = []
            
            for position in result:
                size = float(position.get('size', 0))
                if size != 0:
                    symbol = position.get('product_symbol')
                    product_id = position.get('product_id')
                    
                    print(f"\nClosing position: {symbol}")
                    
                    close_side = 'sell' if size > 0 else 'buy'
                    close_size = abs(size)
                    
                    try:
                        order = self.client.place_market_order(
                            product_id=product_id,
                            size=close_size,
                            side=close_side,
                            reduce_only=True
                        )
                        print(f"✓ Closed {symbol}: {order}")
                        closed_positions.append(order)
                    except Exception as e:
                        print(f"✗ Failed to close {symbol}: {e}")
            
            if closed_positions:
                print(f"\n✓ Successfully closed {len(closed_positions)} position(s)")
            else:
                print("\nNo positions were closed")
            
            return closed_positions
            
        except Exception as e:
            print(f"Error exiting all positions: {e}")
            return []
    
    def monitor_positions(self, underlying_asset: Optional[str] = None):
        """Monitor all open positions"""
        try:
            positions = self.client.get_positions(underlying_asset=underlying_asset)
            
            print("\n=== Current Positions ===")
            
            if not positions or 'result' not in positions:
                print("No positions found or error retrieving positions")
                return
            
            result = positions.get('result', [])
            
            if isinstance(result, dict):
                result = [result]
            
            if not result or len(result) == 0:
                print("No open positions")
                return
            
            for position in result:
                size = float(position.get('size', 0))
                if size != 0:
                    print(f"Symbol: {position.get('product_symbol', 'N/A')}")
                    print(f"  Size: {position.get('size', 0)}")
                    print(f"  Entry Price: {position.get('entry_price', 'N/A')}")
                    print(f"  Mark Price: {position.get('mark_price', 'N/A')}")
                    print(f"  Unrealized PnL: {position.get('unrealized_pnl', 'N/A')}")
                    print(f"  Realized PnL: {position.get('realized_pnl', 'N/A')}")
                    print(f"  Leverage: {position.get('leverage', 'N/A')}")
                    print("---")
            
            if all(float(p.get('size', 0)) == 0 for p in result):
                print("No open positions")
                
        except Exception as e:
            print(f"Error monitoring positions: {e}")
    
    def display_balance(self):
        """Display account balance"""
        balance = self.client.get_balance()
        
        print("\n=== Account Balance ===")
        for wallet in balance.get('result', []):
            print(f"Asset: {wallet['asset_symbol']}")
            print(f"  Balance: {wallet['balance']}")
            print(f"  Available: {wallet['available_balance']}")
            print("---")