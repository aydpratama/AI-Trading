"""Telegram Notification Manager - Lightweight using httpx"""
import httpx
import logging
from typing import Dict, Any, Optional
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
            logger.info("📱 Telegram notifier configured successfully")

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
                # 1. Verify bot token by calling getMe
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

                # 2. Send test message
                test_msg = (
                    "🤖 <b>NexusTrade Bot Connected!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Bot: @{bot_username}\n"
                    f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "Anda akan menerima notifikasi:\n"
                    "• 📊 Signal trading baru\n"
                    "• 📈 Update posisi\n"
                    "• ✅ Trade ditutup\n"
                    "• ⚠️ Alert risiko\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "<i>NexusTrade AI Trading Platform</i>"
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
                        "message": f"Gagal mengirim pesan: {send_result.get('description', 'Chat ID salah atau bot belum di-start')}"
                    }

        except httpx.ConnectError:
            return {"success": False, "message": "Tidak bisa terhubung ke Telegram API. Periksa koneksi internet."}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    # ========================
    # Notification Methods
    # ========================

    async def send_signal(self, signal: Dict[str, Any]) -> dict:
        """Send new signal notification"""
        direction = signal.get("direction", "UNKNOWN")
        symbol = signal.get("symbol", "???")
        confidence = signal.get("confidence", 0)
        entry = signal.get("entry", 0)
        sl = signal.get("stop_loss", signal.get("sl", 0))
        tp = signal.get("take_profit", signal.get("tp", 0))
        lot_size = signal.get("lot_size", 0)
        rr = signal.get("risk_reward", 0)
        reasons = signal.get("reasons", [])

        emoji = "🟢" if direction == "BUY" else "🔴"
        conf_bar = self._progress_bar(confidence)

        # Format prices based on symbol
        decimals = 2 if "XAU" in symbol or "XAG" in symbol else 3 if "JPY" in symbol else 5

        message = (
            f"📊 <b>SIGNAL — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{emoji} <b>{direction}</b>  |  Confidence: <b>{confidence:.0f}%</b>\n"
            f"{conf_bar}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 Entry: <code>{entry:.{decimals}f}</code>\n"
            f"🛡 SL: <code>{sl:.{decimals}f}</code>\n"
            f"🎯 TP: <code>{tp:.{decimals}f}</code>\n"
            f"📐 R:R = <b>1:{rr:.1f}</b>\n"
            f"📦 Lot: <b>{lot_size}</b>\n"
        )

        if reasons:
            message += f"━━━━━━━━━━━━━━━━━━━━\n💡 <b>Reasons:</b>\n"
            for r in reasons[:5]:
                message += f"  • {r}\n"

        message += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  <i>NexusTrade</i>"
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

        emoji = "🟢" if direction in ("BUY", "buy", 0) else "🔴"
        decimals = 2 if "XAU" in symbol else 3 if "JPY" in symbol else 5

        message = (
            f"📈 <b>TRADE OPENED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{emoji} {symbol} — <b>{direction}</b>\n"
            f"🎫 Ticket: <code>{ticket}</code>\n"
            f"📦 Volume: <b>{volume}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 Entry: <code>{entry:.{decimals}f}</code>\n"
            f"🛡 SL: <code>{sl:.{decimals}f}</code>\n"
            f"🎯 TP: <code>{tp:.{decimals}f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  <i>NexusTrade</i>"
        )

        return await self._send_message(message)

    async def send_trade_closed(self, trade: Dict[str, Any]) -> dict:
        """Send trade closed notification"""
        symbol = trade.get("symbol", "???")
        ticket = trade.get("ticket", 0)
        pnl = trade.get("profit", trade.get("pnl", 0))
        direction = trade.get("direction", trade.get("type", "UNKNOWN"))

        pnl_emoji = "💰" if pnl >= 0 else "💸"
        pnl_text = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        message = (
            f"✅ <b>TRADE CLOSED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{'🟢' if direction in ('BUY', 'buy', 0) else '🔴'} {symbol} — {direction}\n"
            f"🎫 Ticket: <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pnl_emoji} PnL: <b>{pnl_text}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  <i>NexusTrade</i>"
        )

        return await self._send_message(message)

    async def send_risk_alert(self, alert_type: str, details: str) -> dict:
        """Send risk alert notification"""
        emoji_map = {
            "MAX_DAILY_LOSS": "🚨",
            "MAX_DRAWDOWN": "🚨",
            "MAX_POSITION": "⚠️",
            "LOW_MARGIN": "⚠️",
        }
        emoji = emoji_map.get(alert_type, "⚠️")

        message = (
            f"{emoji} <b>RISK ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Type: <b>{alert_type}</b>\n"
            f"{details}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  <i>NexusTrade</i>"
        )

        return await self._send_message(message)

    def _progress_bar(self, value: float, total: float = 100, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int(value / total * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {value:.0f}%"


# Singleton instance
telegram_notifier = TelegramNotifier()
