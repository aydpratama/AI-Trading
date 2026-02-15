"""Telegram & Scanner API Routes"""
from fastapi import APIRouter, Query
from notification.telegram import telegram_notifier
from ai.auto_scanner import auto_scanner
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/test")
async def test_telegram(
    bot_token: str = Query(...),
    chat_id: str = Query(...)
):
    """Test Telegram bot connection and send a test message."""
    result = await telegram_notifier.test_connection(bot_token, chat_id)
    return result


@router.post("/configure")
async def configure_telegram(
    bot_token: str = Query(...),
    chat_id: str = Query(...)
):
    """Configure Telegram and start auto scanner."""
    telegram_notifier.configure(bot_token, chat_id)

    # Auto-start scanner when Telegram is configured
    if telegram_notifier.enabled and not auto_scanner.running:
        auto_scanner.start()
        logger.info("Auto scanner started via UI configuration")

    return {
        "success": True,
        "message": "Telegram configured, scanner started",
        "telegram_enabled": telegram_notifier.enabled,
        "scanner_running": auto_scanner.running
    }


@router.get("/status")
async def telegram_status():
    """Get Telegram + Scanner status"""
    scanner_status = auto_scanner.get_status()
    return {
        "telegram_enabled": telegram_notifier.enabled,
        "scanner": scanner_status
    }


@router.post("/scanner/start")
async def start_scanner():
    """Manually start the auto scanner"""
    if not telegram_notifier.enabled:
        return {"success": False, "message": "Telegram belum dikonfigurasi"}
    if auto_scanner.running:
        return {"success": True, "message": "Scanner sudah berjalan", "status": auto_scanner.get_status()}

    auto_scanner.start()
    return {"success": True, "message": "Scanner dimulai", "status": auto_scanner.get_status()}


@router.post("/scanner/stop")
async def stop_scanner():
    """Stop the auto scanner"""
    auto_scanner.stop()
    return {"success": True, "message": "Scanner dihentikan"}


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
