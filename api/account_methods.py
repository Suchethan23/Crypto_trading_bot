"""
Account management methods for Delta Exchange
"""
from typing import Dict,Optional, List
from api.delta_client import DeltaExchangeClient


class AccountMethods(DeltaExchangeClient):
    """Account and wallet operations"""
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        return self._request('GET', '/v2/wallet/balances')
    
    def get_wallet_transactions(self, asset_id: Optional[int] = None, 
                               transaction_type: Optional[str] = None,
                               after: Optional[str] = None, 
                               before: Optional[str] = None,
                               page_size: int = 100) -> Dict:
        """
        Get wallet transaction history
        
        Args:
            asset_id: Filter by asset ID
            transaction_type: Filter by type (deposit, withdrawal, etc.)
            after: Cursor for pagination
            before: Cursor for pagination
            page_size: Number of records per page
        """
        params = {'page_size': page_size}
        
        if asset_id:
            params['asset_id'] = asset_id
        if transaction_type:
            params['transaction_type'] = transaction_type
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        
        return self._request('GET', '/v2/wallet/transactions', params=params)
    
    def get_trading_fees(self) -> Dict:
        """Get current trading fee rates"""
        return self._request('GET', '/v2/profile')
    
    def get_user_info(self) -> Dict:
        """Get user account information"""
        return self._request('GET', '/v2/profile')

