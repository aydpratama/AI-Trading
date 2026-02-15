"""
Smart Auto Scanner — Background signal scanner with Telegram notifications.

Scans on H1 candle close during active market hours.
Filters: confidence >= 80%, R:R >= 2, max 5 signals/day/pair, anti-duplicate.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class SmartScanner:
    """Background scanner that monitors markets and sends Telegram alerts."""

    SCAN_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    TIMEFRAME = "H1"
    MIN_CONFIDENCE = 80
    MIN_RR = 2.0
    MAX_SIGNALS_PER_DAY = 5  # per pair
    SCAN_INTERVAL_MINUTES = 60  # aligned to H1 candle close

    # Active market hours (WIB / UTC+7)
    # London: 14:00-23:00 WIB  |  NY: 19:00-04:00 WIB
    ACTIVE_HOURS_START = 14  # 14:00 WIB (London open)
    ACTIVE_HOURS_END = 4     # 04:00 WIB next day (NY close)

    def __init__(self):
        self.running = False
        self._task = None
        self._sent_signals: Dict[str, Set[str]] = defaultdict(set)  # date -> set of signal keys
        self._daily_count: Dict[str, Dict[str, int]] = {}  # date -> {pair: count}
        self._last_scan_date: str = ""

    def _is_market_active(self) -> bool:
        """Check if current time is within active trading hours (WIB)."""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0=Monday ... 6=Sunday

        # No trading on weekends
        if weekday >= 5:
            return False

        # Active: 14:00 - 23:59 OR 00:00 - 04:00
        if self.ACTIVE_HOURS_START <= hour <= 23:
            return True
        if 0 <= hour < self.ACTIVE_HOURS_END:
            return True

        return False

    def _get_signal_key(self, symbol: str, direction: str, entry: float) -> str:
        """Create a unique key for a signal to prevent duplicates."""
        # Round entry to prevent tiny price differences from being treated as different signals
        entry_rounded = round(entry, 3)
        return f"{symbol}_{direction}_{entry_rounded}"

    def _is_duplicate(self, signal_key: str) -> bool:
        """Check if this signal was already sent today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return signal_key in self._sent_signals[today]

    def _can_send_more(self, symbol: str) -> bool:
        """Check if we haven't exceeded daily signal limit for this pair."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self._daily_count:
            self._daily_count[today] = defaultdict(int)
        return self._daily_count[today][symbol] < self.MAX_SIGNALS_PER_DAY

    def _record_signal(self, symbol: str, signal_key: str):
        """Record that a signal was sent."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._sent_signals[today].add(signal_key)
        if today not in self._daily_count:
            self._daily_count[today] = defaultdict(int)
        self._daily_count[today][symbol] += 1

    def _cleanup_old_data(self):
        """Remove data older than yesterday to prevent memory leak."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        keys_to_remove = [
            k for k in self._sent_signals.keys()
            if k != today and k != yesterday
        ]
        for k in keys_to_remove:
            del self._sent_signals[k]
            if k in self._daily_count:
                del self._daily_count[k]

    async def _scan_once(self):
        """Perform a single scan of all pairs."""
        from ai.genius_ai import genius_ai
        from notification.telegram import telegram_notifier
        from mt5.connector import connector

        if not connector.is_connected():
            logger.warning("[Scanner] MT5 not connected, skipping scan")
            return

        if not telegram_notifier.enabled:
            return  # No point scanning if Telegram isn't configured

        if not self._is_market_active():
            logger.debug("[Scanner] Market not active, skipping")
            return

        self._cleanup_old_data()
        now = datetime.now()
        logger.info(f"[Scanner] Scanning {len(self.SCAN_PAIRS)} pairs at {now.strftime('%H:%M')}")

        signals_found = 0

        for symbol in self.SCAN_PAIRS:
            try:
                if not self._can_send_more(symbol):
                    logger.debug(f"[Scanner] Daily limit reached for {symbol}")
                    continue

                analysis = genius_ai.analyze(symbol, self.TIMEFRAME, "moderate")

                if not analysis or not analysis.get("signal"):
                    continue

                signal = analysis["signal"]
                setup = analysis.get("setup", {})
                confidence = signal.get("confidence", 0)
                direction = signal.get("direction", "")
                entry = setup.get("entry", 0)
                sl = setup.get("stop_loss", 0)
                tp = setup.get("take_profit", 0)
                rr = setup.get("risk_reward", 0)
                lot_size = setup.get("lot_size", 0)
                reasons = signal.get("reasons", [])

                # Filter: confidence
                if confidence < self.MIN_CONFIDENCE:
                    continue

                # Filter: R:R
                if rr < self.MIN_RR:
                    continue

                # Filter: duplicate
                signal_key = self._get_signal_key(symbol, direction, entry)
                if self._is_duplicate(signal_key):
                    continue

                # Send notification
                notif_data = {
                    "symbol": symbol,
                    "direction": direction,
                    "confidence": confidence,
                    "entry": entry,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "lot_size": lot_size,
                    "risk_reward": rr,
                    "reasons": reasons,
                    "auto_scan": True
                }

                result = await telegram_notifier.send_signal(notif_data)
                if result.get("ok"):
                    self._record_signal(symbol, signal_key)
                    signals_found += 1
                    logger.info(f"[Scanner] Signal sent: {direction} {symbol} (conf: {confidence}%)")

            except Exception as e:
                logger.error(f"[Scanner] Error scanning {symbol}: {e}")
                continue

        if signals_found > 0:
            logger.info(f"[Scanner] Scan complete: {signals_found} signal(s) sent")

    async def _run_loop(self):
        """Main scanner loop — runs every SCAN_INTERVAL_MINUTES."""
        logger.info(f"[Scanner] Started — scanning every {self.SCAN_INTERVAL_MINUTES} min")
        logger.info(f"[Scanner] Pairs: {', '.join(self.SCAN_PAIRS)}")
        logger.info(f"[Scanner] Filters: confidence >= {self.MIN_CONFIDENCE}%, R:R >= {self.MIN_RR}")
        logger.info(f"[Scanner] Active hours: {self.ACTIVE_HOURS_START}:00 - {self.ACTIVE_HOURS_END}:00 WIB")

        # Wait a bit on startup to let everything initialize
        await asyncio.sleep(10)

        while self.running:
            try:
                await self._scan_once()
            except Exception as e:
                logger.error(f"[Scanner] Error in scan loop: {e}")

            # Sleep until next scan
            await asyncio.sleep(self.SCAN_INTERVAL_MINUTES * 60)

    def start(self):
        """Start the background scanner."""
        if self.running:
            return

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("[Scanner] Background scanner started")

    def stop(self):
        """Stop the background scanner."""
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[Scanner] Background scanner stopped")

    def get_status(self) -> dict:
        """Get current scanner status."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self._daily_count.get(today, {})
        total_today = sum(daily.values())

        return {
            "running": self.running,
            "market_active": self._is_market_active(),
            "scan_interval_min": self.SCAN_INTERVAL_MINUTES,
            "pairs": self.SCAN_PAIRS,
            "min_confidence": self.MIN_CONFIDENCE,
            "min_rr": self.MIN_RR,
            "signals_today": total_today,
            "signals_by_pair": dict(daily),
            "active_hours": f"{self.ACTIVE_HOURS_START}:00 - {self.ACTIVE_HOURS_END}:00 WIB"
        }


# Singleton
auto_scanner = SmartScanner()
