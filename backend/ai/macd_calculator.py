"""MACD (Moving Average Convergence Divergence) Calculator"""
import numpy as np
from typing import List, Dict, Any


class MACDCalculator:
    """Calculates MACD indicator"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def calculate(self, candles: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Calculate MACD from candles
        Returns dict with macd, signal, and histogram values
        """
        if len(candles) < self.slow + 1:
            return {
                "macd": [0.0] * len(candles),
                "signal": [0.0] * len(candles),
                "histogram": [0.0] * len(candles)
            }

        closes = [candle["close"] for candle in candles]

        # Calculate EMAs
        ema_fast = self._calculate_ema(closes, self.fast)
        ema_slow = self._calculate_ema(closes, self.slow)

        # Calculate MACD line
        macd_values = []
        for i in range(len(closes)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_values.append(ema_fast[i] - ema_slow[i])
            else:
                macd_values.append(0.0)

        # Calculate Signal line (EMA of MACD)
        signal_values = self._calculate_ema(macd_values, self.signal)

        # Calculate Histogram
        histogram = []
        for i in range(len(macd_values)):
            if signal_values[i] is not None:
                histogram.append(macd_values[i] - signal_values[i])
            else:
                histogram.append(0.0)

        # Pad with zeros
        pad_length = len(candles) - len(macd_values)
        macd_values = [0.0] * pad_length + macd_values
        signal_values = [0.0] * pad_length + signal_values
        histogram = [0.0] * pad_length + histogram

        return {
            "macd": macd_values,
            "signal": signal_values,
            "histogram": histogram
        }

    def get_current_macd(self, candles: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get current MACD values"""
        result = self.calculate(candles)
        return {
            "macd": result["macd"][-1] if result["macd"] else 0.0,
            "signal": result["signal"][-1] if result["signal"] else 0.0,
            "histogram": result["histogram"][-1] if result["histogram"] else 0.0
        }

    def get_macd_status(self, macd: float, signal: float, histogram: float) -> str:
        """Get MACD status"""
        if histogram > 0 and macd > signal:
            return "BULLISH"
        elif histogram < 0 and macd < signal:
            return "BEARISH"
        elif histogram > 0:
            return "BULLISH_CROSS"
        elif histogram < 0:
            return "BEARISH_CROSS"
        else:
            return "NEUTRAL"

    def is_crossover(self, candles: List[Dict[str, Any]], threshold: float = 0.00001) -> str:
        """
        Check for MACD crossover
        Returns 'BULLISH', 'BEARISH', or None
        """
        result = self.calculate(candles)

        if len(result["macd"]) < 2:
            return None

        # Check for bullish crossover (MACD crosses above signal)
        if (result["macd"][-2] <= result["signal"][-2] + threshold and
            result["macd"][-1] > result["signal"][-1] - threshold):
            return "BULLISH"

        # Check for bearish crossover (MACD crosses below signal)
        if (result["macd"][-2] >= result["signal"][-2] - threshold and
            result["macd"][-1] < result["signal"][-1] + threshold):
            return "BEARISH"

        return None

    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return [None] * len(data)

        ema = [None] * period
        multiplier = 2 / (period + 1)

        # Calculate SMA for first period
        sma = sum(data[:period]) / period
        ema[period - 1] = sma

        # Calculate subsequent EMAs
        for i in range(period, len(data)):
            ema.append((data[i] - ema[i - 1]) * multiplier + ema[i - 1])

        return ema


# Singleton instance
macd_calculator = MACDCalculator()
