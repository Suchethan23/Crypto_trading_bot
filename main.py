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
import logging
from datetime import datetime
from dotenv import load_dotenv

import sys
sys.stdout.reconfigure(encoding='utf-8')


load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def wait_until_next_15m():
    """
    Block execution until the next 15-minute candle close
    Ensures fresh candle data (no partial candles)
    """
    while True:
        now = datetime.now()
        if now.minute % 1 == 0 and now.second < 2:
            logger.info("15m candle close detected")
            return
        time.sleep(1)


def verify_position_closed(bot, symbol, max_attempts=3):
    """
    Verify that position is actually closed
    Returns True if closed, False otherwise
    """
    for attempt in range(max_attempts):
        time.sleep(1)
        positions = bot.monitor_positions(symbol)
        if not positions or all(pos.get("size", 0) == 0 for pos in positions):
            return True
        logger.warning(f"Position still open, attempt {attempt + 1}/{max_attempts}")
    return False


def get_current_position(bot, symbol):
    """
    Get current position side and size
    Returns: (side, size) where side is 'long', 'short', or None
    """
    try:
        positions = bot.monitor_positions(symbol)
        if not positions:
            return None, 0
        
        for pos in positions:
            size = pos.get("size", 0)
            if size > 0:
                return "long", size
            elif size < 0:
                return "short", abs(size)
        
        return None, 0
    except Exception as e:
        logger.error(f"Error getting position: {e}")
        return None, 0


def close_position(bot, notifier, symbol, current_side, size):
    """
    Close current position with verification
    Returns True if successful, False otherwise
    """
    try:
        if current_side == "long":
            logger.info("Closing LONG position")
            order = bot.execute_simple_trade(symbol, "sell", size)
        elif current_side == "short":
            logger.info("Closing SHORT position")
            order = bot.execute_simple_trade(symbol, "buy", size)
        else:
            return True  # No position to close
        
        if not order:
            logger.error("Failed to execute close order")
            notifier.info(f"❌ Failed to close {current_side.upper()} position")
            return False
        
        # Verify position is closed
        if verify_position_closed(bot, symbol):
            logger.info(f"{current_side.upper()} position closed successfully")
            return True
        else:
            logger.error("Position not fully closed after attempts")
            notifier.info(f"⚠️ {current_side.upper()} position may not be fully closed")
            return False
            
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        notifier.info(f"❌ Error closing position: {e}")
        return False


def calculate_stop_loss(price, supertrend_value, side, fallback_pct=0.02):
    """
    Calculate stop loss using SuperTrend value with fallback
    
    Args:
        price: Current market price
        supertrend_value: SuperTrend indicator value
        side: 'long' or 'short'
        fallback_pct: Fallback percentage if SuperTrend is invalid
    
    Returns:
        Stop loss price
    """
    if side == "long":
        # For longs, SuperTrend should be below price (support)
        if supertrend_value and supertrend_value < price:
            sl_price = supertrend_value
            logger.info(f"Using SuperTrend SL: {sl_price}")
        else:
            sl_price = price * (1 - fallback_pct)
            logger.info(f"Using fallback SL: {sl_price} ({fallback_pct*100}%)")
    else:  # short
        # For shorts, SuperTrend should be above price (resistance)
        if supertrend_value and supertrend_value > price:
            sl_price = supertrend_value
            logger.info(f"Using SuperTrend SL: {sl_price}")
        else:
            sl_price = price * (1 + fallback_pct)
            logger.info(f"Using fallback SL: {sl_price} ({fallback_pct*100}%)")
    
    return sl_price


def main(notifier):
    """
    Main trading loop
    
    Args:
        notifier: TelegramNotifier instance
    """
    # ---------------- INITIALIZATION ---------------- #
    bot = TradingBot()
    fetcher = DataFetcher()

    # Configuration
    symbol = "ETHUSD"
    timeframe="1m"
    size = 1
    sl_pct = 0.02  # 2% fallback SL
    min_candles_required = 50  # Minimum candles needed for SuperTrend

    logger.info("=" * 80)
    logger.info("🚀 SUPERTREND BOT STARTED")
    logger.info("=" * 80)
    logger.info(f"Symbol        : {symbol}")
    logger.info(f"Position Size : {size}")
    logger.info(f"Stop Loss     : {sl_pct*100}% (fallback)")
    logger.info("Execution     : Every {timeframe} candle close")
    logger.info("=" * 80)
    logger.info("\nPress Ctrl+C to stop...\n")

    consecutive_errors = 0
    max_consecutive_errors = 5

    try:
        while True:
            logger.info("⏳ Waiting for next {timeframe} candle close...")
            wait_until_next_15m()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n[{timestamp}] 🔍 Checking market...")

            try:
                # ---------------- FETCH DATA ---------------- #
                candles = fetcher.get_candles_in_batches(symbol, timeframe)
                
                # Validate data
                if not candles or len(candles) < min_candles_required:
                    logger.warning(f"Insufficient candle data: {len(candles) if candles else 0} candles")
                    notifier.info(f"⚠️ Insufficient data: {len(candles) if candles else 0} candles")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive errors, stopping bot")
                        notifier.info("❌ Bot stopped due to repeated errors")
                        break
                    continue
                
                supertrend_data = calculate_supertrend(candles)
                
                # Export for analysis
                fetcher.export_to_json(supertrend_data, "supertrend_ETHUSD.json")

                # ---------------- SIGNAL GENERATION ---------------- #
                signal, price, trend, supertrend_value = get_supertrend_signal(supertrend_data)
                
                # Validate signal
                if signal not in ["buy", "sell", "hold", None]:
                    logger.warning(f"Invalid signal received: {signal}")
                    continue
                
                # If signal is None or hold, treat as hold
                if signal is None:
                    signal = "hold"

                logger.info(
                    f"📊 Signal: {signal.upper()} | "
                    f"Price: {price} | "
                    f"Trend: {trend} | "
                    f"SuperTrend: {supertrend_value}"
                )

                # ---------------- POSITION CHECK ---------------- #
                current_side, current_size = get_current_position(bot, symbol)
                logger.info(f"📍 Current Position: {current_side.upper() if current_side else 'None'}")

                # =================================================
                # 🔴 FORCE EXIT ON TREND FLIP (CRITICAL)
                # =================================================
                if current_side == "long" and trend == "down":
                    logger.info("🔁 Trend flipped DOWN → Closing LONG")
                    notifier.info("🔁 Trend flipped DOWN → Closing LONG")
                    
                    if close_position(bot, notifier, symbol, current_side, current_size):
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        consecutive_errors += 1
                    continue

                elif current_side == "short" and trend == "up":
                    logger.info("🔁 Trend flipped UP → Closing SHORT")
                    notifier.info("🔁 Trend flipped UP → Closing SHORT")
                    
                    if close_position(bot, notifier, symbol, current_side, current_size):
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                    continue

                # =================================================
                # 🟢 ENTRY LOGIC
                # =================================================
                if signal == "buy" and current_side != "long":
                    logger.info("🟢 BUY signal → Opening LONG")

                    # Close opposite position if exists
                    if current_side == "short":
                        logger.info("⚠️ Closing existing SHORT")
                        if not close_position(bot, notifier, symbol, current_side, current_size):
                            logger.error("Failed to close SHORT, skipping entry")
                            consecutive_errors += 1
                            continue
                        time.sleep(2)  # Extra buffer after close

                    # Open LONG position
                    order = bot.execute_simple_trade(symbol, "buy", size)

                    if order:
                        logger.info("✅ LONG position opened")
                        # notifer.info("opening long postion", price)
                        time.sleep(1)
                        
                        # Calculate and set stop loss
                        sl_price = calculate_stop_loss(price, supertrend_value, "long", sl_pct)
                        logger.info(f"🛡️ Setting SL at {sl_price}")
                        
                        sl_order = bot.set_stop_loss(symbol, "sell", size, sl_price)
                        if sl_order:
                            logger.info("✅ Stop loss set successfully")
                        else:
                            logger.warning("⚠️ Failed to set stop loss")

                        notifier.trade_entry(
                            symbol=symbol,
                            side="LONG",
                            entry=price,
                            stoploss=sl_price,
                            timeframe=timeframe
                        )
                        consecutive_errors = 0  # Reset on success
                    else:
                        logger.error("❌ Failed to open LONG position")
                        notifier.info("❌ Failed to open LONG")
                        consecutive_errors += 1

                elif signal == "sell" and current_side != "short":
                    logger.info("🔴 SELL signal → Opening SHORT")

                    # Close opposite position if exists
                    if current_side == "long":
                        logger.info("⚠️ Closing existing LONG")
                        if not close_position(bot, notifier, symbol, current_side, current_size):
                            logger.error("Failed to close LONG, skipping entry")
                            consecutive_errors += 1
                            continue
                        time.sleep(2)  # Extra buffer after close

                    # Open SHORT position
                    order = bot.execute_simple_trade(symbol, "sell", size)

                    if order:
                        logger.info("✅ SHORT position opened")
                        time.sleep(1)
                        
                        # Calculate and set stop loss
                        sl_price = calculate_stop_loss(price, supertrend_value, "short", sl_pct)
                        logger.info(f"🛡️ Setting SL at {sl_price}")
                        
                        sl_order = bot.set_stop_loss(symbol, "buy", size, sl_price)
                        if sl_order:
                            logger.info("✅ Stop loss set successfully")
                        else:
                            logger.warning("⚠️ Failed to set stop loss")

                        notifier.trade_entry(
                            symbol=symbol,
                            side="SHORT",
                            entry=price,
                            stoploss=sl_price,
                            timeframe=timeframe
                        )
                        consecutive_errors = 0  # Reset on success
                    else:
                        logger.error("❌ Failed to open SHORT position")
                        notifier.info("❌ Failed to open SHORT")
                        consecutive_errors += 1

                else:
                    logger.info("⏸️ No action — holding position")
                    notifier.info("⏸️ No action — hold on for position")
                    consecutive_errors = 0  # Reset on normal operation

                # Check if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, stopping bot")
                    notifier.info("❌ Bot stopped due to repeated errors")
                    break

            except Exception as e:
                logger.error(f"❌ Error during trading cycle: {e}", exc_info=True)
                notifier.info(f"❌ Bot error: {str(e)[:100]}")
                consecutive_errors += 1
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, stopping bot")
                    notifier.info("❌ Bot stopped due to repeated errors")
                    break

    except KeyboardInterrupt:
        logger.info("\n⛔ Bot stopped by user")
        notifier.info("⛔ Bot manually stopped")

    finally:
        logger.info("Final position check:")
        try:
            positions = bot.monitor_positions(symbol)
            logger.info(positions)
        except Exception as e:
            logger.error(f"Error checking final positions: {e}")
        logger.info("=" * 80)


# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    # Initialize notifier
    notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID")
    )

    try:
        notifier.info("🚀 Supertrend bot started")
        main(notifier)
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        notifier.info(f"❌ Critical error: {str(e)[:100]}")
    finally:
        notifier.info("👋 Bot shutdown complete")