"""
Market Structure Analysis - Swing Detection, Fibonacci, Supply & Demand

Provides advanced market structure analysis:
- Swing High/Low detection with classification (HH/HL/LH/LL)
- Fibonacci retracement/extension levels
- Supply & Demand zones
- Pivot Points (Daily/Weekly)
"""
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MarketStructureAnalyzer:
    """Analyze market structure for institutional-grade trading"""

    def __init__(self):
        self.fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]

    def analyze(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete market structure analysis"""
        if len(candles) < 20:
            return {
                "swing_classification": [],
                "fibonacci": {},
                "supply_demand": {"supply": [], "demand": []},
                "pivot_points": {},
                "trend_summary": "NEUTRAL"
            }

        try:
            # 1. Swing classification (HH/HL/LH/LL)
            swing_class = self._classify_swings(candles)
            
            # 2. Fibonacci levels
            fibonacci = self._calculate_fibonacci(candles)
            
            # 3. Supply & Demand zones
            supply_demand = self._detect_supply_demand(candles)
            
            # 4. Pivot Points
            pivot_points = self._calculate_pivot_points(candles)
            
            # 5. Trend summary
            trend = self._determine_trend(swing_class)

            return {
                "swing_classification": swing_class,
                "fibonacci": fibonacci,
                "supply_demand": supply_demand,
                "pivot_points": pivot_points,
                "trend_summary": trend
            }
        except Exception as e:
            logger.error(f"Market structure error: {e}")
            return {
                "swing_classification": [],
                "fibonacci": {},
                "supply_demand": {"supply": [], "demand": []},
                "pivot_points": {},
                "trend_summary": "NEUTRAL"
            }

    def _classify_swings(self, candles: List[Dict]) -> List[Dict]:
        """
        Classify swing points as HH/HL/LH/LL.
        
        HH (Higher High) + HL (Higher Low) = Uptrend
        LH (Lower High) + LL (Lower Low) = Downtrend
        """
        classifications = []
        lookback = 5
        
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(candles) - lookback):
            # Swing high
            if all(candles[i]["high"] >= candles[j]["high"]
                   for j in range(i - lookback, i + lookback + 1) if j != i):
                swing_highs.append({"index": i, "price": candles[i]["high"]})
            
            # Swing low
            if all(candles[i]["low"] <= candles[j]["low"]
                   for j in range(i - lookback, i + lookback + 1) if j != i):
                swing_lows.append({"index": i, "price": candles[i]["low"]})
        
        # Classify highs
        for i in range(1, len(swing_highs)):
            prev = swing_highs[i - 1]
            curr = swing_highs[i]
            
            if curr["price"] > prev["price"]:
                label = "HH"  # Higher High
            elif curr["price"] < prev["price"]:
                label = "LH"  # Lower High
            else:
                label = "EH"  # Equal High
            
            classifications.append({
                "type": "high",
                "label": label,
                "price": curr["price"],
                "index": curr["index"]
            })
        
        # Classify lows
        for i in range(1, len(swing_lows)):
            prev = swing_lows[i - 1]
            curr = swing_lows[i]
            
            if curr["price"] > prev["price"]:
                label = "HL"  # Higher Low
            elif curr["price"] < prev["price"]:
                label = "LL"  # Lower Low
            else:
                label = "EL"  # Equal Low
            
            classifications.append({
                "type": "low",
                "label": label,
                "price": curr["price"],
                "index": curr["index"]
            })
        
        classifications.sort(key=lambda x: x["index"])
        return classifications[-10:]  # Last 10

    def _calculate_fibonacci(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Fibonacci retracement and extension levels
        based on the most recent significant swing.
        """
        # Find significant swing high and low in recent candles
        recent = candles[-50:]
        if len(recent) < 20:
            return {}
        
        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        
        swing_high = max(highs)
        swing_low = min(lows)
        high_idx = highs.index(swing_high)
        low_idx = lows.index(swing_low)
        
        if swing_high == swing_low:
            return {}
        
        range_size = swing_high - swing_low
        
        # Determine if upswing or downswing (which came first)
        if high_idx > low_idx:
            # Upswing: low came first, high came later
            direction = "UP"
            retracements = {}
            for level in self.fib_levels:
                price = swing_high - (range_size * level)
                retracements[f"{level:.3f}"] = round(price, 5)
            
            # Extensions
            extensions = {}
            for ext in [1.272, 1.618, 2.0, 2.618]:
                price = swing_low + (range_size * ext)
                extensions[f"{ext:.3f}"] = round(price, 5)
        else:
            # Downswing: high came first, low came later
            direction = "DOWN"
            retracements = {}
            for level in self.fib_levels:
                price = swing_low + (range_size * level)
                retracements[f"{level:.3f}"] = round(price, 5)
            
            extensions = {}
            for ext in [1.272, 1.618, 2.0, 2.618]:
                price = swing_high - (range_size * ext)
                extensions[f"{ext:.3f}"] = round(price, 5)
        
        current_price = candles[-1]["close"]
        
        # Find nearest fib level
        all_levels = {**retracements}
        nearest_key = min(all_levels.keys(), key=lambda k: abs(all_levels[k] - current_price))
        
        return {
            "direction": direction,
            "swing_high": round(swing_high, 5),
            "swing_low": round(swing_low, 5),
            "retracements": retracements,
            "extensions": extensions,
            "nearest_level": {
                "level": nearest_key,
                "price": all_levels[nearest_key],
                "distance_pct": round(abs(all_levels[nearest_key] - current_price) / current_price * 100, 3)
            }
        }

    def _detect_supply_demand(self, candles: List[Dict]) -> Dict[str, List]:
        """
        Detect Supply and Demand zones.
        
        Demand Zone: Area where buyers stepped in strongly (rally-base-rally or drop-base-rally)
        Supply Zone: Area where sellers stepped in strongly (drop-base-drop or rally-base-drop)
        """
        supply_zones = []
        demand_zones = []
        current_price = candles[-1]["close"]
        
        # Look for explosive moves preceded by consolidation
        for i in range(3, len(candles) - 1):
            # Calculate body sizes
            body_prev = abs(candles[i-1]["close"] - candles[i-1]["open"])
            body_curr = abs(candles[i]["close"] - candles[i]["open"])
            avg_body = np.mean([abs(c["close"] - c["open"]) for c in candles[max(0,i-10):i]])
            
            if avg_body == 0:
                continue
            
            # Check for base (small candle) followed by explosive move
            is_base = body_prev < avg_body * 0.5  # Small body = consolidation
            is_explosive = body_curr > avg_body * 2.0  # Big body = explosive move
            
            if not (is_base and is_explosive):
                continue
            
            # Demand zone: explosive bullish move
            if candles[i]["close"] > candles[i]["open"]:
                zone = {
                    "type": "DEMAND",
                    "high": candles[i-1]["high"],
                    "low": candles[i-1]["low"],
                    "index": i - 1,
                    "age": len(candles) - 1 - i,
                    "strength": min(100, int(body_curr / avg_body * 25)),
                    "tested": False
                }
                # Check if zone has been tested
                for j in range(i + 1, len(candles)):
                    if candles[j]["low"] <= zone["high"]:
                        zone["tested"] = True
                        break
                
                if zone["age"] <= 40 and not zone["tested"]:
                    demand_zones.append(zone)
            
            # Supply zone: explosive bearish move
            elif candles[i]["close"] < candles[i]["open"]:
                zone = {
                    "type": "SUPPLY",
                    "high": candles[i-1]["high"],
                    "low": candles[i-1]["low"],
                    "index": i - 1,
                    "age": len(candles) - 1 - i,
                    "strength": min(100, int(body_curr / avg_body * 25)),
                    "tested": False
                }
                for j in range(i + 1, len(candles)):
                    if candles[j]["high"] >= zone["low"]:
                        zone["tested"] = True
                        break
                
                if zone["age"] <= 40 and not zone["tested"]:
                    supply_zones.append(zone)
        
        # Sort by strength
        supply_zones.sort(key=lambda x: -x["strength"])
        demand_zones.sort(key=lambda x: -x["strength"])
        
        return {
            "supply": supply_zones[:3],
            "demand": demand_zones[:3]
        }

    def _calculate_pivot_points(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Pivot Points from recent daily data.
        Uses standard pivot point formula:
        PP = (High + Low + Close) / 3
        """
        if len(candles) < 2:
            return {}
        
        # Use recent candle data as proxy for daily
        # (In real implementation, you'd use actual daily candles)
        recent = candles[-24:] if len(candles) >= 24 else candles
        
        period_high = max(c["high"] for c in recent)
        period_low = min(c["low"] for c in recent)
        period_close = candles[-1]["close"]
        
        # Pivot Point
        pp = (period_high + period_low + period_close) / 3
        
        # Resistance levels
        r1 = (2 * pp) - period_low
        r2 = pp + (period_high - period_low)
        r3 = period_high + 2 * (pp - period_low)
        
        # Support levels
        s1 = (2 * pp) - period_high
        s2 = pp - (period_high - period_low)
        s3 = period_low - 2 * (period_high - pp)
        
        current_price = candles[-1]["close"]
        
        # Determine position relative to pivot
        if current_price > r1:
            position = "ABOVE_R1"
        elif current_price > pp:
            position = "ABOVE_PP"
        elif current_price > s1:
            position = "BELOW_PP"
        else:
            position = "BELOW_S1"
        
        return {
            "pp": round(pp, 5),
            "r1": round(r1, 5),
            "r2": round(r2, 5),
            "r3": round(r3, 5),
            "s1": round(s1, 5),
            "s2": round(s2, 5),
            "s3": round(s3, 5),
            "position": position
        }

    def _determine_trend(self, swing_class: List[Dict]) -> str:
        """Determine overall trend from swing classifications"""
        if len(swing_class) < 4:
            return "NEUTRAL"
        
        recent = swing_class[-6:]
        
        hh_count = sum(1 for s in recent if s["label"] == "HH")
        hl_count = sum(1 for s in recent if s["label"] == "HL")
        lh_count = sum(1 for s in recent if s["label"] == "LH")
        ll_count = sum(1 for s in recent if s["label"] == "LL")
        
        bullish = hh_count + hl_count
        bearish = lh_count + ll_count
        
        if bullish >= 3 and bullish > bearish:
            return "STRONG_UPTREND"
        elif bearish >= 3 and bearish > bullish:
            return "STRONG_DOWNTREND"
        elif bullish > bearish:
            return "UPTREND"
        elif bearish > bullish:
            return "DOWNTREND"
        else:
            return "RANGING"


# Singleton
market_structure = MarketStructureAnalyzer()
