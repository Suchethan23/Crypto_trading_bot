"""
Position management methods for Delta Exchange
"""
from typing import Dict, Optional, List
from api.delta_client import DeltaExchangeClient


class PositionManagement(DeltaExchangeClient):
    """Position monitoring and management operations"""
    
    def get_positions(self, product_id: Optional[int] = None, 
                     underlying_asset: Optional[str] = None) -> List[Dict]:
        """
        Get positions
        
        Args:
            product_id: Specific product ID (optional)
            underlying_asset: Underlying asset symbol like 'BTC', 'ETH' (optional)
        """
        params = {}
        if product_id:
            params['product_id'] = product_id
        elif underlying_asset:
            params['underlying_asset_symbol'] = underlying_asset
        
        return self._request('GET', '/v2/positions/margined', params=params)
    
    def get_position(self, product_id: int) -> Dict:
        """Get specific position by product ID"""
        params = {'product_id': product_id}
        return self._request('GET', '/v2/positions/margined', params=params)
    
    def change_leverage(self, product_id: int, leverage: int) -> Dict:
        """Change leverage for a product"""
        data = {
            'product_id': product_id,
            'leverage': str(leverage)
        }
        return self._request('POST', '/v2/positions/change_leverage', data=data)
    
    def add_margin(self, product_id: int, delta_margin: float) -> Dict:
        """Add margin to a position"""
        data = {
            'product_id': product_id,
            'delta_margin': str(delta_margin)
        }
        return self._request('POST', '/v2/positions/add_margin', data=data)
    
    def set_auto_topup(self, product_id: int, auto_topup: bool, 
                      top_up_value: Optional[float] = None) -> Dict:
        """Enable/disable auto top-up for a position"""
        data = {
            'product_id': product_id,
            'auto_topup': auto_topup
        }
        if top_up_value:
            data['top_up_value'] = str(top_up_value)
        
        return self._request('POST', '/v2/positions/auto_topup', data=data)
    
    def close_position(self, product_id: int) -> Dict:
        """Close entire position using market order"""
        position = self.get_position(product_id)
        
        if not position or 'result' not in position:
            return {'success': False, 'message': 'No position to close'}
        
        pos_data = position['result']
        size = abs(float(pos_data.get('size', 0)))
        
        if size == 0:
            return {'success': False, 'message': 'Position size is zero'}
        
        side = 'sell' if float(pos_data['size']) > 0 else 'buy'
        
        # Import OrderManagement to place order
        from api.order_management import OrderManagement
        order_client = OrderManagement(self.api_key, self.api_secret)
        
        return order_client.place_market_order(
            product_id=product_id,
            size=size,
            side=side,
            reduce_only=True
        )
