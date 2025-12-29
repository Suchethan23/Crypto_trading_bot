from utils.data_fetcher import DataFetcher

fetcher=DataFetcher()
    

def get_supertrend_signal(supertrend_data):
    """
    Get current Supertrend signal
    
    Args:
        supertrend_data: List of supertrend data
    
    Returns:
        tuple: (signal, current_price, trend)
        signal: 'buy', 'sell', or 'hold'
    """
    if len(supertrend_data) < 2:
        return 'hold', None, None
    
    current = supertrend_data[-1]
    prev = supertrend_data[-2]
    
    # Check if supertrend values and trends are valid
    if (not current['trend'] or not prev['trend'] or 
        current['supertrend'] is None or prev['supertrend'] is None):
        return 'hold', current['close'], current.get('trend')
    
    # Trend change from down to up = BUY signal
    if prev['trend'] == 'down' and current['trend'] == 'up':
        return 'buy', current['close'], current['trend'],current['supertrend']
    
    # Trend change from up to down = SELL signal
    elif prev['trend'] == 'up' and current['trend'] == 'down':
        return 'sell', current['close'], current['trend'],current['supertrend']
    
    # No trend change = HOLD
    else:
        return 'hold', current['close'], current['trend'],current['supertrend']

# def calculate_supertrend(data,period=10, multiplier=3):
    

#     result = []
#     tr_list = []

#     prev_final_upper = None
#     prev_final_lower = None
#     prev_trend = None

#     if not data or len(data) == 0:
#         return []

#     for i in range(len(data)):
#         time_val, open_price, high, low, close, volume = data[i]

#         if i == 0:
#             result.append({
#                 "time": time_val,
#                 "open": open_price,
#                 "high": high,
#                 "low": low,
#                 "close": close,
#                 "atr": None,
#                 "basic_upper": None,
#                 "basic_lower": None,
#                 "final_upper": None,
#                 "final_lower": None,
#                 "supertrend": None,
#                 "trend": None
#             })
#             continue

#         prev_close = data[i - 1][4]

#         # True Range
#         tr = max(
#             high - low,
#             abs(high - prev_close),
#             abs(low - prev_close)
#         )

#         tr_list.append(tr)
#         if len(tr_list) > period:
#             tr_list.pop(0)

#         if len(tr_list) < period:
#             result.append({
#                 "time": time_val,
#                 "open": open_price,
#                 "high": high,
#                 "low": low,
#                 "close": close,
#                 "atr": None,
#                 "basic_upper": None,
#                 "basic_lower": None,
#                 "final_upper": None,
#                 "final_lower": None,
#                 "supertrend": None,
#                 "trend": None
#             })
#             continue

#         atr = sum(tr_list) / period

#         # Basic Bands
#         hl2 = (high + low) / 2
#         basic_upper = hl2 + multiplier * atr
#         basic_lower = hl2 - multiplier * atr

#         # Final Bands (STATEFUL — this is the key)
#         if prev_final_upper is None or basic_upper < prev_final_upper or prev_close > prev_final_upper:
#             final_upper = basic_upper
#         else:
#             final_upper = prev_final_upper

#         if prev_final_lower is None or basic_lower > prev_final_lower or prev_close < prev_final_lower:
#             final_lower = basic_lower
#         else:
#             final_lower = prev_final_lower

#         # Trend determination
#         if prev_trend is None:
#             trend = "up"   # safer default for first valid candle
#         elif prev_trend == "up":
#             trend = "up" if close > final_lower else "down"
#         else:
#             trend = "down" if close < final_upper else "up"

#         # Supertrend line
#         supertrend = final_lower if trend == "up" else final_upper

#         # Persist state
#         prev_final_upper = final_upper
#         prev_final_lower = final_lower
#         prev_trend = trend

#         result.append({
#             "time": time_val,
#             "open": open_price,
#             "high": high,
#             "low": low,
#             "close": close,

#             "atr": atr,
#             "basic_upper": basic_upper,
#             "basic_lower": basic_lower,
#             "final_upper": final_upper,
#             "final_lower": final_lower,

#             "supertrend": supertrend,
#             "trend": trend
#         })

#     return result
#above is sma atr

def calculate_supertrend(data, period=10, multiplier=3):
    """
    Calculate SuperTrend indicator.
    
    Args:
        data: List of (time, open, high, low, close, volume) tuples
        period: ATR period (default: 10)
        multiplier: ATR multiplier (default: 3)
    
    Returns:
        List of dictionaries containing OHLC data and SuperTrend calculations
    """
    result = []

    prev_final_upper = None
    prev_final_lower = None
    prev_trend = None
    prev_atr = None
    tr_accumulator = []

    if not data or len(data) < period + 1:
        return []

    for i in range(len(data)):
        time_val, open_price, high, low, close, volume = data[i]

        if i == 0:
            result.append({
                "time": time_val,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "atr": None,
                "basic_upper": None,
                "basic_lower": None,
                "final_upper": None,
                "final_lower": None,
                "supertrend": None,
                "trend": None
            })
            continue

        prev_close = data[i - 1][4]

        # True Range
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        # ATR calculation (Wilder) - Correct seeding
        if i < period:
            # Accumulate TRs for initial ATR calculation
            tr_accumulator.append(tr)
            result.append({
                "time": time_val,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "atr": None,
                "basic_upper": None,
                "basic_lower": None,
                "final_upper": None,
                "final_lower": None,
                "supertrend": None,
                "trend": None
            })
            continue
        elif i == period:
            # INCLUDE current TR to make period values
            atr = (sum(tr_accumulator) + tr) / period
        else:
            # Use Wilder's smoothing
            atr = ((prev_atr * (period - 1)) + tr) / period

        prev_atr = atr

        # Basic Bands
        hl2 = (high + low) / 2
        basic_upper = hl2 + multiplier * atr
        basic_lower = hl2 - multiplier * atr

        # Final Bands (stateful)
        if prev_final_upper is None or basic_upper < prev_final_upper or prev_close > prev_final_upper:
            final_upper = basic_upper
        else:
            final_upper = prev_final_upper

        if prev_final_lower is None or basic_lower > prev_final_lower or prev_close < prev_final_lower:
            final_lower = basic_lower
        else:
            final_lower = prev_final_lower

        # Trend logic (TradingView / Delta exact)
        if prev_trend is None:
            trend = "up"
        elif prev_trend == "up":
            trend = "up" if close > final_lower else "down"
        else:
            trend = "down" if close < final_upper else "up"

        supertrend = final_lower if trend == "up" else final_upper

        prev_final_upper = final_upper
        prev_final_lower = final_lower
        prev_trend = trend

        result.append({
            "time": time_val,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "atr": atr,
            "basic_upper": basic_upper,
            "basic_lower": basic_lower,
            "final_upper": final_upper,
            "final_lower": final_lower,
            "supertrend": supertrend,
            "trend": trend
        })

    return result

# data=calculate_supertrend()
# fetcher.export_to_json(data,"supertrend.json")