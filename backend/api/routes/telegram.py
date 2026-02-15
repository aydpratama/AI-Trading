"""Telegram Notification API Routes"""
from fastapi import APIRouter, Query
from typing import Optional
from notification.telegram import telegram_notifier
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/test")
async def test_telegram(
    bot_token: str = Query(...),
    chat_id: str = Query(...)
):
    """
    Test Telegram bot connection and send a test message.
    
    Parameters:
    - bot_token: Telegram Bot Token (from @BotFather)
    - chat_id: Telegram Chat ID (user or group)
    """
    result = await telegram_notifier.test_connection(bot_token, chat_id)
    return result


@router.post("/configure")
async def configure_telegram(
    bot_token: str = Query(...),
    chat_id: str = Query(...)
):
    """
    Configure Telegram credentials for the notifier.
    This enables automatic notifications for signals and trades.
    """
    telegram_notifier.configure(bot_token, chat_id)
    return {
        "success": True,
        "message": "Telegram notifier configured",
        "enabled": telegram_notifier.enabled
    }


@router.get("/status")
async def telegram_status():
    """Check if Telegram notifier is configured and enabled"""
    return {
        "enabled": telegram_notifier.enabled,
        "has_token": bool(telegram_notifier.bot_token),
        "has_chat_id": bool(telegram_notifier.chat_id)
    }


@router.post("/send-signal")
async def send_signal_notification(
    symbol: str = Query(...),
    direction: str = Query(...),
    confidence: float = Query(default=0),
    entry: float = Query(default=0),
    sl: float = Query(default=0),
    tp: float = Query(default=0),
    lot_size: float = Query(default=0.01),
    risk_reward: float = Query(default=0),
):
    """Manually send a signal notification to Telegram"""
    if not telegram_notifier.enabled:
        return {"success": False, "message": "Telegram not configured"}

    signal = {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "entry": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "lot_size": lot_size,
        "risk_reward": risk_reward,
        "reasons": []
    }

    result = await telegram_notifier.send_signal(signal)
    return {"success": result.get("ok", False), "result": result}
