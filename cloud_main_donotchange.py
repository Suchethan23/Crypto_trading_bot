from Bot.trading_bot import TradingBot
from utils.data_fetcher import DataFetcher
from Indicators.SuperTrend.supertrend import calculate_supertrend, get_supertrend_signal
from utils.telegramNotifier import TelegramNotifier

import json
import time
import os
import logging
from datetime import datetime, timedelta, timezone
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
    now = datetime.now(timezone.utc)

    # Minutes until next 15m boundary
    minutes_to_add = (15 - (now.minute % 15)) % 15
    if minutes_to_add == 0:
        minutes_to_add = 15

    next_close = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)

    sleep_seconds = (next_close - now).total_seconds()

    logger.info(
        f"⏳ Sleeping {int(sleep_seconds)}s until "
        f"{next_close.strftime('%H:%M:%S')} UTC"
    )

    time.sleep(max(1, sleep_seconds))

def verify_position_closed(bot, symbol, max_attempts=3):
    """
    Verify that position is actually closed
    Returns True if closed, False otherwise
    """
    logger.info(f"→ Entering verify_position_closed() | Symbol: {symbol} | Max attempts: {max_attempts}")
    
    for attempt in range(max_attempts):
        logger.info(f"  Verification attempt {attempt + 1}/{max_attempts}")
        time.sleep(1)
        
        try:
            positions = bot.monitor_positions(symbol)
            logger.info(f"  Positions returned: {positions}")
            
            if not positions or all(pos.get("size", 0) == 0 for pos in positions):
                logger.info("✓ Position verified as closed")
                logger.info("← Exiting verify_position_closed() returning True")
                return True
            
            logger.warning(f"⚠ Position still open on attempt {attempt + 1}/{max_attempts}")
            for pos in positions:
                logger.warning(f"  Position details: {pos}")
        except Exception as e:
            logger.error(f"✗ Error during position verification: {e}", exc_info=True)
    
    logger.error("✗ Position not closed after all attempts")
    logger.info("← Exiting verify_position_closed() returning False")
    return False


def get_current_position(bot, symbol):
    """
    Get current position side and size
    Returns: (side, size) where side is 'long', 'short', or None
    """
    logger.info(f"→ Entering get_current_position() | Symbol: {symbol}")
    
    try:
        positions = bot.monitor_positions(symbol)
        logger.info(f"  Raw positions data: {positions}")
        
        if not positions:
            logger.info("  No positions found")
            logger.info("← Exiting get_current_position() returning (None, 0)")
            return None, 0
        
        for pos in positions:
            size = pos.get("size", 0)
            logger.info(f"  Checking position: {pos}")
            logger.info(f"  Position size: {size}")
            
            if size > 0:
                logger.info(f"✓ Found LONG position with size: {size}")
                logger.info("← Exiting get_current_position() returning ('long', size)")
                return "long", size
            elif size < 0:
                abs_size = abs(size)
                logger.info(f"✓ Found SHORT position with size: {abs_size}")
                logger.info("← Exiting get_current_position() returning ('short', abs_size)")
                return "short", abs_size
        
        logger.info("  All positions have zero size")
        logger.info("← Exiting get_current_position() returning (None, 0)")
        return None, 0
        
    except Exception as e:
        logger.error(f"✗ Error getting position: {e}", exc_info=True)
        logger.info("← Exiting get_current_position() returning (None, 0) due to error")
        return None, 0


def close_position(bot, notifier, symbol, current_side, size):
    """
    Close current position with verification
    Returns True if successful, False otherwise
    """
    logger.info(f"→ Entering close_position() | Symbol: {symbol} | Side: {current_side} | Size: {size}")
    
    try:
        if current_side == "long":
            logger.info("  Executing SELL order to close LONG position")
            order = bot.execute_simple_trade(symbol, "sell", size)
            logger.info(f"  Order result: {order}")
            
        elif current_side == "short":
            logger.info("  Executing BUY order to close SHORT position")
            order = bot.execute_simple_trade(symbol, "buy", size)
            logger.info(f"  Order result: {order}")
            
        else:
            logger.info("  No position to close (current_side is None)")
            logger.info("← Exiting close_position() returning True")
            return True
        
        if not order:
            logger.error("✗ Failed to execute close order - order is None/False")
            notifier.info(f"❌ Failed to close {current_side.upper()} position")
            logger.info("← Exiting close_position() returning False")
            return False
        
        logger.info("  Order executed, verifying position closure...")
        # Verify position is closed
        if verify_position_closed(bot, symbol):
            logger.info(f"✓ {current_side.upper()} position closed successfully")
            logger.info("← Exiting close_position() returning True")
            return True
        else:
            logger.error("✗ Position not fully closed after verification attempts")
            notifier.info(f"⚠️ {current_side.upper()} position may not be fully closed")
            logger.info("← Exiting close_position() returning False")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error closing position: {e}", exc_info=True)
        notifier.info(f"❌ Error closing position: {e}")
        logger.info("← Exiting close_position() returning False due to exception")
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
    logger.info(f"→ Entering calculate_stop_loss() | Price: {price} | SuperTrend: {supertrend_value} | Side: {side} | Fallback: {fallback_pct}")
    
    if side == "long":
        logger.info("  Calculating stop loss for LONG position")
        # For longs, SuperTrend should be below price (support)
        if supertrend_value and supertrend_value < price:
            sl_price = supertrend_value
            logger.info(f"✓ Using SuperTrend SL: {sl_price} (SuperTrend is below price)")
        else:
            sl_price = price * (1 - fallback_pct)
            logger.info(f"⚠ Using fallback SL: {sl_price} ({fallback_pct*100}%) - SuperTrend invalid or above price")
            logger.info(f"  Reason: supertrend_value={supertrend_value}, price={price}")
    else:  # short
        logger.info("  Calculating stop loss for SHORT position")
        # For shorts, SuperTrend should be above price (resistance)
        if supertrend_value and supertrend_value > price:
            sl_price = supertrend_value
            logger.info(f"✓ Using SuperTrend SL: {sl_price} (SuperTrend is above price)")
        else:
            sl_price = price * (1 + fallback_pct)
            logger.info(f"⚠ Using fallback SL: {sl_price} ({fallback_pct*100}%) - SuperTrend invalid or below price")
            logger.info(f"  Reason: supertrend_value={supertrend_value}, price={price}")
    
    logger.info(f"← Exiting calculate_stop_loss() returning {sl_price}")
    return sl_price


def main(notifier):
    """
    Main trading loop
    
    Args:
        notifier: TelegramNotifier instance
    """
    logger.info("→ Entering main() function")
    
    # ---------------- INITIALIZATION ---------------- #
    logger.info("Initializing TradingBot and DataFetcher...")
    bot = TradingBot()
    fetcher = DataFetcher()
    logger.info("✓ Bot and Fetcher initialized")

    # Configuration
    symbol = "ETHUSD"
    timeframe="5m"
    size = 5
    sl_pct = 0.02  # 2% fallback SL
    min_candles_required = 50  # Minimum candles needed for SuperTrend

    logger.info("=" * 80)
    logger.info("🚀 SUPERTREND BOT STARTED")
    logger.info("=" * 80)
    logger.info(f"Symbol        : {symbol}")
    logger.info(f"Position Size : {size}")
    logger.info(f"Stop Loss     : {sl_pct*100}% (fallback)")
    logger.info(f"Execution     : Every {timeframe} candle close")
    logger.info(f"Min Candles   : {min_candles_required}")
    logger.info("=" * 80)
    logger.info("\nPress Ctrl+C to stop...\n")

    consecutive_errors = 0
    max_consecutive_errors = 5
    logger.info(f"Error tracking initialized: {consecutive_errors}/{max_consecutive_errors}")

    try:
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"ITERATION #{iteration} | Consecutive Errors: {consecutive_errors}/{max_consecutive_errors}")
            logger.info(f"{'='*80}")
            
            logger.info(f"⏳ Waiting for next {timeframe} candle close...")
            wait_until_next_15m()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n[{timestamp}] 🔍 Checking market...")

            try:
                # ---------------- FETCH DATA ---------------- #
                logger.info("STEP 1: Fetching candle data...")
                candles = fetcher.get_candles_in_batches(symbol, timeframe)
                logger.info(f"  Candles fetched: {len(candles) if candles else 0} candles")
                
                # Validate data
                if not candles or len(candles) < min_candles_required:
                    logger.warning(f"⚠ Insufficient candle data: {len(candles) if candles else 0} candles (required: {min_candles_required})")
                    notifier.info(f"⚠️ Insufficient data: {len(candles) if candles else 0} candles")
                    consecutive_errors += 1
                    logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("✗ Too many consecutive errors, stopping bot")
                        notifier.info("❌ Bot stopped due to repeated errors")
                        break
                    continue
                
                logger.info("✓ Sufficient candle data received")
                logger.info(f"  Sample candle data (first): {candles[0] if candles else 'None'}")
                logger.info(f"  Sample candle data (last): {candles[-1] if candles else 'None'}")
                
                logger.info("STEP 2: Calculating SuperTrend...")
                supertrend_data = calculate_supertrend(candles)
                logger.info(f"  SuperTrend data calculated: {len(supertrend_data) if supertrend_data else 0} data points")
                
                # Export for analysis
                logger.info("  Exporting SuperTrend data to JSON...")
                fetcher.export_to_json(supertrend_data, "supertrend_ETHUSD.json")
                logger.info("✓ Data exported to supertrend_ETHUSD.json")

                # ---------------- SIGNAL GENERATION ---------------- #
                logger.info("STEP 3: Generating trading signal...")
                signal, price, trend, supertrend_value = get_supertrend_signal(supertrend_data)
                
                logger.info(f"  Signal returned: {signal}")
                logger.info(f"  Price: {price}")
                logger.info(f"  Trend: {trend}")
                logger.info(f"  SuperTrend value: {supertrend_value}")
                
                # Validate signal
                if signal not in ["buy", "sell", "hold", None]:
                    logger.warning(f"⚠ Invalid signal received: {signal} | Type: {type(signal)}")
                    continue
                
                # If signal is None or hold, treat as hold
                if signal is None:
                    logger.info("  Signal is None, converting to 'hold'")
                    signal = "hold"

                logger.info(
                    f"📊 FINAL SIGNAL: {signal.upper()} | "
                    f"Price: {price} | "
                    f"Trend: {trend} | "
                    f"SuperTrend: {supertrend_value}"
                )

                # ---------------- POSITION CHECK ---------------- #
                logger.info("STEP 4: Checking current position...")
                current_side, current_size = get_current_position(bot, symbol)
                logger.info(f"📍 Current Position: {current_side.upper() if current_side else 'NONE'} | Size: {current_size}")

                # =================================================
                # 🔴 FORCE EXIT ON TREND FLIP (CRITICAL)
                # =================================================
                logger.info("STEP 5: Checking for trend flip exit conditions...")
                
                if current_side == "long" and trend == "down":
                    logger.info("🔁 TREND FLIP DETECTED: LONG position + DOWN trend")
                    logger.info("  Action: Closing LONG position immediately")
                    notifier.info("🔁 Trend flipped DOWN → Closing LONG")
                    
                    if close_position(bot, notifier, symbol, current_side, current_size):
                        logger.info("✓ LONG position closed due to trend flip")
                        consecutive_errors = 0
                        logger.info(f"  Consecutive errors reset to: {consecutive_errors}")
                    else:
                        logger.error("✗ Failed to close LONG position on trend flip")
                        consecutive_errors += 1
                        logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                    continue

                elif current_side == "short" and trend == "up":
                    logger.info("🔁 TREND FLIP DETECTED: SHORT position + UP trend")
                    logger.info("  Action: Closing SHORT position immediately")
                    notifier.info("🔁 Trend flipped UP → Closing SHORT")
                    
                    if close_position(bot, notifier, symbol, current_side, current_size):
                        logger.info("✓ SHORT position closed due to trend flip")
                        consecutive_errors = 0
                        logger.info(f"  Consecutive errors reset to: {consecutive_errors}")
                    else:
                        logger.error("✗ Failed to close SHORT position on trend flip")
                        consecutive_errors += 1
                        logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                    continue
                
                logger.info("  No trend flip detected - proceeding to entry logic")

                # =================================================
                # 🟢 ENTRY LOGIC
                # =================================================
                logger.info("STEP 6: Processing entry/exit logic...")
                
                if signal == "buy" and current_side != "long":
                    logger.info("🟢 BUY SIGNAL with no LONG position")
                    logger.info(f"  Current position: {current_side}")
                    logger.info("  Action: Opening LONG position")

                    # Close opposite position if exists
                    if current_side == "short":
                        logger.info("⚠️ Opposite SHORT position exists - closing first")
                        if not close_position(bot, notifier, symbol, current_side, current_size):
                            logger.error("✗ Failed to close SHORT, skipping LONG entry")
                            consecutive_errors += 1
                            logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                            continue
                        logger.info("✓ SHORT position closed successfully")
                        logger.info("  Waiting 2 seconds before opening LONG...")
                        time.sleep(2)

                    # Open LONG position
                    logger.info("  Executing BUY order...")
                    order = bot.execute_simple_trade(symbol, "buy", size)
                    logger.info(f"  Order result: {order}")

                    if order:
                        logger.info("✅ LONG position opened successfully")
                        logger.info("  Waiting 1 second before setting stop loss...")
                        time.sleep(1)
                        
                        # Calculate and set stop loss
                        sl_price = calculate_stop_loss(price, supertrend_value, "long", sl_pct)
                        logger.info(f"🛡️ Setting stop loss at {sl_price}")
                        
                        sl_order = bot.set_stop_loss(symbol, "sell", size, sl_price)
                        logger.info(f"  Stop loss order result: {sl_order}")
                        
                        if sl_order:
                            logger.info("✅ Stop loss set successfully")
                        else:
                            logger.warning("⚠️ Failed to set stop loss")

                        logger.info("  Sending trade notification...")
                        notifier.trade_entry(
                            symbol=symbol,
                            side="LONG",
                            entry=price,
                            stoploss=sl_price,
                            timeframe=timeframe
                        )
                        consecutive_errors = 0
                        logger.info(f"✓ Consecutive errors reset to: {consecutive_errors}")
                    else:
                        logger.error("❌ Failed to open LONG position - order returned None/False")
                        notifier.info("❌ Failed to open LONG")
                        consecutive_errors += 1
                        logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")

                elif signal == "sell" and current_side != "short":
                    logger.info("🔴 SELL SIGNAL with no SHORT position")
                    logger.info(f"  Current position: {current_side}")
                    logger.info("  Action: Opening SHORT position")

                    # Close opposite position if exists
                    if current_side == "long":
                        logger.info("⚠️ Opposite LONG position exists - closing first")
                        if not close_position(bot, notifier, symbol, current_side, current_size):
                            logger.error("✗ Failed to close LONG, skipping SHORT entry")
                            consecutive_errors += 1
                            logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                            continue
                        logger.info("✓ LONG position closed successfully")
                        logger.info("  Waiting 2 seconds before opening SHORT...")
                        time.sleep(2)

                    # Open SHORT position
                    logger.info("  Executing SELL order...")
                    order = bot.execute_simple_trade(symbol, "sell", size)
                    logger.info(f"  Order result: {order}")

                    if order:
                        logger.info("✅ SHORT position opened successfully")
                        logger.info("  Waiting 1 second before setting stop loss...")
                        time.sleep(1)
                        
                        # Calculate and set stop loss
                        sl_price = calculate_stop_loss(price, supertrend_value, "short", sl_pct)
                        logger.info(f"🛡️ Setting stop loss at {sl_price}")
                        
                        sl_order = bot.set_stop_loss(symbol, "buy", size, sl_price)
                        logger.info(f"  Stop loss order result: {sl_order}")
                        
                        if sl_order:
                            logger.info("✅ Stop loss set successfully")
                        else:
                            logger.warning("⚠️ Failed to set stop loss")

                        logger.info("  Sending trade notification...")
                        notifier.trade_entry(
                            symbol=symbol,
                            side="SHORT",
                            entry=price,
                            stoploss=sl_price,
                            timeframe=timeframe
                        )
                        consecutive_errors = 0
                        logger.info(f"✓ Consecutive errors reset to: {consecutive_errors}")
                    else:
                        logger.error("❌ Failed to open SHORT position - order returned None/False")
                        notifier.info("❌ Failed to open SHORT")
                        consecutive_errors += 1
                        logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")

                else:
                    logger.info("⏸️ No action required")
                    logger.info(f"  Signal: {signal} | Current position: {current_side}")
                    logger.info("  Reason: Either holding current position or no valid entry signal")
                    notifier.info("⏸️ No action — hold on for position")
                    consecutive_errors = 0
                    logger.info(f"  Consecutive errors reset to: {consecutive_errors}")

                # Check if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"✗ CRITICAL: Too many consecutive errors ({consecutive_errors}/{max_consecutive_errors})")
                    logger.error("  Stopping bot to prevent further issues")
                    notifier.info("❌ Bot stopped due to repeated errors")
                    break

            except Exception as e:
                logger.error(f"❌ Error during trading cycle: {e}", exc_info=True)
                logger.error(f"  Error type: {type(e).__name__}")
                logger.error(f"  Error details: {str(e)}")
                notifier.info(f"❌ Bot error: {str(e)[:100]}")
                consecutive_errors += 1
                logger.warning(f"  Consecutive errors incremented to: {consecutive_errors}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"✗ CRITICAL: Too many consecutive errors ({consecutive_errors}/{max_consecutive_errors})")
                    logger.error("  Stopping bot due to exception handling")
                    notifier.info("❌ Bot stopped due to repeated errors")
                    break

    except KeyboardInterrupt:
        logger.info("\n⛔ Bot stopped by user (KeyboardInterrupt)")
        notifier.info("⛔ Bot manually stopped")

    finally:
        logger.info("\nEntering cleanup phase...")
        logger.info("Performing final position check:")
        try:
            positions = bot.monitor_positions(symbol)
            logger.info(f"Final positions: {positions}")
        except Exception as e:
            logger.error(f"✗ Error checking final positions: {e}", exc_info=True)
        logger.info("=" * 80)
        logger.info("← Exiting main() function")


# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    logger.info("="*80)
    logger.info("PROGRAM STARTED")
    logger.info("="*80)
    
    # Initialize notifier
    logger.info("Initializing TelegramNotifier...")
    logger.info(f"  Bot token: {'*' * 10}{os.getenv('TELEGRAM_BOT_TOKEN', '')[-4:] if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET'}")
    logger.info(f"  Chat ID: {os.getenv('TELEGRAM_CHAT_ID', 'NOT SET')}")
    
    notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID")
    )
    logger.info("✓ TelegramNotifier initialized")

    try:
        logger.info("Sending startup notification...")
        notifier.info("🚀 Supertrend bot started")
        logger.info("✓ Startup notification sent")
        
        logger.info("Calling main() function...")
        main(notifier)
        
    except Exception as e:
        logger.critical(f"❌ CRITICAL ERROR in main: {e}", exc_info=True)
        logger.critical(f"  Error type: {type(e).__name__}")
        logger.critical(f"  Error details: {str(e)}")
        notifier.info(f"❌ Critical error: {str(e)[:100]}")
        
    finally:
        logger.info("Sending shutdown notification...")
        notifier.info("👋 Bot shutdown complete")
        logger.info("="*80)
        logger.info("PROGRAM ENDED")
        logger.info("="*80)