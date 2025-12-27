import json
from pathlib import Path

from utils.data_fetcher import DataFetcher

fetcher=DataFetcher()
    
class SupertrendBacktest:
    """
    Supertrend trend-flip backtest engine
    """

    def __init__(self, data_file: str = "supertrend.json"):
        self.data_file = data_file
        self.data = []
        self.trades = []

    def load_data(self):
        """Load Supertrend JSON data"""
        file_path = Path(__file__).parent.parent / self.data_file

        with open(file_path, "r") as f:
            self.data = json.load(f)

    def supertrend_signal_flip_bt(self):
        """Run backtest and calculate PnL"""
        if not self.data:
            raise ValueError("Data not loaded. Call load_data() first.")

        position = None        # "long" | "short" | None
        entry_price = None
        entry_time = None

        for i in range(len(self.data) - 1):
            curr = self.data[i]
            nxt = self.data[i + 1]

            # Trend flip detected
            if curr["trend"] != nxt["trend"]:

                # EXIT existing position
                if position is not None:
                    exit_price = nxt["close"]

                    pnl = (
                        exit_price - entry_price
                        if position == "long"
                        else entry_price - exit_price
                    )

                    self.trades.append({
                        "entry_time": entry_time,
                        "exit_time": nxt["time"],
                        "side": position,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": round(pnl, 5)
                    })

                    position = None
                    entry_price = None
                    entry_time = None

                # ENTER new position
                position = "long" if nxt["trend"] == "up" else "short"
                entry_price = nxt["close"]
                entry_time = nxt["time"]

    def summary(self):
        """Print backtest summary"""
        if not self.trades:
            print("No trades executed.")
            return

        total_pnl = sum(t["pnl"] for t in self.trades)
        wins = [t for t in self.trades if t["pnl"] > 0]
        losses = [t for t in self.trades if t["pnl"] <= 0]

        print("\n📊 BACKTEST SUMMARY")
        print("=" * 40)
        print(f"Total Trades : {len(self.trades)}")
        print(f"Winning Trades : {len(wins)}")
        print(f"Losing Trades  : {len(losses)}")
        print(f"Win Rate       : {round(len(wins) / len(self.trades) * 100, 2)}%")
        print(f"Total PnL      : {round(total_pnl, 5)}")

    def get_trades(self):
        """Return trades list"""
        return self.trades

    def extract_local_maxima_local_minima_trend_range(self):
        """
        Extract AFE & MAE per Supertrend trade (LONG + SHORT)
        """
        supertrend_data=self.data
        trades = []

        for i in range(len(supertrend_data) - 1):
            curr = supertrend_data[i]
            nxt = supertrend_data[i + 1]

            # ---------- LONG ----------
            if curr["trend"] == "down" and nxt["trend"] == "up":
                entry = nxt["close"]
                entry_time = nxt["time"]

                max_high = entry
                min_low = entry
                candles = 0

                j = i + 1
                while j < len(supertrend_data) and supertrend_data[j]["trend"] == "up":
                    max_high = max(max_high, supertrend_data[j]["high"])
                    min_low = min(min_low, supertrend_data[j]["low"])
                    candles += 1
                    j += 1
                
                exit_price = supertrend_data[j]["close"] if j < len(supertrend_data) else supertrend_data[-1]["close"]
                exit_time = supertrend_data[j]["time"] if j < len(supertrend_data) else supertrend_data[-1]["time"]

                trades.append({
                    "side": "long",
                    "entry_time": entry_time,
                    "entry": entry,
                    "afe": round((max_high - entry) / entry * 100, 2),
                    "mae": round((entry - min_low) / entry * 100, 2),
                    "exit":exit_price,
                    "exit_time":exit_time,
                    "max_high_in_range":max_high,
                    "min_low_in_range":min_low,
                    "candles": candles
                })

            # ---------- SHORT ----------
            elif curr["trend"] == "up" and nxt["trend"] == "down":
                entry = nxt["close"]
                entry_time = nxt["time"]

                min_low = entry
                max_high = entry
                candles = 0

                j = i + 1
                while j < len(supertrend_data) and supertrend_data[j]["trend"] == "down":
                    min_low = min(min_low, supertrend_data[j]["low"])
                    max_high = max(max_high, supertrend_data[j]["high"])
                    candles += 1
                    j += 1

                exit_price = supertrend_data[j]["close"] if j < len(supertrend_data) else supertrend_data[-1]["close"]
                exit_time = supertrend_data[j]["time"] if j < len(supertrend_data) else supertrend_data[-1]["time"]
                trades.append({
                    "side": "short",
                    "entry_time": entry_time,
                    "entry": entry,
                    "afe": round((entry - min_low) / entry * 100, 2),
                    "mae": round((max_high - entry) / entry * 100, 2),
                    "max_high_in_range":max_high,
                    "exit":exit_price,
                    "exit_time":exit_time,
                    "min_low_in_range":min_low,
                    "candles": candles
                })

        return trades
# ---- CLI runner ----
    def backtest_sl_target(self, sl_pct=12, target_pct=3):
        supertrend_data=self.data
        trades = []

        position = None
        entry = None
        entry_time = None
        side = None

        for i in range(len(supertrend_data) - 1):
            curr = supertrend_data[i]
            nxt = supertrend_data[i + 1]

            # ---------------- ENTRY ----------------
            if position is None:
                if curr["trend"] == "down" and nxt["trend"] == "up":
                    position = "long"
                elif curr["trend"] == "up" and nxt["trend"] == "down":
                    position = "short"
                else:
                    continue

                entry = nxt["close"]
                entry_time = nxt["time"]
                side = position
                continue

            # ---------------- MANAGE OPEN TRADE ----------------
            high = curr["high"]
            low = curr["low"]

            exit_price = None
            exit_reason = None

            if side == "long":
                stop = entry * (1 - sl_pct / 100)
                target = entry * (1 + target_pct / 100)

                if low <= stop:
                    exit_price = stop
                    exit_reason = "SL"
                elif high >= target:
                    exit_price = target
                    exit_reason = "TARGET"

            else:  # SHORT
                stop = entry * (1 + sl_pct / 100)
                target = entry * (1 - target_pct / 100)

                if high >= stop:
                    exit_price = stop
                    exit_reason = "SL"
                elif low <= target:
                    exit_price = target
                    exit_reason = "TARGET"

            # ---------------- EXIT ----------------
            if exit_price is not None:
                pnl = (
                    exit_price - entry
                    if side == "long"
                    else entry - exit_price
                )

                trades.append({
                    "side": side,
                    "entry_time": entry_time,
                    "exit_time": curr["time"],
                    "entry": round(entry, 5),
                    "exit": round(exit_price, 5),
                    "pnl_pct": round(pnl / entry * 100, 2),
                    "exit_reason": exit_reason
                })

                position = None
                entry = None
                side = None

            # Exit on trend flip (if SL/Target not hit)
            elif (
                (side == "long" and curr["trend"] == "up" and nxt["trend"] == "down") or
                (side == "short" and curr["trend"] == "down" and nxt["trend"] == "up")
            ):
                exit_price = nxt["close"]
                pnl = (
                    exit_price - entry
                    if side == "long"
                    else entry - exit_price
                )

                trades.append({
                    "side": side,
                    "entry_time": entry_time,
                    "exit_time": nxt["time"],
                    "entry": round(entry, 5),
                    "exit": round(exit_price, 5),
                    "pnl_pct": round(pnl / entry * 100, 2),
                    "exit_reason": "TREND_FLIP"
                })

                position = None
                entry = None
                side = None

        return trades
    def backtest_inverse_supertrend(self, sl_pct=2, target_pct=3):
        assert sl_pct > 0, "sl_pct must be positive"
        assert target_pct > 0, "target_pct must be positive"

        supertrend_data = self.data
        trades = []

        position = None
        entry = None
        entry_time = None
        side = None

        for i in range(len(supertrend_data) - 1):
            curr = supertrend_data[i]
            nxt = supertrend_data[i + 1]

            # ---------------- ENTRY (INVERTED) ----------------
            if position is None:
                if curr["trend"] == "down" and nxt["trend"] == "up":
                    position = "short"   # INVERT BUY → SELL
                elif curr["trend"] == "up" and nxt["trend"] == "down":
                    position = "long"    # INVERT SELL → BUY
                else:
                    continue

                entry = nxt["close"]
                entry_time = nxt["time"]
                side = position
                continue

            # ---------------- MANAGE OPEN TRADE ----------------
            high = curr["high"]
            low = curr["low"]

            exit_price = None
            exit_reason = None

            if side == "long":
                stop = entry * (1 - sl_pct / 100)
                target = entry * (1 + target_pct / 100)

                if low <= stop:
                    exit_price = stop
                    exit_reason = "SL"
                elif high >= target:
                    exit_price = target
                    exit_reason = "TARGET"

            else:  # SHORT
                stop = entry * (1 + sl_pct / 100)
                target = entry * (1 - target_pct / 100)

                if high >= stop:
                    exit_price = stop
                    exit_reason = "SL"
                elif low <= target:
                    exit_price = target
                    exit_reason = "TARGET"

            # ---------------- EXIT ----------------
            if exit_price is not None:
                pnl = (
                    exit_price - entry
                    if side == "long"
                    else entry - exit_price
                )

                trades.append({
                    "side": side,
                    "entry_time": entry_time,
                    "exit_time": curr["time"],
                    "entry": round(entry, 5),
                    "exit": round(exit_price, 5),
                    "pnl_pct": round(pnl / entry * 100, 2),
                    "exit_reason": exit_reason
                })

                position = None
                entry = None
                side = None

            # Exit on ORIGINAL trend flip (not inverted)
            elif (
                (side == "long" and curr["trend"] == "up" and nxt["trend"] == "down") or
                (side == "short" and curr["trend"] == "down" and nxt["trend"] == "up")
            ):
                exit_price = nxt["close"]
                pnl = (
                    exit_price - entry
                    if side == "long"
                    else entry - exit_price
                )

                trades.append({
                    "side": side,
                    "entry_time": entry_time,
                    "exit_time": nxt["time"],
                    "entry": round(entry, 5),
                    "exit": round(exit_price, 5),
                    "pnl_pct": round(pnl / entry * 100, 2),
                    "exit_reason": "TREND_FLIP"
                })

                position = None
                entry = None
                side = None

        return trades

    def returns_supertrend(self):
        data=self.extract_local_maxima_local_minima_trend_range()
        data2=self.backtest_sl_target()
        data3=self.backtest_inverse_supertrend()
        capital=5000
        capital2=5000
        capital3=5000
        res,res2=0,0
        total_pnl=0.0
        for i in data:
             res =res+capital *( i["afe"] / 100)
        afe_values = sorted(t["afe"] for t in data)

        for trade in data2:
            trade_pnl = 5000 * (trade["pnl_pct"] / 100)
            # print(trade_pnl)
            # total_pnl += trade_pnl
        for trade in data3:
            trade_pnl = 5000 * (trade["pnl_pct"] / 100)
            print(trade_pnl)
            total_pnl += trade_pnl

        print("Max AFE:", max(afe_values))
        print("95th percentile AFE:", afe_values[int(len(afe_values)*0.95)])
        print("Median AFE:", afe_values[len(afe_values)//2])

        return total_pnl



if __name__ == "__main__":
    bt = SupertrendBacktest()
    bt.load_data()
    bt.supertrend_signal_flip_bt()
    bt.summary()
    lmlm_data=bt.extract_local_maxima_local_minima_trend_range()
    sl_target_data=bt.backtest_sl_target()
    fetcher.export_to_json(sl_target_data,"supertrend_backtest_sl_target.json")
    
    # print(lmlm_data[:5])
    fetcher.export_to_json(lmlm_data,"supertrend_backtest_afe_mae.json")
    data=bt.get_trades()
    print(bt.returns_supertrend())
    # print(data)
    fetcher.export_to_json(data,"supertrend_backtest.json")