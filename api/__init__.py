from api.delta_client import DeltaExchangeClient
from api.market_data import MarketData
from api.account_methods import AccountMethods
from api.order_management import OrderManagement
from api.position_management import PositionManagement


class DeltaAPI(MarketData, AccountMethods, OrderManagement, PositionManagement):
    """Complete Delta Exchange API client"""
    pass


__all__ = [
    'DeltaExchangeClient',
    'MarketData',
    'AccountMethods',
    'OrderManagement',
    'PositionManagement',
    'DeltaAPI'
]