# from Bot.trading_bot import TradingBot
# from utils.data_fetcher import DataFetcher
# from Indicators.SuperTrend.supertrend import calculate_supertrend, get_supertrend_signal
# import json
# import time
# from datetime import datetime
# from utils.telegramNotifier import TelegramNotifier
# import os
# from dotenv import load_dotenv

# load_dotenv()


# def wait_until_next_15m():
#     """
#     Block execution until the next 15-minute candle close
#     Ensures fresh candle data (no partial candles)
#     """
#     while True:
#         now = datetime.now()
#         if now.minute % 15 == 0 and now.second < 2:
#             return
#         time.sleep(1)


# def main():
#     # Initialize
#     bot = TradingBot()
#     fetcher = DataFetcher()
#     symbol = "ETHUSD"
#     size = 1
#     check_interval = 300  # kept for logging/reference only
#     sl_pct = 1 / 50  # 2% stop loss

#     print("=" * 80)
#     print("🚀 TRADING BOT STARTED")
#     print("=" * 80)
#     print(f"Symbol: {symbol}")
#     print(f"Position Size: {size}")
#     print(f"Stop Loss: {sl_pct * 100:.1f}%")
#     print("Execution: Every 15m candle close")
#     print("=" * 80)
#     print("\nPress Ctrl+C to stop...\n")

#     try:
#         while True:
#             print("⏳ Waiting for next 15m candle close...")
#             wait_until_next_15m()



#             timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             print(f"\n[{timestamp}] 🔍 Checking market...")

#             try:
#                 # 1. Fetch fresh data
#                 data = fetcher.get_candles_in_batches(symbol, "1m")
#                 supertrend = calculate_supertrend(data)

#                 # with open("supertrend_ETHUSD.json", "r") as f:
#                 #     data = json.load(f)


#                 fetcher.export_to_json(supertrend, "supertrend_ETHUSD.json")

#                 # 2. Get signal
#                 signal, price, trend, supertrend_value = get_supertrend_signal(supertrend)
#                 print(signal," fgg ", price,"sdgdg", trend,"fsgsd", supertrend_value)

#                 if signal == "buy":
#                     notifier.trade_entry(
#                         symbol="ETHUSD",
#                         side="long",
#                         entry=price,
#                         stoploss=supertrend_value,
#                         timeframe="15m"
#                     )

#                     print("📩 Telegram signal sent → LONG")

#                 elif signal == "sell":
#                     notifier.trade_entry(
#                         symbol="ETHUSD",
#                         side="short",
#                         entry=price,
#                         stoploss=supertrend_value,
#                         timeframe="15m"
#                     )
#                     print("📩 Telegram signal sent → SHORT")
#                     # notifier.info("⏸️ ")

#                 else:
#                     notifier.info("⏸️ No signal yet. Waiting...")
                
#                 # 3. Check current position
#                 positions = bot.monitor_positions(symbol)
#                 current_side = None

#                 if positions:
#                     for pos in positions:
#                         if pos.get('size', 0) > 0:
#                             current_side = 'long'
#                         elif pos.get('size', 0) < 0:
#                             current_side = 'short'

#                 print(
#                     f"📊 Signal: {signal.upper()} | "
#                     f"Price: ${price:,.2f} | "
#                     f"Trend: {trend} | "
#                     f"Supertrend: {supertrend_value}"
#                 )
#                 print(f"📍 Current Position: {current_side or 'None'}")

#                 # 4. Execute trades
#                 if signal == "buy" and current_side != "long":
#                     print("🟢 BUY signal detected - Opening LONG position")

#                     if current_side == "short":
#                         print("⚠️ Closing existing SHORT position")
#                         bot.execute_simple_trade(symbol, "buy", size)
#                         time.sleep(2)

#                     order = bot.execute_simple_trade(symbol, "buy", size)

#                     if order:
#                         time.sleep(1)
#                         sl_price = round(price * (1 - sl_pct), 2)
#                         print(f"🛡️ Setting stop loss at ${sl_price:,.2f}")
#                         bot.set_stop_loss(symbol, "sell", size, sl_price)

#                 elif signal == "sell" and current_side != "short":
#                     print("🔴 SELL signal detected - Opening SHORT position")

#                     if current_side == "long":
#                         print("⚠️ Closing existing LONG position")
#                         bot.execute_simple_trade(symbol, "sell", size)
#                         time.sleep(2)

#                     order = bot.execute_simple_trade(symbol, "sell", size)

#                     if order:
#                         time.sleep(1)
#                         sl_price = round(price * (1 + sl_pct), 2)
#                         print(f"🛡️ Setting stop loss at ${sl_price:,.2f}")
#                         bot.set_stop_loss(symbol, "buy", size, sl_price)

#                 else:
#                     print("⏸️ No action - Position aligned or HOLD")

#             except Exception as e:
#                 print(f"❌ Error in trading cycle: {e}")

#     except KeyboardInterrupt:
#         print("\n⛔ Bot stopped by user")
#         print("=" * 80)
#         print("Final position check:")
#         positions = bot.monitor_positions(symbol)
#         print(positions)
#         print("=" * 80)


# if __name__ == "__main__":
#     notifier = TelegramNotifier(
#         bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
#         chat_id=os.getenv("TELEGRAM_CHAT_ID")
#     )

#     notifier.info("🚀 Supertrend bot started")
#     main()


from Bot.trading_bot import TradingBot
from utils.data_fetcher import DataFetcher
from Indicators.SuperTrend.supertrend import calculate_supertrend, get_supertrend_signal
from utils.telegramNotifier import TelegramNotifier

import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def wait_until_next_15m():
    """
    Block execution until the next 15-minute candle close
    Ensures fresh candle data (no partial candles)
    """
    while True:
        now = datetime.now()
        if now.minute % 15 == 0 and now.second < 2:
            return
        time.sleep(1)


def main():
    # ---------------- INITIALIZATION ---------------- #
    bot = TradingBot()
    fetcher = DataFetcher()

    symbol = "ETHUSD"
    size = 1
    sl_pct = 1 / 50  # 2% fallback SL (only if supertrend SL not used)

    print("=" * 80)
    print("🚀 SUPERTRAND BOT STARTED")
    print("=" * 80)
    print(f"Symbol        : {symbol}")
    print(f"Position Size : {size}")
    print("Execution     : Every 15m candle close")
    print("=" * 80)
    print("\nPress Ctrl+C to stop...\n")

    try:
        while True:
            print("⏳ Waiting for next 15m candle close...")
            wait_until_next_15m()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] 🔍 Checking market...")

            try:
                # ---------------- FETCH DATA ---------------- #
                candles = fetcher.get_candles_in_batches(symbol, "1m")
                supertrend_data = calculate_supertrend(candles)

                fetcher.export_to_json(supertrend_data, "supertrend_ETHUSD.json")

                # ---------------- SIGNAL ---------------- #
                signal, price, trend, supertrend_value = get_supertrend_signal(supertrend_data)

                print(
                    f"📊 Signal: {signal.upper()} | "
                    f"Price: {price} | "
                    f"Trend: {trend} | "
                    f"Supertrend: {supertrend_value}"
                )

                # ---------------- POSITION CHECK ---------------- #
                positions = bot.monitor_positions(symbol)
                current_side = None

                if positions:
                    for pos in positions:
                        if pos.get("size", 0) > 0:
                            current_side = "long"
                        elif pos.get("size", 0) < 0:
                            current_side = "short"

                print(f"📍 Current Position: {current_side or 'None'}")

                # =================================================
                # 🔴 FORCE EXIT ON TREND FLIP (CRITICAL FIX)
                # =================================================
                if current_side == "long" and trend == "down":
                    print("🔁 Trend flipped DOWN → Closing LONG")
                    notifier.info("🔁 Trend flipped DOWN → Closing LONG")
                    bot.execute_simple_trade(symbol, "sell", size)
                    continue

                elif current_side == "short" and trend == "up":
                    print("🔁 Trend flipped UP → Closing SHORT")
                    notifier.info("🔁 Trend flipped UP → Closing SHORT")
                    bot.execute_simple_trade(symbol, "buy", size)
                    continue

                # =================================================
                # 🟢 ENTRY LOGIC
                # =================================================
                if signal == "buy" and current_side != "long":
                    print("🟢 BUY signal → Opening LONG")

                    if current_side == "short":
                        print("⚠️ Closing existing SHORT")
                        bot.execute_simple_trade(symbol, "buy", size)
                        time.sleep(2)

                    order = bot.execute_simple_trade(symbol, "buy", size)

                    if order:
                        time.sleep(1)
                        sl_price = supertrend_value or round(price * (1 - sl_pct), 2)
                        print(f"🛡️ Setting SL at {sl_price}")
                        bot.set_stop_loss(symbol, "sell", size, sl_price)

                        notifier.trade_entry(
                            symbol=symbol,
                            side="LONG",
                            entry=price,
                            stoploss=sl_price,
                            timeframe="15m"
                        )

                elif signal == "sell" and current_side != "short":
                    print("🔴 SELL signal → Opening SHORT")

                    if current_side == "long":
                        print("⚠️ Closing existing LONG")
                        bot.execute_simple_trade(symbol, "sell", size)
                        time.sleep(2)

                    order = bot.execute_simple_trade(symbol, "sell", size)

                    if order:
                        time.sleep(1)
                        sl_price = supertrend_value or round(price * (1 + sl_pct), 2)
                        print(f"🛡️ Setting SL at {sl_price}")
                        bot.set_stop_loss(symbol, "buy", size, sl_price)

                        notifier.trade_entry(
                            symbol=symbol,
                            side="SHORT",
                            entry=price,
                            stoploss=sl_price,
                            timeframe="15m"
                        )

                else:
                    notifier.info("⏸️ No action — holding position")

            except Exception as e:
                print(f"❌ Error during trading cycle: {e}")
                notifier.info(f"❌ Bot error: {e}")

    except KeyboardInterrupt:
        print("\n⛔ Bot stopped by user")
        notifier.info("⛔ Bot manually stopped")

        print("Final position check:")
        positions = bot.monitor_positions(symbol)
        print(positions)
        print("=" * 80)


# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID")
    )

    notifier.info("🚀 Supertrend bot started")
    main()
