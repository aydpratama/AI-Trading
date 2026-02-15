"""Multi-Timeframe Analysis - Analyze multiple timeframes for confluence"""
from typing import List, Dict, Any, Optional
from ai.rsi_calculator import rsi_calculator
from ai.macd_calculator import macd_calculator
from ai.ma_calculator import ma_calculator
from ai.sr_detector import sr_detector
from ai.pattern_recognition import pattern_recognition
from mt5.connector import connector


class MultiTimeframeAnalyzer:
    """Analyze multiple timeframes for trading confluence"""

    TIMEFRAMES = {
        'M5': 5,
        'M15': 15,
        'M30': 30,
        'H1': 60,
        'H4': 240,
        'D1': 1440,
        'W1': 10080
    }

    # Timeframe hierarchy for trend confirmation
    TF_HIERARCHY = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']

    def __init__(self):
        self.min_candles = 50

    def analyze_all_timeframes(self, symbol: str, primary_timeframe: str = 'H1') -> Dict[str, Any]:
        """
        Analyze all relevant timeframes and find confluence
        Returns comprehensive analysis with trend alignment
        """
        result = {
            "symbol": symbol,
            "primary_timeframe": primary_timeframe,
            "timeframes": {},
            "confluence": {
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "alignment_score": 0,
                "trend_direction": "NEUTRAL",
                "confidence": 0
            },
            "recommendation": None,
            "patterns": {"bullish": [], "bearish": []},
            "key_levels": {
                "resistance": [],
                "support": []
            }
        }

        # Determine which timeframes to analyze
        tf_to_analyze = self._get_timeframes_to_analyze(primary_timeframe)

        for tf in tf_to_analyze:
            analysis = self._analyze_single_timeframe(symbol, tf)
            if analysis:
                result["timeframes"][tf] = analysis

                # Count trend directions
                if analysis["trend"] == "BULLISH":
                    result["confluence"]["bullish_count"] += 1
                elif analysis["trend"] == "BEARISH":
                    result["confluence"]["bearish_count"] += 1
                else:
                    result["confluence"]["neutral_count"] += 1

        # Calculate confluence
        total = len(result["timeframes"])
        if total > 0:
            bullish_pct = result["confluence"]["bullish_count"] / total
            bearish_pct = result["confluence"]["bearish_count"] / total

            # Alignment score (how much agreement between timeframes)
            max_pct = max(bullish_pct, bearish_pct)
            result["confluence"]["alignment_score"] = round(max_pct * 100, 1)

            if bullish_pct > 0.6:
                result["confluence"]["trend_direction"] = "BULLISH"
                result["confluence"]["confidence"] = round(bullish_pct * 100, 1)
            elif bearish_pct > 0.6:
                result["confluence"]["trend_direction"] = "BEARISH"
                result["confluence"]["confidence"] = round(bearish_pct * 100, 1)
            else:
                result["confluence"]["trend_direction"] = "MIXED"
                result["confluence"]["confidence"] = 50

        # Generate recommendation
        result["recommendation"] = self._generate_recommendation(result)

        # Collect patterns across timeframes
        result["patterns"] = self._collect_patterns(result["timeframes"])

        # Collect key levels
        result["key_levels"] = self._collect_key_levels(result["timeframes"])

        return result

    def _get_timeframes_to_analyze(self, primary_tf: str) -> List[str]:
        """Get list of timeframes to analyze based on primary"""
        try:
            idx = self.TF_HIERARCHY.index(primary_tf)
            # Get one lower and one higher timeframe
            start = max(0, idx - 1)
            end = min(len(self.TF_HIERARCHY), idx + 2)
            return self.TF_HIERARCHY[start:end]
        except ValueError:
            return ['M15', 'H1', 'H4']

    def _analyze_single_timeframe(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Analyze a single timeframe"""
        try:
            # Get candles
            candles = connector.get_candles(symbol, timeframe, 100)
            if not candles or len(candles) < 30:
                return None

            # Calculate indicators
            rsi_values = rsi_calculator.calculate(candles)
            macd_data = macd_calculator.calculate(candles)
            ma_data = ma_calculator.calculate(candles)
            sr_levels = sr_detector.detect(candles)
            patterns = pattern_recognition.detect_all_patterns(candles)

            current_price = candles[-1]["close"]
            current_rsi = rsi_values[-1] if rsi_values else 50
            current_macd = macd_data["macd"][-1] if macd_data["macd"] else 0
            current_signal = macd_data["signal"][-1] if macd_data["signal"] else 0
            histogram = macd_data["histogram"][-1] if macd_data["histogram"] else 0

            ema_9 = ma_data["ema_9"][-1] if ma_data["ema_9"] else current_price
            ema_21 = ma_data["ema_21"][-1] if ma_data["ema_21"] else current_price
            ema_50 = ma_data["ema_50"][-1] if ma_data["ema_50"] else current_price

            # Determine trend
            trend = self._determine_trend(
                current_price, ema_9, ema_21, ema_50,
                current_rsi, histogram
            )

            # Calculate momentum
            momentum = self._calculate_momentum(candles, rsi_values, macd_data)

            # Signal strength
            signal_strength = self._calculate_signal_strength(
                current_rsi, histogram, ema_9, ema_21, ema_50, current_price
            )

            return {
                "timeframe": timeframe,
                "trend": trend,
                "momentum": momentum,
                "signal_strength": signal_strength,
                "price": current_price,
                "indicators": {
                    "rsi": round(current_rsi, 2),
                    "macd": round(current_macd, 6),
                    "signal": round(current_signal, 6),
                    "histogram": round(histogram, 6),
                    "ema_9": round(ema_9, 5),
                    "ema_21": round(ema_21, 5),
                    "ema_50": round(ema_50, 5)
                },
                "patterns": patterns,
                "support_resistance": sr_levels,
                "candles_count": len(candles)
            }

        except Exception as e:
            print(f"Error analyzing {symbol} {timeframe}: {e}")
            return None

    def _determine_trend(self, price: float, ema9: float, ema21: float, ema50: float,
                         rsi: float, histogram: float) -> str:
        """Determine trend direction based on multiple factors"""
        bullish_signals = 0
        bearish_signals = 0

        # EMA alignment
        if ema9 > ema21 > ema50:
            bullish_signals += 2
        elif ema9 < ema21 < ema50:
            bearish_signals += 2
        elif ema9 > ema21:
            bullish_signals += 1
        elif ema9 < ema21:
            bearish_signals += 1

        # Price vs EMA
        if price > ema21:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # MACD histogram
        if histogram > 0:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # RSI trend
        if rsi > 50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if bullish_signals >= 4:
            return "BULLISH"
        elif bearish_signals >= 4:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_momentum(self, candles: List[Dict], rsi: List[float],
                            macd: Dict) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        if len(candles) < 10:
            return {"value": 0, "direction": "NEUTRAL"}

        # Price momentum (last 5 candles)
        price_change = (candles[-1]["close"] - candles[-5]["close"]) / candles[-5]["close"] * 100

        # RSI momentum
        rsi_change = rsi[-1] - rsi[-5] if len(rsi) >= 5 else 0

        # MACD momentum
        hist_values = macd.get("histogram", [])
        macd_momentum = hist_values[-1] - hist_values[-3] if len(hist_values) >= 3 else 0

        # Combined momentum
        momentum_value = (price_change * 10) + (rsi_change * 0.5) + (macd_momentum * 1000)

        if momentum_value > 1:
            direction = "BULLISH"
        elif momentum_value < -1:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        return {
            "value": round(momentum_value, 2),
            "direction": direction,
            "price_change_pct": round(price_change, 3)
        }

    def _calculate_signal_strength(self, rsi: float, histogram: float,
                                   ema9: float, ema21: float, ema50: float,
                                   price: float) -> int:
        """Calculate overall signal strength (0-100)"""
        strength = 50  # Base

        # RSI contribution (max 20 points)
        if rsi < 30:  # Oversold - bullish
            strength += 20
        elif rsi > 70:  # Overbought - bearish signal
            strength -= 20
        elif 40 <= rsi <= 60:
            strength += 0  # Neutral
        elif rsi > 60:
            strength += 10
        else:
            strength -= 10

        # EMA alignment (max 15 points)
        if ema9 > ema21 > ema50:
            strength += 15
        elif ema9 < ema21 < ema50:
            strength -= 15

        # MACD histogram (max 15 points)
        if histogram > 0:
            strength += min(15, histogram * 1000)
        else:
            strength += max(-15, histogram * 1000)

        return max(0, min(100, int(strength)))

    def _generate_recommendation(self, analysis: Dict) -> Optional[Dict[str, Any]]:
        """Generate trading recommendation based on multi-timeframe analysis"""
        confluence = analysis["confluence"]

        if confluence["alignment_score"] < 60:
            return None  # Not enough confluence

        direction = confluence["trend_direction"]
        if direction == "MIXED" or direction == "NEUTRAL":
            return None

        # Get primary timeframe data
        primary_tf = analysis.get("timeframes", {}).get(analysis["primary_timeframe"])
        if not primary_tf:
            return None

        price = primary_tf["price"]
        indicators = primary_tf["indicators"]
        sr = primary_tf.get("support_resistance", {})

        # Calculate entry, SL, TP
        if direction == "BULLISH":
            entry = price
            # SL below nearest support or 0.5%
            support = sr.get("support", [price * 0.99])
            sl = min(support) if support else price * 0.995
            if sl >= entry:
                sl = entry * 0.995

            # TP at resistance or 1:2 R:R
            resistance = sr.get("resistance", [price * 1.01])
            tp = max(resistance) if resistance else entry * 1.01
            risk = entry - sl
            tp = max(tp, entry + (risk * 2))

        else:  # BEARISH
            entry = price
            # SL above nearest resistance
            resistance = sr.get("resistance", [price * 1.01])
            sl = max(resistance) if resistance else price * 1.005
            if sl <= entry:
                sl = entry * 1.005

            # TP at support or 1:2 R:R
            support = sr.get("support", [price * 0.99])
            tp = min(support) if support else entry * 0.99
            risk = sl - entry
            tp = min(tp, entry - (risk * 2))

        # Calculate risk/reward
        if direction == "BULLISH":
            risk = entry - sl
            reward = tp - entry
        else:
            risk = sl - entry
            reward = entry - tp

        risk_reward = round(reward / risk, 2) if risk > 0 else 0

        return {
            "direction": direction,
            "entry": round(entry, 5),
            "stop_loss": round(sl, 5),
            "take_profit": round(tp, 5),
            "risk_reward": risk_reward,
            "confidence": confluence["confidence"],
            "timeframes_aligned": f"{confluence['bullish_count'] if direction == 'BULLISH' else confluence['bearish_count']}/{len(analysis['timeframes'])}",
            "reason": f"{direction} confluence across {confluence['alignment_score']}% of timeframes"
        }

    def _collect_patterns(self, timeframes: Dict) -> Dict[str, List]:
        """Collect all patterns from all timeframes"""
        bullish = []
        bearish = []

        for tf, data in timeframes.items():
            patterns = data.get("patterns", {})
            for p in patterns.get("bullish", []):
                bullish.append({**p, "timeframe": tf})
            for p in patterns.get("bearish", []):
                bearish.append({**p, "timeframe": tf})

        return {"bullish": bullish, "bearish": bearish}

    def _collect_key_levels(self, timeframes: Dict) -> Dict[str, List]:
        """Collect key support/resistance levels from all timeframes"""
        all_resistance = []
        all_support = []

        for tf, data in timeframes.items():
            sr = data.get("support_resistance", {})
            for r in sr.get("resistance", []):
                all_resistance.append({"level": r, "timeframe": tf})
            for s in sr.get("support", []):
                all_support.append({"level": s, "timeframe": tf})

        # Sort and remove duplicates (within 0.1%)
        def dedupe(levels):
            if not levels:
                return []
            sorted_levels = sorted(levels, key=lambda x: x["level"])
            result = [sorted_levels[0]]
            for level in sorted_levels[1:]:
                diff = abs(level["level"] - result[-1]["level"]) / result[-1]["level"]
                if diff > 0.001:
                    result.append(level)
            return result

        return {
            "resistance": dedupe(all_resistance),
            "support": dedupe(all_support)
        }

    def get_best_entry_time(self, symbol: str) -> Dict[str, Any]:
        """Analyze best time to enter based on session and volatility"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        hour = now.hour

        # Trading sessions (UTC)
        sessions = {
            "sydney": (22, 7),    # 22:00 - 07:00 UTC
            "tokyo": (0, 9),      # 00:00 - 09:00 UTC
            "london": (8, 17),    # 08:00 - 17:00 UTC
            "new_york": (13, 22)  # 13:00 - 22:00 UTC
        }

        active_sessions = []
        for session, (start, end) in sessions.items():
            if start <= hour < end or (start > end and (hour >= start or hour < end)):
                active_sessions.append(session)

        # Best trading times
        best_times = {
            "asia_europe_overlap": (8, 9),    # London open + Tokyo close
            "europe_us_overlap": (13, 17),    # London + NY overlap
        }

        is_best_time = False
        current_quality = "LOW"

        for period, (start, end) in best_times.items():
            if start <= hour < end:
                is_best_time = True
                current_quality = "HIGH"
                break

        if not is_best_time and active_sessions:
            current_quality = "MEDIUM"

        return {
            "current_hour_utc": hour,
            "active_sessions": active_sessions,
            "is_best_time": is_best_time,
            "quality": current_quality,
            "recommendation": "WAIT" if current_quality == "LOW" else "GOOD TO TRADE"
        }


# Singleton
mtf_analyzer = MultiTimeframeAnalyzer()