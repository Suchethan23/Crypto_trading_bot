"""
Order management methods for Delta Exchange
"""
from typing import Dict, Optional, List
from api.delta_client import DeltaExchangeClient


class OrderManagement(DeltaExchangeClient):
    """Order placement and management operations"""
    
    def place_market_order(self, product_id: int, size: float, side: str, 
                          reduce_only: bool = False) -> Dict:
        """
        Place a market order
        
        Args:
            product_id: Product ID to trade
            size: Order size in contracts
            side: 'buy' or 'sell'
            reduce_only: If True, order can only reduce position
        """
        data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'market_order',
            'reduce_only': reduce_only
        }
        return self._request('POST', '/v2/orders', data=data)
    
    def place_limit_order(self, product_id: int, size: float, side: str, 
                         limit_price: float, post_only: bool = False,
                         reduce_only: bool = False, time_in_force: str = 'gtc') -> Dict:
        """
        Place a limit order
        
        Args:
            product_id: Product ID to trade
            size: Order size in contracts
            side: 'buy' or 'sell'
            limit_price: Limit price for the order
            post_only: If True, order will only be maker
            reduce_only: If True, order can only reduce position
            time_in_force: 'gtc', 'fok', or 'ioc'
        """
        data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': 'limit_order',
            'limit_price': str(limit_price),
            'post_only': post_only,
            'reduce_only': reduce_only,
            'time_in_force': time_in_force
        }
        return self._request('POST', '/v2/orders', data=data)
    
    def place_stop_order(self, product_id: int, size: float, side: str,
                        stop_price: float, order_type: str = 'market_order',
                        limit_price: Optional[float] = None) -> Dict:
        """
        Place a stop order (stop loss or take profit)
        
        Args:
            product_id: Product ID to trade
            size: Order size in contracts
            side: 'buy' or 'sell'
            stop_price: Trigger price for the order
            order_type: 'market_order' or 'limit_order'
            limit_price: Required if order_type is 'limit_order'
        """
        data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': order_type,
            'stop_order_type': 'stop_loss_order',
            'stop_price': str(stop_price)
        }
        
        if order_type == 'limit_order' and limit_price:
            data['limit_price'] = str(limit_price)
        
        return self._request('POST', '/v2/orders', data=data)
    
    def cancel_order(self, order_id: int, product_id: int) -> Dict:
        """Cancel an open order"""
        data = {
            'id': order_id,
            'product_id': product_id
        }
        return self._request('DELETE', '/v2/orders', data=data)
    
    def cancel_all_orders(self, product_id: Optional[int] = None) -> Dict:
        """Cancel all open orders, optionally filtered by product"""
        data = {}
        if product_id:
            data['product_id'] = product_id
        return self._request('DELETE', '/v2/orders/all', data=data)
    
    def get_open_orders(self, product_id: Optional[int] = None) -> List[Dict]:
        """Get all open orders"""
        params = {'product_id': product_id} if product_id else {}
        return self._request('GET', '/v2/orders', params=params)
    
    def get_order_history(self, product_id: Optional[int] = None, 
                         limit: int = 100) -> List[Dict]:
        """Get order history"""
        params = {'limit': limit}
        if product_id:
            params['product_id'] = product_id
        return self._request('GET', '/v2/orders/history', params=params)
    
    def get_order_by_id(self, order_id: int) -> Dict:
        """Get specific order details by ID"""
        return self._request('GET', f'/v2/orders/{order_id}')
    
    def get_fills(self, product_id: Optional[int] = None, 
                 limit: int = 100) -> List[Dict]:
        """Get trade fills (executed trades)"""
        params = {'limit': limit}
        if product_id:
            params['product_id'] = product_id
        return self._request('GET', '/v2/fills', params=params)
