"""Pattern Recognition - Candlestick & Chart Patterns"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class PatternRecognition:
    """Recognizes candlestick and chart patterns for trading signals"""

    def __init__(self):
        self.min_pattern_candles = 5

    def detect_all_patterns(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect all patterns from candles"""
        if len(candles) < 10:
            return {"bullish": [], "bearish": [], "neutral": [], "signals": []}

        patterns = {
            "bullish": [],
            "bearish": [],
            "neutral": [],
            "signals": []
        }

        # Candlestick patterns
        candle_patterns = self._detect_candlestick_patterns(candles)
        patterns["bullish"].extend(candle_patterns["bullish"])
        patterns["bearish"].extend(candle_patterns["bearish"])

        # Chart patterns
        chart_patterns = self._detect_chart_patterns(candles)
        patterns["bullish"].extend(chart_patterns["bullish"])
        patterns["bearish"].extend(chart_patterns["bearish"])

        # Generate signals from patterns
        patterns["signals"] = self._generate_pattern_signals(patterns, candles)

        return patterns

    def _detect_candlestick_patterns(self, candles: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Detect single and multi-candle patterns"""
        bullish = []
        bearish = []

        if len(candles) < 5:
            return {"bullish": bullish, "bearish": bearish}

        # Last 5 candles for analysis
        recent = candles[-5:]

        # Single candle patterns
        last = candles[-1]
        prev = candles[-2] if len(candles) > 1 else None

        # Doji
        if self._is_doji(last):
            if prev and prev["close"] < prev["open"]:  # Downtrend
                bullish.append({
                    "name": "Doji",
                    "type": "reversal",
                    "strength": 60,
                    "description": "Doji after downtrend - potential reversal"
                })
            elif prev and prev["close"] > prev["open"]:  # Uptrend
                bearish.append({
                    "name": "Doji",
                    "type": "reversal",
                    "strength": 60,
                    "description": "Doji after uptrend - potential reversal"
                })

        # Hammer (bullish reversal)
        if self._is_hammer(last):
            bullish.append({
                "name": "Hammer",
                "type": "reversal",
                "strength": 75,
                "description": "Hammer candle - strong bullish reversal signal"
            })

        # Inverted Hammer
        if self._is_inverted_hammer(last):
            bullish.append({
                "name": "Inverted Hammer",
                "type": "reversal",
                "strength": 70,
                "description": "Inverted hammer - potential bullish reversal"
            })

        # Hanging Man (bearish)
        if self._is_hanging_man(last, candles):
            bearish.append({
                "name": "Hanging Man",
                "type": "reversal",
                "strength": 70,
                "description": "Hanging man - bearish reversal signal"
            })

        # Shooting Star (bearish)
        if self._is_shooting_star(last):
            bearish.append({
                "name": "Shooting Star",
                "type": "reversal",
                "strength": 75,
                "description": "Shooting star - strong bearish reversal"
            })

        # Multi-candle patterns
        if len(candles) >= 2:
            # Bullish Engulfing
            if self._is_bullish_engulfing(prev, last):
                bullish.append({
                    "name": "Bullish Engulfing",
                    "type": "reversal",
                    "strength": 85,
                    "description": "Bullish engulfing - strong buy signal"
                })

            # Bearish Engulfing
            if self._is_bearish_engulfing(prev, last):
                bearish.append({
                    "name": "Bearish Engulfing",
                    "type": "reversal",
                    "strength": 85,
                    "description": "Bearish engulfing - strong sell signal"
                })

        if len(candles) >= 3:
            prev2 = candles[-3]

            # Morning Star (bullish)
            if self._is_morning_star(prev2, prev, last):
                bullish.append({
                    "name": "Morning Star",
                    "type": "reversal",
                    "strength": 90,
                    "description": "Morning star - very strong bullish reversal"
                })

            # Evening Star (bearish)
            if self._is_evening_star(prev2, prev, last):
                bearish.append({
                    "name": "Evening Star",
                    "type": "reversal",
                    "strength": 90,
                    "description": "Evening star - very strong bearish reversal"
                })

            # Three White Soldiers
            if self._is_three_white_soldiers(candles[-3:]):
                bullish.append({
                    "name": "Three White Soldiers",
                    "type": "continuation",
                    "strength": 85,
                    "description": "Three white soldiers - strong bullish continuation"
                })

            # Three Black Crows
            if self._is_three_black_crows(candles[-3:]):
                bearish.append({
                    "name": "Three Black Crows",
                    "type": "continuation",
                    "strength": 85,
                    "description": "Three black crows - strong bearish continuation"
                })

        # Piercing Line (bullish)
        if prev and self._is_piercing_line(prev, last):
            bullish.append({
                "name": "Piercing Line",
                "type": "reversal",
                "strength": 75,
                "description": "Piercing line - bullish reversal pattern"
            })

        # Dark Cloud Cover (bearish)
        if prev and self._is_dark_cloud_cover(prev, last):
            bearish.append({
                "name": "Dark Cloud Cover",
                "type": "reversal",
                "strength": 75,
                "description": "Dark cloud cover - bearish reversal pattern"
            })

        return {"bullish": bullish, "bearish": bearish}

    def _detect_chart_patterns(self, candles: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Detect larger chart patterns"""
        bullish = []
        bearish = []

        if len(candles) < 20:
            return {"bullish": bullish, "bearish": bearish}

        # Double Bottom (bullish)
        if self._is_double_bottom(candles):
            bullish.append({
                "name": "Double Bottom",
                "type": "reversal",
                "strength": 85,
                "description": "Double bottom pattern - strong bullish reversal"
            })

        # Double Top (bearish)
        if self._is_double_top(candles):
            bearish.append({
                "name": "Double Top",
                "type": "reversal",
                "strength": 85,
                "description": "Double top pattern - strong bearish reversal"
            })

        # Head and Shoulders (bearish)
        if self._is_head_and_shoulders(candles):
            bearish.append({
                "name": "Head and Shoulders",
                "type": "reversal",
                "strength": 90,
                "description": "Head and shoulders - major bearish reversal"
            })

        # Inverse Head and Shoulders (bullish)
        if self._is_inverse_head_and_shoulders(candles):
            bullish.append({
                "name": "Inverse Head and Shoulders",
                "type": "reversal",
                "strength": 90,
                "description": "Inverse head and shoulders - major bullish reversal"
            })

        # Ascending Triangle (bullish)
        if self._is_ascending_triangle(candles):
            bullish.append({
                "name": "Ascending Triangle",
                "type": "continuation",
                "strength": 75,
                "description": "Ascending triangle - bullish continuation"
            })

        # Descending Triangle (bearish)
        if self._is_descending_triangle(candles):
            bearish.append({
                "name": "Descending Triangle",
                "type": "continuation",
                "strength": 75,
                "description": "Descending triangle - bearish continuation"
            })

        # Bull Flag
        if self._is_bull_flag(candles):
            bullish.append({
                "name": "Bull Flag",
                "type": "continuation",
                "strength": 70,
                "description": "Bull flag - bullish continuation pattern"
            })

        # Bear Flag
        if self._is_bear_flag(candles):
            bearish.append({
                "name": "Bear Flag",
                "type": "continuation",
                "strength": 70,
                "description": "Bear flag - bearish continuation pattern"
            })

        return {"bullish": bullish, "bearish": bearish}

    # Single Candle Patterns
    def _is_doji(self, candle: Dict) -> bool:
        """Check if candle is a doji"""
        body = abs(candle["close"] - candle["open"])
        range_val = candle["high"] - candle["low"]
        if range_val == 0:
            return False
        return body / range_val < 0.1

    def _is_hammer(self, candle: Dict) -> bool:
        """Check if candle is a hammer"""
        body = abs(candle["close"] - candle["open"])
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]
        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        range_val = candle["high"] - candle["low"]

        if range_val == 0:
            return False

        # Lower wick should be at least 2x body, small or no upper wick
        return lower_wick >= body * 2 and upper_wick < body and body / range_val < 0.3

    def _is_inverted_hammer(self, candle: Dict) -> bool:
        """Check if candle is an inverted hammer"""
        body = abs(candle["close"] - candle["open"])
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]
        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        range_val = candle["high"] - candle["low"]

        if range_val == 0:
            return False

        return upper_wick >= body * 2 and lower_wick < body and body / range_val < 0.3

    def _is_hanging_man(self, candle: Dict, candles: List[Dict]) -> bool:
        """Check if candle is a hanging man (in uptrend)"""
        if len(candles) < 5:
            return False

        # Must be in uptrend
        trend = candles[-5]["close"] < candle["close"]
        return trend and self._is_hammer(candle)

    def _is_shooting_star(self, candle: Dict) -> bool:
        """Check if candle is a shooting star"""
        body = abs(candle["close"] - candle["open"])
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]
        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        range_val = candle["high"] - candle["low"]

        if range_val == 0:
            return False

        # Upper wick should be at least 2x body, small lower wick
        return upper_wick >= body * 2 and lower_wick < body * 0.5 and body / range_val < 0.3

    # Multi-Candle Patterns
    def _is_bullish_engulfing(self, prev: Dict, curr: Dict) -> bool:
        """Check for bullish engulfing pattern"""
        if not prev or not curr:
            return False

        # Previous candle is bearish
        prev_bearish = prev["close"] < prev["open"]
        # Current candle is bullish
        curr_bullish = curr["close"] > curr["open"]
        # Current engulfs previous
        engulfs = curr["open"] < prev["close"] and curr["close"] > prev["open"]

        return prev_bearish and curr_bullish and engulfs

    def _is_bearish_engulfing(self, prev: Dict, curr: Dict) -> bool:
        """Check for bearish engulfing pattern"""
        if not prev or not curr:
            return False

        # Previous candle is bullish
        prev_bullish = prev["close"] > prev["open"]
        # Current candle is bearish
        curr_bearish = curr["close"] < curr["open"]
        # Current engulfs previous
        engulfs = curr["open"] > prev["close"] and curr["close"] < prev["open"]

        return prev_bullish and curr_bearish and engulfs

    def _is_morning_star(self, c1: Dict, c2: Dict, c3: Dict) -> bool:
        """Check for morning star pattern"""
        # First candle: bearish
        first_bearish = c1["close"] < c1["open"]
        # Second candle: small body (doji-like)
        second_small = abs(c2["close"] - c2["open"]) < abs(c1["close"] - c1["open"]) * 0.3
        # Third candle: bullish, closes above midpoint of first
        third_bullish = c3["close"] > c3["open"]
        third_closes_high = c3["close"] > (c1["open"] + c1["close"]) / 2

        return first_bearish and second_small and third_bullish and third_closes_high

    def _is_evening_star(self, c1: Dict, c2: Dict, c3: Dict) -> bool:
        """Check for evening star pattern"""
        # First candle: bullish
        first_bullish = c1["close"] > c1["open"]
        # Second candle: small body
        second_small = abs(c2["close"] - c2["open"]) < abs(c1["close"] - c1["open"]) * 0.3
        # Third candle: bearish, closes below midpoint of first
        third_bearish = c3["close"] < c3["open"]
        third_closes_low = c3["close"] < (c1["open"] + c1["close"]) / 2

        return first_bullish and second_small and third_bearish and third_closes_low

    def _is_three_white_soldiers(self, candles: List[Dict]) -> bool:
        """Check for three white soldiers"""
        if len(candles) < 3:
            return False

        all_bullish = all(c["close"] > c["open"] for c in candles)
        increasing = candles[0]["close"] < candles[1]["close"] < candles[2]["close"]
        small_wicks = all(
            (c["high"] - c["close"]) < (c["close"] - c["open"]) * 0.3
            for c in candles
        )

        return all_bullish and increasing and small_wicks

    def _is_three_black_crows(self, candles: List[Dict]) -> bool:
        """Check for three black crows"""
        if len(candles) < 3:
            return False

        all_bearish = all(c["close"] < c["open"] for c in candles)
        decreasing = candles[0]["close"] > candles[1]["close"] > candles[2]["close"]
        small_wicks = all(
            (c["close"] - c["low"]) < (c["open"] - c["close"]) * 0.3
            for c in candles
        )

        return all_bearish and decreasing and small_wicks

    def _is_piercing_line(self, prev: Dict, curr: Dict) -> bool:
        """Check for piercing line pattern"""
        prev_bearish = prev["close"] < prev["open"]
        curr_bullish = curr["close"] > curr["open"]
        closes_above_mid = curr["close"] > (prev["open"] + prev["close"]) / 2
        opens_below_prev = curr["open"] < prev["close"]

        return prev_bearish and curr_bullish and closes_above_mid and opens_below_prev

    def _is_dark_cloud_cover(self, prev: Dict, curr: Dict) -> bool:
        """Check for dark cloud cover pattern"""
        prev_bullish = prev["close"] > prev["open"]
        curr_bearish = curr["close"] < curr["open"]
        closes_below_mid = curr["close"] < (prev["open"] + prev["close"]) / 2
        opens_above_prev = curr["open"] > prev["close"]

        return prev_bullish and curr_bearish and closes_below_mid and opens_above_prev

    # Chart Patterns
    def _is_double_bottom(self, candles: List[Dict]) -> bool:
        """Detect double bottom pattern"""
        if len(candles) < 20:
            return False

        lows = [c["low"] for c in candles[-20:]]
        min_low = min(lows)
        min_idx = lows.index(min_low)

        # Find second bottom
        if min_idx > 5:
            recent_lows = lows[min_idx + 5:]
            if recent_lows:
                second_min = min(recent_lows)
                # Two bottoms within 1% of each other
                if abs(second_min - min_low) / min_low < 0.01:
                    return True

        return False

    def _is_double_top(self, candles: List[Dict]) -> bool:
        """Detect double top pattern"""
        if len(candles) < 20:
            return False

        highs = [c["high"] for c in candles[-20:]]
        max_high = max(highs)
        max_idx = highs.index(max_high)

        if max_idx > 5:
            recent_highs = highs[max_idx + 5:]
            if recent_highs:
                second_max = max(recent_highs)
                if abs(second_max - max_high) / max_high < 0.01:
                    return True

        return False

    def _is_head_and_shoulders(self, candles: List[Dict]) -> bool:
        """Detect head and shoulders pattern (no scipy)"""
        if len(candles) < 30:
            return False

        highs = [c["high"] for c in candles[-30:]]

        # Find peaks manually
        peaks = []
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                peaks.append(i)

        if len(peaks) >= 3:
            last_three = peaks[-3:]
            left, head, right = [highs[p] for p in last_three]
            # Head should be higher than shoulders
            if head > left and head > right:
                # Shoulders should be roughly equal
                if abs(left - right) / left < 0.02:
                    return True

        return False

    def _is_inverse_head_and_shoulders(self, candles: List[Dict]) -> bool:
        """Detect inverse head and shoulders pattern (no scipy)"""
        if len(candles) < 30:
            return False

        lows = [c["low"] for c in candles[-30:]]

        # Find valleys manually
        valleys = []
        for i in range(5, len(lows) - 5):
            if lows[i] == min(lows[i-5:i+6]):
                valleys.append(i)

        if len(valleys) >= 3:
            last_three = valleys[-3:]
            left, head, right = [lows[v] for v in last_three]
            # Head should be lower than shoulders
            if head < left and head < right:
                if abs(left - right) / left < 0.02:
                    return True

        return False

    def _is_ascending_triangle(self, candles: List[Dict]) -> bool:
        """Detect ascending triangle"""
        if len(candles) < 15:
            return False

        highs = [c["high"] for c in candles[-15:]]
        lows = [c["low"] for c in candles[-15:]]

        # Flat resistance, rising support
        high_std = float(np.std(highs) / np.mean(highs))
        low_trend = bool(lows[-1] > lows[0])

        return bool(high_std < 0.005 and low_trend)

    def _is_descending_triangle(self, candles: List[Dict]) -> bool:
        """Detect descending triangle"""
        if len(candles) < 15:
            return False

        highs = [c["high"] for c in candles[-15:]]
        lows = [c["low"] for c in candles[-15:]]

        # Falling resistance, flat support
        low_std = float(np.std(lows) / np.mean(lows))
        high_trend = bool(highs[-1] < highs[0])

        return bool(low_std < 0.005 and high_trend)

    def _is_bull_flag(self, candles: List[Dict]) -> bool:
        """Detect bull flag pattern"""
        if len(candles) < 10:
            return False

        # Strong upward move followed by consolidation
        first_half = candles[:5]
        second_half = candles[5:]

        first_move = first_half[-1]["close"] - first_half[0]["open"]
        second_move = second_half[-1]["close"] - second_half[0]["open"]

        return first_move > 0 and abs(second_move) < first_move * 0.3

    def _is_bear_flag(self, candles: List[Dict]) -> bool:
        """Detect bear flag pattern"""
        if len(candles) < 10:
            return False

        first_half = candles[:5]
        second_half = candles[5:]

        first_move = first_half[-1]["close"] - first_half[0]["open"]
        second_move = second_half[-1]["close"] - second_half[0]["open"]

        return first_move < 0 and abs(second_move) < abs(first_move) * 0.3

    def _generate_pattern_signals(self, patterns: Dict, candles: List[Dict]) -> List[Dict]:
        """Generate trading signals from detected patterns"""
        signals = []

        bullish_strength = sum(p["strength"] for p in patterns["bullish"])
        bearish_strength = sum(p["strength"] for p in patterns["bearish"])

        current_price = candles[-1]["close"]

        if bullish_strength > bearish_strength and bullish_strength >= 100:
            patterns_list = [p["name"] for p in patterns["bullish"]]
            avg_strength = bullish_strength / len(patterns["bullish"]) if patterns["bullish"] else 0

            signals.append({
                "type": "BUY",
                "confidence": min(avg_strength, 95),
                "patterns": patterns_list,
                "entry": current_price,
                "reason": f"Multiple bullish patterns detected: {', '.join(patterns_list[:3])}"
            })

        elif bearish_strength > bullish_strength and bearish_strength >= 100:
            patterns_list = [p["name"] for p in patterns["bearish"]]
            avg_strength = bearish_strength / len(patterns["bearish"]) if patterns["bearish"] else 0

            signals.append({
                "type": "SELL",
                "confidence": min(avg_strength, 95),
                "patterns": patterns_list,
                "entry": current_price,
                "reason": f"Multiple bearish patterns detected: {', '.join(patterns_list[:3])}"
            })

        return signals


# Singleton
pattern_recognition = PatternRecognition()