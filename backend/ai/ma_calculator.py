"""Moving Average Calculator"""
import numpy as np
from typing import List, Dict, Any


class MACalculator:
    """Calculates Moving Average indicators"""

    def __init__(self, ema_9: int = 9, ema_21: int = 21, ema_50: int = 50):
        self.ema_9 = ema_9
        self.ema_21 = ema_21
        self.ema_50 = ema_50

    def calculate(self, candles: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Calculate EMAs from candles
        Returns dict with ema_9, ema_21, ema_50 values
        """
        closes = [candle["close"] for candle in candles]

        ema_9 = self._calculate_ema(closes, self.ema_9)
        ema_21 = self._calculate_ema(closes, self.ema_21)
        ema_50 = self._calculate_ema(closes, self.ema_50)

        # Pad with zeros
        pad_length = len(candles) - len(ema_9)
        ema_9 = [0.0] * pad_length + ema_9
        ema_21 = [0.0] * pad_length + ema_21
        ema_50 = [0.0] * pad_length + ema_50

        return {
            "ema_9": ema_9,
            "ema_21": ema_21,
            "ema_50": ema_50
        }

    def get_current_ma(self, candles: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get current MA values"""
        result = self.calculate(candles)
        return {
            "ema_9": result["ema_9"][-1] if result["ema_9"] else 0.0,
            "ema_21": result["ema_21"][-1] if result["ema_21"] else 0.0,
            "ema_50": result["ema_50"][-1] if result["ema_50"] else 0.0
        }

    def get_ma_status(self, ema_9: float, ema_21: float, ema_50: float) -> str:
        """Get MA status"""
        if ema_9 > ema_21 > ema_50:
            return "BULLISH"
        elif ema_9 < ema_21 < ema_50:
            return "BEARISH"
        elif ema_9 > ema_21:
            return "BULLISH_CROSS"
        elif ema_9 < ema_21:
            return "BEARISH_CROSS"
        else:
            return "NEUTRAL"

    def is_crossover(self, ema_9: float, ema_21: float, threshold: float = 0.00001) -> str:
        """
        Check for EMA crossover
        Returns 'BULLISH', 'BEARISH', or None
        """
        if ema_9 > ema_21 + threshold:
            return "BULLISH"
        elif ema_9 < ema_21 - threshold:
            return "BEARISH"
        return None

    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return [0.0] * len(data)

        ema = [0.0] * period
        multiplier = 2 / (period + 1)

        # Calculate SMA for first period
        sma = sum(data[:period]) / period
        ema[period - 1] = sma

        # Calculate subsequent EMAs
        for i in range(period, len(data)):
            ema.append((data[i] - ema[i - 1]) * multiplier + ema[i - 1])

        return ema


# Singleton instance
ma_calculator = MACalculator()
