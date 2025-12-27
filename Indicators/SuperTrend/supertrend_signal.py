# ==================== strategies/supertrend_signal.py ====================
"""
Supertrend signal generator with incremental updates
Works with your existing Supertrend calculation logic
"""
from typing import Dict, Optional, List
from utils.data_fetcher import DataFetcher


class SupertrendState:
    """Maintains Supertrend state for incremental calculation"""
    
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        self.period = period
        self.multiplier = multiplier
        
        # State variables
        self.tr_list = []
        self.prev_final_upper = None
        self.prev_final_lower = None
        self.prev_trend = None
        self.prev_close = None
        
        # Last calculated values
        self.last_supertrend_data = None
    
    def reset(self):
        """Reset state to recalculate from scratch"""
        self.tr_list = []
        self.prev_final_upper = None
        self.prev_final_lower = None
        self.prev_trend = None
        self.prev_close = None
        self.last_supertrend_data = None
    
    def update(self, candle: List) -> Dict:
        """
        Update Supertrend with new candle data
        
        Args:
            candle: [time, open, high, low, close, volume]
        
        Returns:
            Dict with updated Supertrend values
        """
        time_val, open_price, high, low, close, volume = candle
        
        # First candle or insufficient data
        if self.prev_close is None:
            self.prev_close = close
            return {
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
            }
        
        # Calculate True Range
        tr = max(
            high - low,
            abs(high - self.prev_close),
            abs(low - self.prev_close)
        )
        
        self.tr_list.append(tr)
        if len(self.tr_list) > self.period:
            self.tr_list.pop(0)
        
        # Need minimum period data
        if len(self.tr_list) < self.period:
            self.prev_close = close
            return {
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
            }
        
        # Calculate ATR
        atr = sum(self.tr_list) / self.period
        
        # Basic Bands
        hl2 = (high + low) / 2
        basic_upper = hl2 + self.multiplier * atr
        basic_lower = hl2 - self.multiplier * atr
        
        # Final Bands (STATEFUL)
        if self.prev_final_upper is None or basic_upper < self.prev_final_upper or self.prev_close > self.prev_final_upper:
            final_upper = basic_upper
        else:
            final_upper = self.prev_final_upper
        
        if self.prev_final_lower is None or basic_lower > self.prev_final_lower or self.prev_close < self.prev_final_lower:
            final_lower = basic_lower
        else:
            final_lower = self.prev_final_lower
        
        # Trend determination
        if self.prev_trend is None:
            trend = "up"  # Default for first valid candle
        elif self.prev_trend == "up":
            trend = "up" if close > final_lower else "down"
        else:
            trend = "down" if close < final_upper else "up"
        
        # Supertrend line
        supertrend = final_lower if trend == "up" else final_upper
        
        # Update state
        self.prev_final_upper = final_upper
        self.prev_final_lower = final_lower
        self.prev_trend = trend
        self.prev_close = close
        
        # Store result
        result = {
            "time": time_val,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "atr": round(atr, 2),
            "basic_upper": round(basic_upper, 2),
            "basic_lower": round(basic_lower, 2),
            "final_upper": round(final_upper, 2),
            "final_lower": round(final_lower, 2),
            "supertrend": round(supertrend, 2),
            "trend": trend
        }
        
        self.last_supertrend_data = result
        return result


class SupertrendSignalGenerator:
    """Generate trading signals based on Supertrend"""
    
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        """
        Initialize Signal Generator
        
        Args:
            period: ATR period (default 10)
            multiplier: ATR multiplier (default 3.0)
        """
        self.period = period
        self.multiplier = multiplier
        self.state = SupertrendState(period, multiplier)
        self.data_fetcher = DataFetcher()
        
        # Signal tracking
        self.last_signal = None
        self.last_signal_time = None
    
    def initialize_from_history(self, historical_data: List[List]) -> Dict:
        """
        Initialize Supertrend state from historical data
        
        Args:
            historical_data: List of candles [[time, open, high, low, close, volume], ...]
        
        Returns:
            Latest Supertrend data
        """
        self.state.reset()
        
        latest = None
        for candle in historical_data:
            latest = self.state.update(candle)
        
        return latest
    
    def update_with_new_candle(self, new_candle: List) -> Dict:
        """
        Update Supertrend with a new candle
        
        Args:
            new_candle: [time, open, high, low, close, volume]
        
        Returns:
            Updated Supertrend data
        """
        return self.state.update(new_candle)
    
    def generate_signal(self, current_data: Dict, previous_data: Optional[Dict] = None) -> Dict:
        """
        Generate trading signal from Supertrend data
        
        Args:
            current_data: Current candle Supertrend data
            previous_data: Previous candle Supertrend data (optional)
        
        Returns:
            Signal information dict
        """
        if not current_data or current_data.get('trend') is None:
            return {
                'signal': 'NO_SIGNAL',
                'reason': 'Insufficient Supertrend data',
                'timestamp': current_data.get('time') if current_data else None
            }
        
        current_trend = current_data.get('trend')
        current_close = current_data.get('close')
        current_supertrend = current_data.get('supertrend')
        current_atr = current_data.get('atr')
        
        # If no previous data, use state
        if previous_data is None and self.state.last_supertrend_data:
            # Use the trend from before the current update
            # We need to track previous trend separately
            previous_trend = self.last_signal_trend if hasattr(self, 'last_signal_trend') else None
        else:
            previous_trend = previous_data.get('trend') if previous_data else None
        
        signal_data = {
            'timestamp': current_data.get('time'),
            'close': current_close,
            'supertrend': current_supertrend,
            'atr': current_atr,
            'current_trend': current_trend,
            'previous_trend': previous_trend,
            'signal': 'HOLD',
            'action': None,
            'reason': '',
            'entry_price': None,
            'stop_loss': None,
            'take_profit': None,
            'risk_reward_ratio': None
        }
        
        # Detect trend change
        if previous_trend and current_trend != previous_trend:
            
            # BUY SIGNAL: Trend changed from DOWN to UP
            if current_trend == 'up':
                signal_data['signal'] = 'BUY'
                signal_data['action'] = 'OPEN_LONG'
                signal_data['reason'] = '🟢 Supertrend: DOWN → UP (Bullish reversal)'
                signal_data['entry_price'] = current_close
                signal_data['stop_loss'] = current_supertrend
                
                # Take profit at 2x ATR
                signal_data['take_profit'] = current_close + (2 * current_atr)
                
                # Calculate risk-reward
                risk = abs(current_close - current_supertrend)
                reward = abs(signal_data['take_profit'] - current_close)
                signal_data['risk_reward_ratio'] = round(reward / risk, 2) if risk > 0 else 0
                
                self.last_signal = 'BUY'
                self.last_signal_time = current_data.get('time')
            
            # SELL SIGNAL: Trend changed from UP to DOWN
            elif current_trend == 'down':
                signal_data['signal'] = 'SELL'
                signal_data['action'] = 'OPEN_SHORT'
                signal_data['reason'] = '🔴 Supertrend: UP → DOWN (Bearish reversal)'
                signal_data['entry_price'] = current_close
                signal_data['stop_loss'] = current_supertrend
                
                # Take profit at 2x ATR
                signal_data['take_profit'] = current_close - (2 * current_atr)
                
                # Calculate risk-reward
                risk = abs(current_supertrend - current_close)
                reward = abs(current_close - signal_data['take_profit'])
                signal_data['risk_reward_ratio'] = round(reward / risk, 2) if risk > 0 else 0
                
                self.last_signal = 'SELL'
                self.last_signal_time = current_data.get('time')
        
        # HOLD: No trend change
        else:
            if current_trend == 'up':
                signal_data['reason'] = '⬆️ Uptrend continues (HOLD LONG)'
                signal_data['action'] = 'HOLD_LONG'
            else:
                signal_data['reason'] = '⬇️ Downtrend continues (HOLD SHORT)'
                signal_data['action'] = 'HOLD_SHORT'
        
        # Store current trend for next comparison
        self.last_signal_trend = current_trend
        
        return signal_data
    
    def generate_signal_from_json_data(self, current: Dict, previous: Dict) -> Dict:
        """
        Convenience method to generate signal from your JSON format
        
        Args:
            current: Current candle data from your JSON
            previous: Previous candle data from your JSON
        
        Returns:
            Signal information
        """
        return self.generate_signal(current, previous)
    
    def print_signal(self, signal_data: Dict):
        """Print formatted signal information"""
        print("\n" + "="*70)
        print("🎯 SUPERTREND SIGNAL")
        print("="*70)
        
        # Format timestamp
        from datetime import datetime
        if signal_data.get('timestamp'):
            dt = datetime.fromtimestamp(signal_data['timestamp'])
            print(f"⏰ Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"💰 Close Price: ${signal_data.get('close', 0):.2f}")
        print(f"📊 Supertrend: ${signal_data.get('supertrend', 0):.2f}")
        print(f"📈 Trend: {signal_data.get('current_trend', 'N/A').upper()}")
        
        if signal_data.get('previous_trend'):
            print(f"📉 Previous Trend: {signal_data['previous_trend'].upper()}")
        
        print("\n" + "-"*70)
        
        signal = signal_data.get('signal', 'HOLD')
        
        if signal == 'BUY':
            print(f"🚀 SIGNAL: {signal} (LONG)")
            print(f"✅ Action: {signal_data.get('action', 'N/A')}")
            print(f"💡 Reason: {signal_data.get('reason', 'N/A')}")
            print(f"\n📍 Entry: ${signal_data.get('entry_price', 0):.2f}")
            print(f"🛑 Stop Loss: ${signal_data.get('stop_loss', 0):.2f}")
            print(f"🎯 Take Profit: ${signal_data.get('take_profit', 0):.2f}")
            print(f"⚖️  Risk/Reward: 1:{signal_data.get('risk_reward_ratio', 0)}")
            
        elif signal == 'SELL':
            print(f"📉 SIGNAL: {signal} (SHORT)")
            print(f"✅ Action: {signal_data.get('action', 'N/A')}")
            print(f"💡 Reason: {signal_data.get('reason', 'N/A')}")
            print(f"\n📍 Entry: ${signal_data.get('entry_price', 0):.2f}")
            print(f"🛑 Stop Loss: ${signal_data.get('stop_loss', 0):.2f}")
            print(f"🎯 Take Profit: ${signal_data.get('take_profit', 0):.2f}")
            print(f"⚖️  Risk/Reward: 1:{signal_data.get('risk_reward_ratio', 0)}")
            
        else:
            print(f"⏸️  SIGNAL: {signal}")
            print(f"💡 Reason: {signal_data.get('reason', 'N/A')}")
        
        print("="*70 + "\n")


# ==================== Example Usage ====================

def example_signal_generation():
    """Example: Generate signal from your existing Supertrend data"""
    
    # Your current candle data (latest)
    current_candle = {
        "time": 1766755800,
        "open": 88749.5,
        "high": 88781.0,
        "low": 88735.5,
        "close": 88764.5,
        "atr": 114.55,
        "basic_upper": 89101.9,
        "basic_lower": 88414.6,
        "final_upper": 88912.95,
        "final_lower": 88414.6,
        "supertrend": 88912.95,
        "trend": "down"
    }
    
    # Previous candle data
    previous_candle = {
        "time": 1766755500,  # 5 minutes earlier
        "trend": "down"  # Same trend = HOLD
    }
    
    # Initialize signal generator
    signal_gen = SupertrendSignalGenerator(period=10, multiplier=3.0)
    
    # Generate signal
    signal = signal_gen.generate_signal_from_json_data(current_candle, previous_candle)
    
    # Print signal
    signal_gen.print_signal(signal)
    
    return signal


def example_incremental_update():
    """Example: Update Supertrend incrementally with new candles"""
    
    from utils.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    signal_gen = SupertrendSignalGenerator(period=10, multiplier=3.0)
    
    print("Fetching historical data...")
    
    # Get historical data
    df = fetcher.get_recent_candles('BTCUSD', '15m', hours_back=24)
    
    if df.empty:
        print("No data available")
        return
    
    # Convert to list format
    historical_data = []
    for idx, row in df.iterrows():
        historical_data.append([
            int(idx.timestamp()),
            float(row['open']),
            float(row['high']),
            float(row['low']),
            float(row['close']),
            float(row['volume'])
        ])
    
    print(f"Initializing with {len(historical_data)} candles...")
    
    # Initialize state with all but last candle
    previous_data = signal_gen.initialize_from_history(historical_data[:-1])
    
    # Update with latest candle
    print("\nUpdating with latest candle...")
    current_data = signal_gen.update_with_new_candle(historical_data[-1])
    
    # Generate signal
    signal = signal_gen.generate_signal(current_data, previous_data)
    
    # Print signal
    signal_gen.print_signal(signal)
    
    return signal


if __name__ == "__main__":
    print("="*70)
    print("SUPERTREND SIGNAL GENERATOR - Examples")
    print("="*70)
    
    # Example 1: Generate signal from existing data
    print("\n📊 Example 1: Signal from existing Supertrend data\n")
    example_signal_generation()
    
    print("\n" + "="*70 + "\n")
    
    # Example 2: Incremental update with live data
    print("\n📊 Example 2: Incremental update with live data\n")
    try:
        example_incremental_update()
    except Exception as e:
        print(f"Error: {e}")