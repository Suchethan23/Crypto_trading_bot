import requests
from datetime import datetime


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, message: str):
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            requests.post(self.base_url, data=payload, timeout=5)
        except Exception as e:
            print("❌ Telegram error:", e)

    def trade_entry(self, symbol, side, entry, stoploss, timeframe="1H"):
        msg = (
            f"🚨 <b>NEW TRADE</b>\n\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Side:</b> {side.upper()}\n"
            f"<b>Entry:</b> {entry:.2f}\n"
            f"<b>Stop Loss (ST):</b> {stoploss:.2f}\n"
            f"<b>Timeframe:</b> {timeframe}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send(msg)

    def trade_exit(self, symbol, side, entry, exit_price, reason):
        pnl_pct = (
            (exit_price - entry) / entry * 100
            if side == "long"
            else (entry - exit_price) / entry * 100
        )

        msg = (
            f"❌ <b>TRADE CLOSED</b>\n\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Side:</b> {side.upper()}\n"
            f"<b>Entry:</b> {entry:.2f}\n"
            f"<b>Exit:</b> {exit_price:.2f}\n"
            f"<b>PnL:</b> {pnl_pct:.2f}%\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send(msg)

    def info(self, message: str):
        self.send(f"ℹ️ {message}")

    def error(self, message: str):
        self.send(f"❌ <b>ERROR</b>\n{message}")
