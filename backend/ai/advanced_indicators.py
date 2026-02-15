"""Advanced Technical Indicators - Stochastic, Bollinger Bands, ADX, ATR"""
from typing import Dict, Any, List, Optional
import numpy as np


def _to_bool(value) -> bool:
    """Convert numpy boolean to Python boolean"""
    return bool(value) if value is not None else False


def _to_float(value) -> float:
    """Convert numpy float to Python float"""
    return float(value) if value is not None else 0.0


class AdvancedIndicators:
    """Calculate advanced technical indicators"""

    def __init__(self):
        # Default periods
        self.stoch_k_period = 14
        self.stoch_d_period = 3
        self.stoch_smooth = 3
        self.bb_period = 20
        self.bb_std = 2
        self.adx_period = 14
        self.atr_period = 14

    def calculate_all(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate all advanced indicators

        Returns:
            Dictionary with all indicator values
        """
        if len(candles) < self.atr_period + 5:
            return {
                "stochastic": None,
                "bollinger_bands": None,
                "adx": None,
                "atr": None,
                "error": "Insufficient data for advanced indicators"
            }

        return {
            "stochastic": self.calculate_stochastic(candles),
            "bollinger_bands": self.calculate_bollinger_bands(candles),
            "adx": self.calculate_adx(candles),
            "atr": self.calculate_atr(candles)
        }

    def calculate_stochastic(
        self,
        candles: List[Dict[str, Any]],
        k_period: int = None,
        d_period: int = None,
        smooth: int = None
    ) -> Dict[str, Any]:
        """
        Calculate Stochastic Oscillator

        Formula:
        %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = SMA of %K

        Returns:
            {
                "k_value": current %K (0-100),
                "d_value": current %D (0-100),
                "k_history": list of %K values,
                "d_history": list of %D values,
                "status": "OVERBOUGHT" | "OVERSOLD" | "NEUTRAL"
            }
        """
        k_period = k_period or self.stoch_k_period
        d_period = d_period or self.stoch_d_period
        smooth = smooth or self.stoch_smooth

        if len(candles) < k_period + d_period + smooth:
            return None

        # Extract high, low, close
        highs = np.array([c["high"] for c in candles])
        lows = np.array([c["low"] for c in candles])
        closes = np.array([c["close"] for c in candles])

        # Calculate %K
        k_values = []
        for i in range(k_period - 1, len(closes)):
            high_window = highs[i - k_period + 1:i + 1]
            low_window = lows[i - k_period + 1:i + 1]

            highest_high = np.max(high_window)
            lowest_low = np.min(low_window)

            if highest_high == lowest_low:
                k = 50
            else:
                k = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100

            k_values.append(k)

        # Smooth %K
        if smooth > 1:
            k_smoothed = self._sma(k_values, smooth)
        else:
            k_smoothed = k_values

        # Calculate %D (SMA of smoothed %K)
        d_values = self._sma(k_smoothed, d_period)

        # Get current values
        current_k = k_smoothed[-1] if k_smoothed else 50
        current_d = d_values[-1] if d_values else 50

        # Determine status
        if current_k > 80:
            status = "OVERBOUGHT"
        elif current_k < 20:
            status = "OVERSOLD"
        elif current_k > 60:
            status = "BULLISH"
        elif current_k < 40:
            status = "BEARISH"
        else:
            status = "NEUTRAL"

        return {
            "k_value": round(current_k, 2),
            "d_value": round(current_d, 2),
            "k_history": [round(k, 2) for k in k_smoothed[-20:]],
            "d_history": [round(d, 2) for d in d_values[-20:]],
            "status": status,
            "crossover": self._detect_stoch_crossover(k_smoothed, d_values)
        }

    def _detect_stoch_crossover(self, k_values: List[float], d_values: List[float]) -> str:
        """Detect stochastic crossover signals"""
        if len(k_values) < 2 or len(d_values) < 2:
            return "NONE"

        # Recent crossover detection
        recent_k = k_values[-3:]
        recent_d = d_values[-3:]

        if len(recent_k) < 2 or len(recent_d) < 2:
            return "NONE"

        # Bullish crossover: K crosses above D
        if (recent_k[-2] <= recent_d[-2] and recent_k[-1] > recent_d[-1] and
            recent_k[-1] < 80):  # Not in overbought
            return "BULLISH_CROSS"

        # Bearish crossover: K crosses below D
        if (recent_k[-2] >= recent_d[-2] and recent_k[-1] < recent_d[-1] and
            recent_k[-1] > 20):  # Not in oversold
            return "BEARISH_CROSS"

        return "NONE"

    def calculate_bollinger_bands(
        self,
        candles: List[Dict[str, Any]],
        period: int = None,
        std_dev: float = None
    ) -> Dict[str, Any]:
        """
        Calculate Bollinger Bands

        Formula:
        Middle Band = SMA(Close, period)
        Upper Band = Middle Band + (std * StdDev(Close, period))
        Lower Band = Middle Band - (std * StdDev(Close, period))
        Bandwidth = (Upper - Lower) / Middle

        Returns:
            {
                "upper": upper band value,
                "middle": middle band (SMA),
                "lower": lower band value,
                "bandwidth": bandwidth percentage,
                "position": "ABOVE_UPPER" | "BELOW_LOWER" | "BETWEEN" | "AT_MIDDLE"
            }
        """
        period = period or self.bb_period
        std_dev = std_dev or self.bb_std

        if len(candles) < period:
            return None

        closes = np.array([c["close"] for c in candles])

        # Calculate middle band (SMA)
        middle_band = self._sma(closes, period)

        # Calculate standard deviation
        std_values = []
        for i in range(period - 1, len(closes)):
            window = closes[i - period + 1:i + 1]
            std = np.std(window)
            std_values.append(std)

        # Calculate upper and lower bands
        upper_band = [m + (std_dev * s) for m, s in zip(middle_band, std_values)]
        lower_band = [m - (std_dev * s) for m, s in zip(middle_band, std_values)]

        # Get current values
        current_close = closes[-1]
        current_upper = upper_band[-1]
        current_middle = middle_band[-1]
        current_lower = lower_band[-1]
        current_bandwidth = ((current_upper - current_lower) / current_middle * 100) if current_middle > 0 else 0

        # Determine price position
        if current_close > current_upper:
            position = "ABOVE_UPPER"
        elif current_close < current_lower:
            position = "BELOW_LOWER"
        elif abs(current_close - current_middle) < (current_upper - current_lower) * 0.1:
            position = "AT_MIDDLE"
        elif current_close > current_middle:
            position = "UPPER_HALF"
        else:
            position = "LOWER_HALF"

        # Determine squeeze (low volatility)
        bandwidth_history = [((u - l) / m * 100) for u, l, m in zip(upper_band[-20:], lower_band[-20:], middle_band[-20:])]
        avg_bandwidth = np.mean(bandwidth_history) if bandwidth_history else 0
        is_squeeze = current_bandwidth < avg_bandwidth * 0.5

        return {
            "upper": round(current_upper, 5),
            "middle": round(current_middle, 5),
            "lower": round(current_lower, 5),
            "bandwidth": round(current_bandwidth, 3),
            "avg_bandwidth": round(_to_float(avg_bandwidth), 3),
            "position": position,
            "squeeze": _to_bool(is_squeeze),
            "squeeze_alert": _to_bool(is_squeeze and current_bandwidth < 1.0)
        }

    def calculate_adx(
        self,
        candles: List[Dict[str, Any]],
        period: int = None
    ) -> Dict[str, Any]:
        """
        Calculate Average Directional Index (ADX)

        Measures trend strength (0-100)
        - ADX > 25: Strong trend
        - ADX 20-25: Trending
        - ADX < 20: No trend (sideways)

        Returns:
            {
                "adx": current ADX value,
                "di_plus": positive directional indicator,
                "di_minus": negative directional indicator,
                "trend_strength": "STRONG" | "TRENDING" | "WEAK" | "NONE",
                "direction": "BULLISH" | "BEARISH" | "NEUTRAL"
            }
        """
        period = period or self.adx_period

        if len(candles) < period * 2:
            return None

        highs = np.array([c["high"] for c in candles])
        lows = np.array([c["low"] for c in candles])
        closes = np.array([c["close"] for c in candles])

        # Calculate True Range (TR)
        tr_values = []
        for i in range(1, len(candles)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)

        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        for i in range(1, len(candles)):
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]

            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)

            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)

        # Smooth TR, +DM, -DM
        tr_smooth = self._sma(tr_values, period)
        plus_dm_smooth = self._sma(plus_dm, period)
        minus_dm_smooth = self._sma(minus_dm, period)

        # Calculate +DI and -DI
        plus_di = [(pdm / tr * 100) if tr > 0 else 0 for pdm, tr in zip(plus_dm_smooth, tr_smooth)]
        minus_di = [(mdm / tr * 100) if tr > 0 else 0 for mdm, tr in zip(minus_dm_smooth, tr_smooth)]

        # Calculate DX
        dx = []
        for pdi, mdi in zip(plus_di, minus_di):
            di_sum = pdi + mdi
            if di_sum > 0:
                dx.append(abs(pdi - mdi) / di_sum * 100)
            else:
                dx.append(0)

        # Calculate ADX
        adx = self._sma(dx, period)

        # Get current values
        current_adx = adx[-1] if adx else 0
        current_di_plus = plus_di[-1] if plus_di else 0
        current_di_minus = minus_di[-1] if minus_di else 0

        # Determine trend strength
        if current_adx > 40:
            trend_strength = "VERY_STRONG"
        elif current_adx > 25:
            trend_strength = "STRONG"
        elif current_adx > 20:
            trend_strength = "TRENDING"
        elif current_adx > 10:
            trend_strength = "WEAK"
        else:
            trend_strength = "NONE"

        # Determine direction
        if current_di_plus > current_di_minus:
            direction = "BULLISH"
        elif current_di_minus > current_di_plus:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        return {
            "adx": round(current_adx, 2),
            "di_plus": round(current_di_plus, 2),
            "di_minus": round(current_di_minus, 2),
            "trend_strength": trend_strength,
            "direction": direction,
            "history": [round(a, 2) for a in adx[-20:]]
        }

    def calculate_atr(
        self,
        candles: List[Dict[str, Any]],
        period: int = None
    ) -> Dict[str, Any]:
        """
        Calculate Average True Range (ATR)

        Measures market volatility
        Formula: Average of True Range over period
        True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)

        Returns:
            {
                "atr": current ATR value,
                "atr_percent": ATR as percentage of price,
                "atr_pips": ATR in pips,
                "volatility": "HIGH" | "NORMAL" | "LOW"
            }
        """
        period = period or self.atr_period

        if len(candles) < period + 1:
            return None

        highs = np.array([c["high"] for c in candles])
        lows = np.array([c["low"] for c in candles])
        closes = np.array([c["close"] for c in candles])

        # Calculate True Range (TR)
        tr_values = []
        for i in range(1, len(candles)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)

        # Calculate ATR (SMA of TR)
        atr_values = self._sma(tr_values, period)

        # Get current ATR
        current_atr = atr_values[-1] if atr_values else 0
        current_close = closes[-1]

        # Calculate ATR as percentage
        atr_percent = (current_atr / current_close * 100) if current_close > 0 else 0

        # Calculate in pips (assuming standard forex pair)
        atr_pips = current_atr * 10000

        # Determine volatility level based on ATR percentage
        if atr_percent > 0.5:
            volatility = "HIGH"
        elif atr_percent > 0.2:
            volatility = "NORMAL"
        else:
            volatility = "LOW"

        # Calculate ATR history for trend
        atr_history = atr_values[-20:]
        if len(atr_history) > 5:
            recent_avg = np.mean(atr_history[-5:])
            older_avg = np.mean(atr_history[:-5])
            volatility_trend = "INCREASING" if recent_avg > older_avg else "DECREASING"
        else:
            volatility_trend = "STABLE"

        return {
            "atr": round(current_atr, 5),
            "atr_percent": round(atr_percent, 4),
            "atr_pips": round(atr_pips, 2),
            "volatility": volatility,
            "volatility_trend": volatility_trend,
            "history": [round(a, 5) for a in atr_history]
        }

    def _sma(self, data: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return []

        sma_values = []
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            sma = sum(window) / period
            sma_values.append(sma)

        return sma_values


# Singleton instance
advanced_indicators_instance = AdvancedIndicators()

# Convenience function wrapper
def calculate_advanced_indicators(candles):
    """Calculate all advanced indicators from candle data"""
    return advanced_indicators_instance.calculate_all(candles)

def calculate_stochastic(candles, **kwargs):
    """Calculate stochastic oscillator"""
    return advanced_indicators_instance.calculate_stochastic(candles, **kwargs)

def calculate_bollinger_bands(candles, **kwargs):
    """Calculate bollinger bands"""
    return advanced_indicators_instance.calculate_bollinger_bands(candles, **kwargs)

def calculate_adx(candles, **kwargs):
    """Calculate ADX"""
    return advanced_indicators_instance.calculate_adx(candles, **kwargs)

def calculate_atr(candles, **kwargs):
    """Calculate ATR"""
    return advanced_indicators_instance.calculate_atr(candles, **kwargs)
