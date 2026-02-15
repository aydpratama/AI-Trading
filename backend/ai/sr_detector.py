"""Support/Resistance Detector"""
from typing import List, Dict, Any, Tuple
import numpy as np


class SRDetector:
    """Detects support and resistance levels"""

    def __init__(self, levels_count: int = 5, refresh_rate: int = 50):
        self.levels_count = levels_count
        self.refresh_rate = refresh_rate

    def detect(self, candles: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Detect support and resistance levels
        Returns dict with resistance and support levels
        """
        if len(candles) < 100:
            return {
                "resistance": [],
                "support": []
            }

        # Get recent high and low
        recent_candles = candles[-self.refresh_rate:]

        highs = [candle["high"] for candle in recent_candles]
        lows = [candle["low"] for candle in recent_candles]

        # Find resistance levels (local highs)
        resistance_levels = self._find_levels(highs, direction="resistance")

        # Find support levels (local lows)
        support_levels = self._find_levels(lows, direction="support")

        return {
            "resistance": resistance_levels,
            "support": support_levels
        }

    def _find_levels(self, prices: List[float], direction: str) -> List[float]:
        """Find local high/low levels"""
        levels = []
        threshold = float(np.std(prices) * 0.5)  # Convert to Python float

        # Simple peak detection
        for i in range(1, len(prices) - 1):
            prev = prices[i - 1]
            curr = prices[i]
            next_ = prices[i + 1]

            if direction == "resistance":
                # Local high
                if curr > prev and curr > next_ and curr - prev > threshold:
                    levels.append(curr)
            else:
                # Local low
                if curr < prev and curr < next_ and prev - curr > threshold:
                    levels.append(curr)

        # Sort and take top levels
        levels = sorted(levels, reverse=True) if direction == "resistance" else sorted(levels)
        return levels[:self.levels_count]

    def find_nearest_level(self, price: float, levels: List[float], direction: str) -> float:
        """Find nearest support or resistance level"""
        if not levels:
            return None

        if direction == "support":
            # Find level below price
            return min([level for level in levels if level < price], default=None)
        else:
            # Find level above price
            return max([level for level in levels if level > price], default=None)

    def get_levels_for_entry(self, candles: List[Dict[str, Any]], price: float) -> Dict[str, float]:
        """
        Get support and resistance levels for entry
        Returns dict with resistance_1, resistance_2, support_1, support_2
        """
        sr_levels = self.detect(candles)

        resistance_1 = self.find_nearest_level(price, sr_levels["resistance"], "resistance")
        support_1 = self.find_nearest_level(price, sr_levels["support"], "support")

        # Get second nearest levels
        resistance_2 = sr_levels["resistance"][1] if len(sr_levels["resistance"]) > 1 else None
        support_2 = sr_levels["support"][1] if len(sr_levels["support"]) > 1 else None

        return {
            "resistance_1": resistance_1,
            "resistance_2": resistance_2,
            "support_1": support_1,
            "support_2": support_2
        }


# Singleton instance
sr_detector = SRDetector()
