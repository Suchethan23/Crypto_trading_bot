"""
Data fetching utilities for Delta Exchange
Pure data retrieval without indicator calculations
"""
import json
from pathlib import Path

import pandas as pd
from api import DeltaAPI
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class DataFetcher:
    """Helper class for fetching market data from Delta Exchange"""
    
    def __init__(self, client: Optional[DeltaAPI] = None):
        """
        Initialize DataFetcher
        
        Args:
            client: DeltaAPI client instance (optional)
        """
        self.client = client or DeltaAPI()
    
    # ==================== Candlestick Data Methods ====================
    
    def get_candles(self, symbol: str, resolution: str = '5m', 
                   start: Optional[int] = None, end: Optional[int] = None):
        """
        Get raw candlestick data
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSD', 'ETHUSD')
            resolution: Timeframe - '1m', '3m', '5m', '15m', '30m', '1h', '2h', 
                       '4h', '6h', '1d', '7d', '30d', '1w', '2w'
            start: Start timestamp (Unix epoch in seconds)
            end: End timestamp (Unix epoch in seconds)
        
        Returns:
            Raw API response with candle data
        """
        return self.client.get_candles(symbol, resolution, start, end)
    
    def get_candles_in_batches(self, symbol: str, resolution: str = '5m', 
                   start: Optional[int] = None, end: Optional[int] = None):
        """
        Get raw candlestick data
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSD', 'ETHUSD')
            resolution: Timeframe - '1m', '3m', '5m', '15m', '30m', '1h', '2h', 
                       '4h', '6h', '1d', '7d', '30d', '1w', '2w'
            start: Start timestamp (Unix epoch in seconds)
            end: End timestamp (Unix epoch in seconds)
        
        Returns:
            Raw API response with candle data
        """
        return self.client.get_candles_in_batches(symbol, resolution, start, end)
        
    
    def get_candles_dataframe(self, symbol: str, resolution: str = '5m',
                             start: Optional[int] = None, end: Optional[int] = None):
        """
        Get candlestick data as pandas DataFrame
        
        Args:
            symbol: Trading pair
            resolution: Timeframe
            start: Start timestamp
            end: End timestamp
        
        Returns:
            DataFrame with columns: timestamp(index), open, high, low, close, volume
        """
        return self.client.get_candles_dataframe(symbol, resolution, start, end)
    
    def get_recent_candles(self, symbol: str, resolution: str = '5m', 
                          hours_back: int = 24):
        """
        Get recent candles for the specified time period
        
        Args:
            symbol: Trading pair
            resolution: Timeframe
            hours_back: How many hours of historical data to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        end_time = int(time.time())
        start_time = end_time - (hours_back * 3600)
        
        return self.get_candles_dataframe(
            symbol=symbol,
            resolution=resolution,
            start=start_time,
            end=end_time
        )
    
    def get_candles_by_date_range(self, symbol: str, resolution: str,
                                   start_date: str, end_date: str):
        """
        Get candles between specific dates
        
        Args:
            symbol: Trading pair
            resolution: Timeframe
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
        
        Returns:
            DataFrame with OHLCV data
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        start_timestamp = int(start_dt.timestamp())
        end_timestamp = int(end_dt.timestamp())
        
        return self.get_candles_dataframe(
            symbol=symbol,
            resolution=resolution,
            start=start_timestamp,
            end=end_timestamp
        )
    
    def get_multiple_timeframes(self, symbol: str, 
                               timeframes: List[str] = ['5m', '15m', '1h'],
                               hours_back: int = 24) -> Dict:
        """
        Fetch data for multiple timeframes at once
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes to fetch
            hours_back: Hours of historical data for each timeframe
        
        Returns:
            Dict with timeframe as key and DataFrame as value
        """
        data = {}
        
        for tf in timeframes:
            print(f"Fetching {tf} data for {symbol}...")
            try:
                df = self.get_recent_candles(symbol, tf, hours_back)
                data[tf] = df
                time.sleep(0.2)  # Rate limiting to avoid API throttling
            except Exception as e:
                print(f"Error fetching {tf} data: {e}")
                data[tf] = None
        
        return data
    
    # ==================== Real-time Market Data Methods ====================
    
    def get_live_price(self, symbol: str) -> Dict:
        """
        Get current live price and market statistics
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dict with current price info: mark_price, last_price, bid, ask, 
            volume_24h, high_24h, low_24h, change_24h
        """
        ticker = self.client.get_ticker(symbol)
        
        if not ticker or 'result' not in ticker:
            return {}
        
        result = ticker['result']
        return {
            'symbol': result.get('symbol'),
            'mark_price': float(result.get('mark_price', 0)),
            'last_price': float(result.get('close', 0)),
            'bid': float(result.get('bid', 0)),
            'ask': float(result.get('ask', 0)),
            'spread': float(result.get('ask', 0)) - float(result.get('bid', 0)),
            'volume_24h': float(result.get('volume', 0)),
            'high_24h': float(result.get('high', 0)),
            'low_24h': float(result.get('low', 0)),
            'open_24h': float(result.get('open', 0)),
            'change_24h': float(result.get('price_change_24h', 0)),
            'change_24h_percent': float(result.get('price_change_24h_percent', 0)),
            'timestamp': result.get('timestamp')
        }
    
    def get_ticker_data(self, symbol: str) -> Dict:
        """
        Get complete ticker data (raw API response)
        
        Args:
            symbol: Trading pair
        
        Returns:
            Complete ticker data from API
        """
        return self.client.get_ticker(symbol)
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """
        Get current orderbook (bids and asks)
        
        Args:
            symbol: Trading pair
            depth: Number of levels to fetch (default 20)
        
        Returns:
            Orderbook with buy and sell orders
        """
        return self.client.get_orderbook(symbol, depth)
    
    def get_recent_trades(self, symbol: str) -> Dict:
        """
        Get recent executed trades
        
        Args:
            symbol: Trading pair
        
        Returns:
            List of recent trades
        """
        return self.client.get_trades(symbol)
    
    # ==================== Historical Market Data Methods ====================
    
    def get_mark_price_history(self, symbol: str, resolution: str = '1m',
                               start: Optional[int] = None, 
                               end: Optional[int] = None) -> Dict:
        """
        Get historical mark price data
        
        Args:
            symbol: Trading pair
            resolution: Timeframe
            start: Start timestamp
            end: End timestamp
        
        Returns:
            Historical mark price data
        """
        return self.client.get_mark_price_history(symbol, resolution, start, end)
    
    def get_funding_rate_history(self, symbol: str, resolution: str = '1h',
                                 start: Optional[int] = None, 
                                 end: Optional[int] = None) -> Dict:
        """
        Get historical funding rate data
        
        Args:
            symbol: Trading pair
            resolution: Timeframe (usually '1h' or '8h')
            start: Start timestamp
            end: End timestamp
        
        Returns:
            Historical funding rate data
        """
        return self.client.get_funding_rate_history(symbol, resolution, start, end)
    
    def get_open_interest_history(self, symbol: str, resolution: str = '1h',
                                  start: Optional[int] = None, 
                                  end: Optional[int] = None) -> Dict:
        """
        Get historical open interest data
        
        Args:
            symbol: Trading pair
            resolution: Timeframe
            start: Start timestamp
            end: End timestamp
        
        Returns:
            Historical open interest data
        """
        return self.client.get_open_interest_history(symbol, resolution, start, end)
    
    # ==================== Product & Symbol Information ====================
    
    def get_all_products(self) -> List[Dict]:
        """
        Get all available trading products
        
        Returns:
            List of all trading products with details
        """
        response = self.client.get_products()
        return response.get('result', [])
    
    def get_product_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Get specific product details by symbol
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Product details or None if not found
        """
        products = self.get_all_products()
        
        for product in products:
            if product.get('symbol') == symbol:
                return product
        
        return None
    
    def get_available_symbols(self, asset_type: Optional[str] = None) -> List[str]:
        """
        Get list of all available trading symbols
        
        Args:
            asset_type: Filter by type ('futures', 'perpetual_futures', etc.)
        
        Returns:
            List of symbol names
        """
        products = self.get_all_products()
        
        if asset_type:
            products = [p for p in products if p.get('contract_type') == asset_type]
        
        return [p.get('symbol') for p in products if p.get('symbol')]
    
    # ==================== Batch Data Fetching ====================
    
    def get_multiple_symbols_data(self, symbols: List[str], 
                                  resolution: str = '5m',
                                  hours_back: int = 24) -> Dict:
        """
        Fetch data for multiple symbols
        
        Args:
            symbols: List of trading pairs
            resolution: Timeframe
            hours_back: Hours of historical data
        
        Returns:
            Dict with symbol as key and DataFrame as value
        """
        data = {}
        
        for symbol in symbols:
            print(f"Fetching data for {symbol}...")
            try:
                df = self.get_recent_candles(symbol, resolution, hours_back)
                data[symbol] = df
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {symbol} data: {e}")
                data[symbol] = None
        
        return data
    
    def get_live_prices_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get live prices for multiple symbols
        
        Args:
            symbols: List of trading pairs
        
        Returns:
            Dict with symbol as key and price data as value
        """
        prices = {}
        
        for symbol in symbols:
            try:
                prices[symbol] = self.get_live_price(symbol)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching price for {symbol}: {e}")
                prices[symbol] = None
        
        return prices
    
    # ==================== Data Export Methods ====================
    
    def export_to_csv(self, df, filename: str):
        """
        Export DataFrame to CSV file
        
        Args:
            df: pandas DataFrame
            filename: Output filename (e.g., 'btc_data.csv')
        """
        try:
            df.to_csv(filename)
            print(f"✓ Data exported to {filename}")
        except Exception as e:
            print(f"✗ Error exporting data: {e}")
    
    def export_to_json(self, data: Dict, filename: str):
        """
        Export data to JSON file
        
        Args:
            data: Dictionary or data structure
            filename: Output filename (e.g., 'market_data.json')
        """
        import json
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✓ Data exported to {filename}")
        except Exception as e:
            print(f"✗ Error exporting data: {e}")
    
    
    # def export_to_json(
    #     data: Dict,
    #     filename: str,
    #     epoch_key: str = "time",
    #     timezone: str = "Asia/Kolkata"
    # ):
    #     """
    #     Export data to JSON with epoch → datetime conversion

    #     Args:
    #         data: Dictionary (Delta API response)
    #         filename: Output JSON file
    #         epoch_key: Key containing epoch seconds
    #         timezone: Target timezone for human-readable time
    #     """
    #     try:
    #         if not isinstance(data, dict):
    #             raise TypeError("export_to_json expects a dictionary")

    #         data = data.copy()

    #         # Handle Delta-style candle response
    #         if "result" in data and isinstance(data["result"], list):
    #             for candle in data["result"]:
    #                 if epoch_key in candle:
    #                     ts = pd.to_datetime(
    #                         candle[epoch_key], unit="s", utc=True
    #                     )
    #                     candle["datetime_utc"] = ts.isoformat()
    #                     candle["datetime"] = ts.tz_convert(timezone).isoformat()

    #         Path(filename).parent.mkdir(parents=True, exist_ok=True)

    #         with open(filename, "w") as f:
    #             json.dump(data, f, indent=2)

    #         print(f"✓ JSON exported with timestamps: {filename}")

    #     except Exception as e:
    #         print(f"✗ Error exporting JSON: {e}")


    # ==================== Utility Methods ====================
    
    def get_timestamp_range(self, hours_back: int) -> tuple:
        """
        Get start and end timestamps for a time range
        
        Args:
            hours_back: Hours to go back from now
        
        Returns:
            Tuple of (start_timestamp, end_timestamp)
        """
        end_time = int(time.time())
        start_time = end_time - (hours_back * 3600)
        return start_time, end_time
    
    def format_timestamp(self, timestamp: int) -> str:
        """
        Convert Unix timestamp to readable datetime string
        
        Args:
            timestamp: Unix timestamp in seconds
        
        Returns:
            Formatted datetime string
        """
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def print_data_summary(self, df):
        """
        Print summary statistics of DataFrame
        
        Args:
            df: pandas DataFrame with OHLCV data
        """
        if df.empty:
            print("No data available")
            return
        
        print("\n=== Data Summary ===")
        print(f"Period: {df.index[0]} to {df.index[-1]}")
        print(f"Total Candles: {len(df)}")
        print(f"\nPrice Statistics:")
        print(f"  High: ${df['high'].max():.4f}")
        print(f"  Low: ${df['low'].min():.4f}")
        print(f"  Average Close: ${df['close'].mean():.4f}")
        print(f"  Latest Close: ${df['close'].iloc[-1]:.4f}")
        print(f"\nVolume Statistics:")
        print(f"  Total Volume: {df['volume'].sum():.2f}")
        print(f"  Average Volume: {df['volume'].mean():.2f}")


# # ==================== Usage Example ====================
# if __name__ == "__main__":
#     """Example usage of DataFetcher"""
    
#     fetcher = DataFetcher()
    
#     # Example 1: Get recent candles
#     print("=== Example 1: Fetching Recent Candles ===")
#     df = fetcher.get_recent_candles('BTCUSD', resolution='5m', hours_back=6)
#     print(df.tail())
    
#     # Example 2: Get live price
#     print("\n=== Example 2: Live Price Data ===")
#     price_data = fetcher.get_live_price('BTCUSD')
#     print(f"Mark Price: ${price_data['mark_price']}")
#     print(f"24h Change: {price_data['change_24h_percent']}%")
    
#     # Example 3: Multiple timeframes
#     print("\n=== Example 3: Multiple Timeframes ===")
#     data = fetcher.get_multiple_timeframes('BTCUSD', ['5m', '15m', '1h'], hours_back=24)
#     for tf, df in data.items():
#         if df is not None:
#             print(f"{tf}: {len(df)} candles")
    
#     # Example 4: Export data
#     print("\n=== Example 4: Export Data ===")
#     fetcher.export_to_csv(df, 'btc_5m_data.csv')
    
#     # Example 5: Available symbols
#     print("\n=== Example 5: Available Symbols ===")
#     symbols = fetcher.get_available_symbols()
#     print(f"Total symbols available: {len(symbols)}")
#     print(f"First 10 symbols: {symbols[:10]}")