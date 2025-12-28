from Bot.trading_bot import TradingBot
from utils.data_fetcher import DataFetcher
from Indicators.SuperTrend.supertrend import calculate_supertrend, get_supertrend_signal
import json
import time
from datetime import datetime
from utils.telegramNotifier import TelegramNotifier
import os
from dotenv import load_dotenv

load_dotenv()



def main():
    # Initialize
    bot = TradingBot()
    fetcher = DataFetcher()
    symbol = "ETHUSD"
    size = 1
    check_interval = 300  # Check every 60 seconds
    sl_pct = 1 / 50  # 2% stop loss
    
    print("="*80)
    print("🚀 TRADING BOT STARTED")
    print("="*80)
    print(f"Symbol: {symbol}")
    print(f"Position Size: {size}")
    print(f"Stop Loss: {sl_pct*100:.1f}%")
    print(f"Check Interval: {check_interval}s")
    print("="*80)
    print("\nPress Ctrl+C to stop...\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{timestamp}] 🔍 Checking market...")
            
            try:
                # 1. Fetch fresh data
                data = fetcher.get_candles_in_batches(symbol, "15m")
                supertrend = calculate_supertrend(data)
                
                fetcher.export_to_json(supertrend,"supertrend_ETHUSD.json")
                # 2. Get signal
                signal, price, trend, supertrend_value = get_supertrend_signal(supertrend)
                
                # 3. Check current position
                positions = bot.monitor_positions(symbol)
                current_side = None
                
                if positions:
                    # Assuming monitor_positions returns a list with position info
                    for pos in positions:
                        if pos.get('size', 0) > 0:
                            current_side = 'long'
                        elif pos.get('size', 0) < 0:
                            current_side = 'short'
                
                print(f"📊 Signal: {signal.upper()} | Price: ${price:,.2f} | Trend: {trend} | Supertrend:{supertrend_value}")
                print(f"📍 Current Position: {current_side or 'None'}")
                
                # 4. Execute trades
                if signal == "buy" and current_side != "long":
                    print(f"🟢 BUY signal detected - Opening LONG position")
                    
                    # Close short if exists
                    if current_side == "short":
                        print("⚠️ Closing existing SHORT position first")
                        bot.execute_simple_trade(symbol, "buy", size)
                        time.sleep(2)
                    
                    # Open long
                    order = bot.execute_simple_trade(symbol, "buy", size)
                    
                    if order:
                        time.sleep(1)
                        sl_price = round(price * (1 - sl_pct), 2)
                        print(f"🛡️ Setting stop loss at ${sl_price:,.2f}")
                        bot.set_stop_loss(symbol, "sell", size, sl_price)
                        
                elif signal == "sell" and current_side != "short":
                    print(f"🔴 SELL signal detected - Opening SHORT position")
                    
                    # Close long if exists
                    if current_side == "long":
                        print("⚠️ Closing existing LONG position first")
                        bot.execute_simple_trade(symbol, "sell", size)
                        time.sleep(2)
                    
                    # Open short
                    order = bot.execute_simple_trade(symbol, "sell", size)
                    
                    if order:
                        time.sleep(1)
                        sl_price = round(price * (1 + sl_pct), 2)
                        print(f"🛡️ Setting stop loss at ${sl_price:,.2f}")
                        bot.set_stop_loss(symbol, "buy", size, sl_price)
                        
                else:
                    print("⏸️ No action - Position aligned with signal or HOLD")
                
            except Exception as e:
                print(f"❌ Error in trading cycle: {e}")
                # Continue running despite errors
            
            # 5. Wait before next check
            print(f"⏳ Waiting {check_interval}s until next check...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n⛔ Bot stopped by user")
        print("="*80)
        print("Final position check:")
        positions = bot.monitor_positions(symbol)
        print(positions)
        print("="*80)

if __name__ == "__main__":
    notifier = TelegramNotifier(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    chat_id=os.getenv("TELEGRAM_CHAT_ID"))
    
    notifier.info("🚀 Supertrend bot started")
    main()
   