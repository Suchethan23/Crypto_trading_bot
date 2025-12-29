"""
Market data methods for Delta Exchange
"""
from typing import Dict, Optional, List
from api.delta_client import DeltaExchangeClient
import time

TIMEFRAME_SECONDS = {
    "1m": 600,
    "3m": 3 * 600,
    "5m": 5 * 600,
    "15m": 15 * 600,
    "30m": 30 * 600,
    "1h": 60 * 600*2,
    "2h": 2 * 60 * 600,
    "4h": 4 * 60 * 600,
    "6h": 6 * 60 * 600,
    "12h": 12 * 60 * 600,
    "1d": 24 * 60 * 600,
    "7d": 7 * 24 * 60 * 600,
    "30d": 30 * 24 * 60 * 600,
    "1w": 7 * 24 * 60 * 600,
    "2w": 14 * 24 * 60 * 600,
}

class MarketData(DeltaExchangeClient):
    """Market data operations"""
    
    def get_products(self) -> List[Dict]:
        """Get all available trading products"""
        return self._request('GET', '/v2/products', auth=False)
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data for a symbol"""
        return self._request('GET', f'/v2/tickers/{symbol}', auth=False)
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """Get orderbook for a symbol"""
        params = {'depth': depth}
        return self._request('GET', f'/v2/l2orderbook/{symbol}', params=params, auth=False)
    
    def get_trades(self, symbol: str) -> Dict:
        """Get recent trades for a symbol"""
        return self._request('GET', f'/v2/trades/{symbol}', auth=False)
    
    def get_candles(self, symbol: str, resolution: str = '5m', 
                   start: Optional[int] = None, end: Optional[int] = None) -> Dict:
        """
        Get historical OHLCV candlestick data
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSD', 'ETHUSD')
            resolution: Timeframe - '1m', '3m', '5m', '15m', '30m', '1h', '2h', 
                       '4h', '6h', '1d', '7d', '30d', '1w', '2w'
            start: Start timestamp (Unix epoch in seconds)
            end: End timestamp (Unix epoch in seconds)
        
        Returns:
            Dict with 'result' containing list of [timestamp, open, high, low, close, volume]
        """

        if not end:
            end = int(time.time())
        if not start:
           start = end - (24*60*60)


        print(resolution)
        params = {
            'symbol': symbol,
            'resolution': resolution
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        response= self._request('GET', '/v2/history/candles', params=params, auth=False)

        candles = []
        for c in response["result"]:
            candles.append([
                c["time"],
                float(c["open"]),
                float(c["high"]),
                float(c["low"]),
                float(c["close"]),
                float(c["volume"])
            ])

        
       
        candles.reverse()
        return candles
    
    def get_candles_dataframe(self, symbol: str, resolution: str = '1m',
                             start: Optional[int] = None, end: Optional[int] = None):
        """
        Get historical candles as a pandas DataFrame
        
        Returns DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        candles = self.get_candles(symbol, resolution, start, end)
        
        if not candles or 'result' not in candles:
            return pd.DataFrame()
        
        data = candles['result']
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df.set_index('timestamp', inplace=True)
        return df
    
    def get_mark_price_history(self, symbol: str, resolution: str = '1m',
                               start: Optional[int] = None, end: Optional[int] = None) -> Dict:
        """Get historical mark price data"""
        mark_symbol = f"MARK:{symbol}" if not symbol.startswith('MARK:') else symbol
        return self.get_candles(mark_symbol, resolution, start, end)
    
    def get_funding_rate_history(self, symbol: str, resolution: str = '1h',
                                 start: Optional[int] = None, end: Optional[int] = None) -> Dict:
        """Get historical funding rate data"""
        params = {
            'symbol': symbol,
            'resolution': resolution
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        return self._request('GET', '/v2/history/funding_rate', params=params, auth=False)
    
    def get_open_interest_history(self, symbol: str, resolution: str = '1h',
                                  start: Optional[int] = None, end: Optional[int] = None) -> Dict:
        """Get historical open interest data"""
        params = {
            'symbol': symbol,
            'resolution': resolution
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        return self._request('GET', '/v2/history/open_interest', params=params, auth=False)

    def get_candles_in_batches(self,symbol: str,resolution: str,start: int,
        end: int,
        max_candles_per_request: int = 500,
        sleep_sec: float = 0.3
    ) -> List[list]:
        """
        Fetch candles in batches without modifying get_candles()

        Args:
            symbol: Trading pair
            resolution: Timeframe (e.g. '5m', '1h')
            start: Start epoch (seconds)
            end: End epoch (seconds)
            max_candles_per_request: Safe Delta batch size
            sleep_sec: Delay between requests (rate-limit safe)

        Returns:
            List of [time, open, high, low, close, volume]
            Ordered oldest → newest
        """

        if not end:
            end = int(time.time())
            print(end)
        if not start:
           start = end - (2*24*60*60)

        if resolution not in TIMEFRAME_SECONDS:
            raise ValueError(f"Unsupported resolution: {resolution}")

        tf_sec = TIMEFRAME_SECONDS[resolution]
        all_candles: List[list] = []

        current_end = end

        while current_end > start:
            current_start = max(
                start,
                current_end - (max_candles_per_request * tf_sec)
            )

            candles = self.get_candles(
                symbol=symbol,
                resolution=resolution,
                start=current_start,
                end=current_end
            )

            if not candles:
                break

            all_candles.extend(candles)

            # Move backward safely
            oldest_time = candles[0][0]
            current_end = oldest_time - tf_sec

            time.sleep(sleep_sec)

        # Deduplicate by timestamp and sort
        unique = {c[0]: c for c in all_candles}
        candles = list(unique.values())
        candles.sort(key=lambda x: x[0])

        return candles
