"""RSI (Relative Strength Index) Calculator"""
import numpy as np
from typing import List, Dict, Any, Optional


class RSICalculator:
    """Calculates RSI indicator"""

    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, candles: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate RSI from candles
        Returns list of RSI values, last value is current RSI
        """
        if len(candles) < self.period + 1:
            return [0.0] * len(candles)

        closes = [candle["close"] for candle in candles]

        # Calculate price changes
        changes = np.diff(closes)

        # Separate gains and losses
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        # Calculate initial average
        avg_gain = np.mean(gains[:self.period])
        avg_loss = np.mean(losses[:self.period])

        rsi_values = []

        # Calculate first RSI
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_values.append(rsi)

        # Calculate subsequent RSI using Wilder's smoothing
        for i in range(self.period, len(closes)):
            current_gain = gains[i - 1]
            current_loss = losses[i - 1]

            avg_gain = ((avg_gain * (self.period - 1)) + current_gain) / self.period
            avg_loss = ((avg_loss * (self.period - 1)) + current_loss) / self.period

            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

        # Pad with zeros for earlier candles
        rsi_values = [0.0] * (len(candles) - len(rsi_values)) + rsi_values

        return rsi_values

    def get_current_rsi(self, candles: List[Dict[str, Any]]) -> float:
        """Get current RSI value"""
        rsi_values = self.calculate(candles)
        return rsi_values[-1] if rsi_values else 0.0

    def get_rsi_status(self, rsi: float) -> str:
        """Get RSI status"""
        if rsi < 30:
            return "OVERSOLD"
        elif rsi > 70:
            return "OVERBOUGHT"
        elif rsi < 40:
            return "WEAK"
        elif rsi > 60:
            return "STRONG"
        else:
            return "NEUTRAL"

    def is_divergence(self, candles: List[Dict[str, Any]], threshold: float = 0.05) -> Optional[str]:
        """
        Check for RSI divergence
        Bullish divergence: Lower low in price, higher low in RSI
        Bearish divergence: Higher high in price, lower high in RSI
        """
        if len(candles) < 20:
            return False

        # Get last 10 candles
        recent_candles = candles[-10:]
        recent_rsi = self.calculate(recent_candles)

        # Find local highs and lows
        highs = []
        lows = []

        for i in range(2, len(recent_rsi) - 2):
            if (recent_rsi[i] > recent_rsi[i - 1] and
                recent_rsi[i] > recent_rsi[i - 2] and
                recent_rsi[i] > recent_rsi[i + 1] and
                recent_rsi[i] > recent_rsi[i + 2]):
                highs.append({
                    "index": i,
                    "rsi": recent_rsi[i],
                    "price": recent_candles[i]["high"]
                })

            if (recent_rsi[i] < recent_rsi[i - 1] and
                recent_rsi[i] < recent_rsi[i - 2] and
                recent_rsi[i] < recent_rsi[i + 1] and
                recent_rsi[i] < recent_rsi[i + 2]):
                lows.append({
                    "index": i,
                    "rsi": recent_rsi[i],
                    "price": recent_candles[i]["low"]
                })

        # Check for divergence
        if len(highs) >= 2 and len(lows) >= 2:
            # Bearish divergence (last high)
            last_high = highs[-1]
            prev_high = highs[-2]

            if (last_high["price"] > prev_high["price"] + threshold and
                last_high["rsi"] < prev_high["rsi"] - threshold):
                return "BEARISH"

            # Bullish divergence (last low)
            last_low = lows[-1]
            prev_low = lows[-2]

            if (last_low["price"] < prev_low["price"] - threshold and
                last_low["rsi"] > prev_low["rsi"] + threshold):
                return "BULLISH"

        return None


# Singleton instance
rsi_calculator = RSICalculator()
