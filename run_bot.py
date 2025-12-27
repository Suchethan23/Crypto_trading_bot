# trading/bot.py

# import time
# from datetime import datetime
# from api.delta_client import DeltaExchange
# from utils.data_fetcher import DataFetcher
# from indicators.supertrend import calculate_supertrend, get_supertrend_signal
# from trading.live_trading import LiveTrader
# from config import settings


# class TradingBot:
#     """Automated trading bot"""
    
#     def __init__(self):
#         self.client = DeltaExchange(
#             api_key=settings.API_KEY,
#             api_secret=settings.API_SECRET,
#             testnet=settings.TESTNET
#         )
#         self.data_fetcher = DataFetcher(self.client)
#         self.product_id = None
#         self.trader = None
#         self.prev_trend = None
        
#     def get_product_id(self, symbol):
#         """Get product ID for symbol"""
#         products = self.data_fetcher.get_products()
#         for product in products:
#             if product.get('symbol') == symbol:
#                 return product.get('id')
#         return None
    
#     def initialize(self, symbol):
#         """Initialize bot with symbol"""
#         print(f"\n🤖 Initializing Trading Bot for {symbol}...")
        
#         self.product_id = self.get_product_id(symbol)
#         if not self.product_id:
#             raise ValueError(f"Product ID not found for {symbol}")
        
#         print(f"✅ Product ID: {self.product_id}")
        
#         self.trader = LiveTrader(
#             client=self.client,
#             data_fetcher=self.data_fetcher,
#             product_id=self.product_id,
#             position_size=settings.POSITION_SIZE
#         )
        
#         # Sync current position
#         position, entry = self.trader.get_current_position()
#         self.trader.current_position = position
#         self.trader.entry_price = entry
        
#         print(f"✅ Current Position: {position or 'None'}")
#         if entry:
#             print(f"✅ Entry Price: ${entry:,.2f}")
    
#     def get_signal(self):
#         """Get trading signal from supertrend"""
#         # Fetch latest candles
#         candles = self.data_fetcher.get_candles(
#             symbol=settings.DEFAULT_SYMBOL,
#             resolution=settings.DEFAULT_RESOLUTION
#         )
        
#         # Calculate supertrend
#         supertrend_data = calculate_supertrend(
#             candles,
#             period=settings.SUPERTREND_PERIOD,
#             multiplier=settings.SUPERTREND_MULTIPLIER
#         )
        
#         # Get last two candles
#         if len(supertrend_data) < 2:
#             return 'hold', None
        
#         current = supertrend_data[-1]
#         prev = supertrend_data[-2]
        
#         # Detect trend change
#         if prev['trend'] == 'down' and current['trend'] == 'up':
#             return 'buy', current['close']
#         elif prev['trend'] == 'up' and current['trend'] == 'down':
#             return 'sell', current['close']
#         else:
#             return 'hold', current['close']
    
#     def run(self, interval=60):
#         """
#         Run trading bot
        
#         Args:
#             interval: Check interval in seconds (default: 60)
#         """
#         print("\n" + "="*80)
#         print("🚀 TRADING BOT STARTED")
#         print("="*80)
#         print(f"Symbol: {settings.DEFAULT_SYMBOL}")
#         print(f"Resolution: {settings.DEFAULT_RESOLUTION}")
#         print(f"Position Size: {settings.POSITION_SIZE}")
#         print(f"Check Interval: {interval}s")
#         print(f"Live Trading: {'ENABLED ⚠️' if settings.ENABLE_LIVE_TRADING else 'DISABLED (Dry Run)'}")
#         print("="*80)
#         print("\nPress Ctrl+C to stop...\n")
        
#         try:
#             while True:
#                 # Get signal
#                 signal, price,trend = self.get_signal()
                
#                 # Execute if live trading enabled
#                 if settings.ENABLE_LIVE_TRADING:
#                     self.trader.execute_signal(signal, price)
#                 else:
#                     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     print(f"[{timestamp}] 🔍 Signal: {signal.upper()} | Price: ${price:,.2f} |trend:{trend} "
#                           f"Position: {self.trader.current_position or 'None'} (DRY RUN)")
                
#                 # Wait for next check
#                 time.sleep(interval)
                
#         except KeyboardInterrupt:
#             print("\n\n⛔ Bot stopped by user")
#             print("="*80)

#     def get_signal(self):
#         """Get trading signal from supertrend"""
#         # Fetch latest candles
#         candles = self.data_fetcher.get_candles(
#             symbol=settings.DEFAULT_SYMBOL,
#             resolution=settings.DEFAULT_RESOLUTION
#         )
        
#         # Calculate supertrend
#         supertrend_data = calculate_supertrend(
#             candles,
#             period=settings.SUPERTREND_PERIOD,
#             multiplier=settings.SUPERTREND_MULTIPLIER
#         )
        
#         # Get signal using the helper function
#         signal, price, trend = get_supertrend_signal(supertrend_data)
        
#         return signal, price, trend
    
from Bot.trading_bot import TradingBot
from utils.data_fetcher import DataFetcher
from Indicators.SuperTrend.supertrend import calculate_supertrend, get_supertrend_signal
import json
import time

bot = TradingBot()
fetcher=DataFetcher()
# product_id = bot.get_product_id("BTCUSD")
# print("Product ID:", product_id)
symbol="XRPUSD"
size=1

data = fetcher.get_candles_in_batches(symbol, "5m")
supertrend= calculate_supertrend(data)

fetcher.export_to_json(supertrend,"supertrend.json")

# with open("supertrend.json", "r") as f:
#     data = json.load(f)

signal,price,trend,supertrend=get_supertrend_signal(supertrend)

print(signal,price,trend,supertrend)

positions=bot.monitor_positions(symbol)

print(positions)


sl_pct = 1 / 50  # 2%

if signal == "buy" and current_side != "long":
    order = bot.execute_simple_trade(symbol, "buy", size)

    if order:
        time.sleep(1)  # allow exchange to register position
        sl_price = round(price * (1 - sl_pct), 2)
        bot.set_stop_loss(symbol, "sell", size, sl_price)

elif signal == "sell" and current_side != "short":
    order = bot.execute_simple_trade(symbol, "sell", size)

    if order:
        time.sleep(1)
        sl_price = round(price * (1 + sl_pct), 2)
        bot.set_stop_loss(symbol, "buy", size, sl_price)

else:
    print("⏳ No trade taken (position exists or HOLD signal)")

# print(supertrend)