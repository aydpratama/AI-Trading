"""Telegram Notification Manager — Lightweight using httpx"""
import httpx
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier:
    """Send notifications via Telegram Bot API using httpx"""

    def __init__(self):
        self.bot_token: str = ""
        self.chat_id: str = ""
        self.enabled: bool = False

    def configure(self, bot_token: str, chat_id: str):
        """Configure Telegram credentials at runtime"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        if self.enabled:
            logger.info("Telegram notifier configured")

    def _api_url(self, method: str) -> str:
        return TELEGRAM_API.format(token=self.bot_token, method=method)

    async def _send_message(self, text: str, parse_mode: str = "HTML") -> dict:
        """Send a message via Telegram Bot API"""
        if not self.enabled:
            return {"ok": False, "error": "Telegram not configured"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self._api_url("sendMessage"),
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": True
                    }
                )
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Telegram API error: {result.get('description')}")
                return result
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return {"ok": False, "error": str(e)}

    async def test_connection(self, bot_token: str, chat_id: str) -> dict:
        """Test Telegram connection with given credentials"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                me_response = await client.get(
                    TELEGRAM_API.format(token=bot_token, method="getMe")
                )
                me_result = me_response.json()
                if not me_result.get("ok"):
                    return {
                        "success": False,
                        "message": f"Token tidak valid: {me_result.get('description', 'Unknown error')}"
                    }

                bot_name = me_result["result"].get("first_name", "Bot")
                bot_username = me_result["result"].get("username", "")

                test_msg = (
                    f"<b>TradingAYDP Connected</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Bot: @{bot_username}\n"
                    f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Notifikasi aktif:\n"
                    f"  - Signal trading otomatis\n"
                    f"  - Update posisi\n"
                    f"  - Trade ditutup\n"
                    f"  - Alert risiko\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"<i>TradingAYDP — Smart Auto Scanner</i>"
                )

                send_response = await client.post(
                    TELEGRAM_API.format(token=bot_token, method="sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": test_msg,
                        "parse_mode": "HTML"
                    }
                )
                send_result = send_response.json()

                if send_result.get("ok"):
                    return {
                        "success": True,
                        "message": f"Terhubung ke @{bot_username}! Cek Telegram Anda.",
                        "bot_name": bot_name,
                        "bot_username": bot_username
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Gagal mengirim: {send_result.get('description', 'Chat ID salah atau bot belum di-start')}"
                    }

        except httpx.ConnectError:
            return {"success": False, "message": "Tidak bisa terhubung ke Telegram API. Periksa koneksi internet."}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    # ========================
    # Notification Methods
    # ========================

    async def send_signal(self, signal: Dict[str, Any]) -> dict:
        """Send signal notification — clean visual, minimal icons"""
        direction = signal.get("direction", "UNKNOWN")
        symbol = signal.get("symbol", "???")
        confidence = signal.get("confidence", 0)
        entry = signal.get("entry", signal.get("open_price", 0))
        sl = signal.get("stop_loss", signal.get("sl", 0))
        tp = signal.get("take_profit", signal.get("tp", 0))
        lot_size = signal.get("lot_size", 0)
        rr = signal.get("risk_reward", 0)
        reasons = signal.get("reasons", [])
        is_auto = signal.get("auto_scan", False)

        # Format prices
        dec = 2 if "XAU" in symbol or "XAG" in symbol else 3 if "JPY" in symbol else 5

        # Direction indicator
        dir_label = "BUY (Long)" if direction == "BUY" else "SELL (Short)"

        # Confidence bar
        conf_bar = self._bar(confidence)

        # Source
        source = "Auto Scanner" if is_auto else "Manual Scan"

        message = (
            f"<b>SIGNAL — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Arah: <b>{dir_label}</b>\n"
            f"Confidence: <b>{confidence:.0f}%</b>  {conf_bar}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Entry : <code>{entry:.{dec}f}</code>\n"
            f"SL    : <code>{sl:.{dec}f}</code>\n"
            f"TP    : <code>{tp:.{dec}f}</code>\n"
            f"R:R   : <b>1:{rr:.1f}</b>\n"
            f"Lot   : <b>{lot_size}</b>\n"
        )

        if reasons:
            message += f"━━━━━━━━━━━━━━━━━━━━\n<b>Alasan:</b>\n"
            for r in reasons[:4]:
                # Strip existing emoji from reasons to keep it clean
                clean_r = r.lstrip("✅❌⚠️🟢🔴📊📈📉💡🔥⭐ ")
                message += f"  - {clean_r}\n"

        message += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Ini bukan rekomendasi entry.\n"
            f"Validasi sendiri sebelum trading.</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{datetime.now().strftime('%H:%M')} | {source} | <b>TradingAYDP</b>"
        )

        return await self._send_message(message)

    async def send_trade_opened(self, trade: Dict[str, Any]) -> dict:
        """Send trade opened notification"""
        direction = trade.get("direction", trade.get("type", "UNKNOWN"))
        symbol = trade.get("symbol", "???")
        ticket = trade.get("ticket", 0)
        volume = trade.get("volume", trade.get("lot_size", 0))
        entry = trade.get("entry", trade.get("open_price", 0))
        sl = trade.get("sl", trade.get("stop_loss", 0))
        tp = trade.get("tp", trade.get("take_profit", 0))

        dec = 2 if "XAU" in symbol else 3 if "JPY" in symbol else 5

        message = (
            f"<b>TRADE OPENED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{symbol} — <b>{direction}</b>\n"
            f"Ticket: <code>{ticket}</code>\n"
            f"Volume: <b>{volume}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Entry : <code>{entry:.{dec}f}</code>\n"
            f"SL    : <code>{sl:.{dec}f}</code>\n"
            f"TP    : <code>{tp:.{dec}f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{datetime.now().strftime('%H:%M')} | <b>TradingAYDP</b>"
        )

        return await self._send_message(message)

    async def send_trade_closed(self, trade: Dict[str, Any]) -> dict:
        """Send trade closed notification"""
        symbol = trade.get("symbol", "???")
        ticket = trade.get("ticket", 0)
        pnl = trade.get("profit", trade.get("pnl", 0))
        direction = trade.get("direction", trade.get("type", "UNKNOWN"))

        pnl_text = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        result_label = "WIN" if pnl >= 0 else "LOSS"

        message = (
            f"<b>TRADE CLOSED — {result_label}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{symbol} — {direction}\n"
            f"Ticket: <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"PnL: <b>{pnl_text}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{datetime.now().strftime('%H:%M')} | <b>TradingAYDP</b>"
        )

        return await self._send_message(message)

    async def send_risk_alert(self, alert_type: str, details: str) -> dict:
        """Send risk alert notification"""
        message = (
            f"<b>RISK ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Type: <b>{alert_type}</b>\n"
            f"{details}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{datetime.now().strftime('%H:%M')} | <b>TradingAYDP</b>"
        )

        return await self._send_message(message)

    async def send_scanner_daily_summary(self, stats: dict) -> dict:
        """Send daily summary from the auto scanner"""
        total = stats.get("signals_today", 0)
        by_pair = stats.get("signals_by_pair", {})

        pair_lines = ""
        for pair, count in by_pair.items():
            pair_lines += f"  {pair}: {count} signal(s)\n"

        if not pair_lines:
            pair_lines = "  Tidak ada sinyal hari ini\n"

        message = (
            f"<b>DAILY SUMMARY</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Total sinyal: <b>{total}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pair_lines}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | <b>TradingAYDP</b>"
        )

        return await self._send_message(message)

    def _bar(self, value: float, length: int = 10) -> str:
        """Create a simple text progress bar"""
        filled = int(value / 100 * length)
        return "▓" * filled + "░" * (length - filled)


# Singleton instance
telegram_notifier = TelegramNotifier()
