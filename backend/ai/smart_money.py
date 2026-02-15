"""
Smart Money Concepts (SMC) - Institutional Trading Analysis

Detects institutional footprints in price action:
- Order Blocks (OB): Where banks placed large orders
- Fair Value Gaps (FVG): Price imbalance zones
- Break of Structure (BOS): Trend continuation confirmation
- Change of Character (CHoCH): Early reversal detection
- Liquidity Sweeps: Stop-hunt detection
- Premium/Discount Zones: Optimal entry zones
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SmartMoneyAnalyzer:
    """Analyze price action using Smart Money Concepts"""

    def __init__(self):
        self.swing_lookback = 5  # Candles to look back for swing detection
        self.ob_max_age = 50     # Max candles old for valid order block
        self.fvg_min_gap = 0.0001  # Minimum gap size for FVG (in price)

    def analyze(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete SMC analysis on candle data.
        
        Returns:
            Dictionary with all SMC components and a composite score
        """
        if len(candles) < 30:
            return {
                "order_blocks": [], "fair_value_gaps": [],
                "structure": {"bos": [], "choch": [], "trend": "NEUTRAL"},
                "liquidity": {"sweeps": [], "equal_highs": [], "equal_lows": []},
                "zones": {"premium_discount": "NEUTRAL"},
                "score": {"bullish": 0, "bearish": 0}
            }

        try:
            # 1. Detect swing points (foundation for everything else)
            swings = self._detect_swings(candles)
            
            # 2. Market Structure (BOS/CHoCH)
            structure = self._analyze_structure(candles, swings)
            
            # 3. Order Blocks
            order_blocks = self._detect_order_blocks(candles, structure)
            
            # 4. Fair Value Gaps
            fvgs = self._detect_fair_value_gaps(candles)
            
            # 5. Liquidity Analysis
            liquidity = self._analyze_liquidity(candles, swings)
            
            # 6. Premium/Discount Zones
            zones = self._calculate_premium_discount(candles, swings)
            
            # 7. Composite SMC Score
            score = self._calculate_smc_score(
                candles, order_blocks, fvgs, structure, liquidity, zones
            )
            
            return {
                "order_blocks": order_blocks,
                "fair_value_gaps": fvgs,
                "structure": structure,
                "liquidity": liquidity,
                "zones": zones,
                "score": score,
                "swings": {
                    "highs": [{"index": s["index"], "price": s["price"]} for s in swings if s["type"] == "high"][-5:],
                    "lows": [{"index": s["index"], "price": s["price"]} for s in swings if s["type"] == "low"][-5:]
                }
            }
        except Exception as e:
            logger.error(f"SMC analysis error: {e}")
            return {
                "order_blocks": [], "fair_value_gaps": [],
                "structure": {"bos": [], "choch": [], "trend": "NEUTRAL"},
                "liquidity": {"sweeps": [], "equal_highs": [], "equal_lows": []},
                "zones": {"premium_discount": "NEUTRAL"},
                "score": {"bullish": 0, "bearish": 0}
            }

    # =========================================
    # 1. Swing Point Detection
    # =========================================
    def _detect_swings(self, candles: List[Dict]) -> List[Dict]:
        """Detect swing highs and swing lows"""
        swings = []
        lookback = self.swing_lookback

        for i in range(lookback, len(candles) - lookback):
            high = candles[i]["high"]
            low = candles[i]["low"]

            # Check for swing high
            is_swing_high = all(
                candles[i]["high"] >= candles[j]["high"]
                for j in range(i - lookback, i + lookback + 1) if j != i
            )
            if is_swing_high:
                swings.append({
                    "type": "high",
                    "index": i,
                    "price": high,
                    "time": candles[i].get("time", "")
                })

            # Check for swing low
            is_swing_low = all(
                candles[i]["low"] <= candles[j]["low"]
                for j in range(i - lookback, i + lookback + 1) if j != i
            )
            if is_swing_low:
                swings.append({
                    "type": "low",
                    "index": i,
                    "price": low,
                    "time": candles[i].get("time", "")
                })

        return sorted(swings, key=lambda x: x["index"])

    # =========================================
    # 2. Market Structure Analysis (BOS/CHoCH)
    # =========================================
    def _analyze_structure(self, candles: List[Dict], swings: List[Dict]) -> Dict[str, Any]:
        """
        Analyze market structure:
        - BOS (Break of Structure): Continuation signal
        - CHoCH (Change of Character): Reversal signal
        """
        bos_list = []
        choch_list = []
        
        swing_highs = [s for s in swings if s["type"] == "high"]
        swing_lows = [s for s in swings if s["type"] == "low"]

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {"bos": [], "choch": [], "trend": "NEUTRAL", "last_break": None}

        # Determine current trend from swing sequence
        trend = "NEUTRAL"
        last_break = None
        
        # Check last few swing highs/lows for structure
        for i in range(1, min(len(swing_highs), 5)):
            prev_h = swing_highs[-i - 1]
            curr_h = swing_highs[-i]
            
            # Higher High
            if curr_h["price"] > prev_h["price"]:
                trend = "BULLISH"
            # Lower High
            elif curr_h["price"] < prev_h["price"]:
                if trend == "BULLISH":
                    # Change of character: was bullish, now making lower highs
                    choch_list.append({
                        "type": "BEARISH_CHOCH",
                        "price": curr_h["price"],
                        "index": curr_h["index"],
                        "description": f"Lower High at {curr_h['price']:.5f} - potential reversal"
                    })
                    trend = "BEARISH"
                    last_break = {"type": "BEARISH_CHOCH", "price": curr_h["price"]}
                else:
                    bos_list.append({
                        "type": "BEARISH_BOS",
                        "price": curr_h["price"],
                        "index": curr_h["index"],
                        "description": f"Break of Structure bearish at {curr_h['price']:.5f}"
                    })

        for i in range(1, min(len(swing_lows), 5)):
            prev_l = swing_lows[-i - 1]
            curr_l = swing_lows[-i]
            
            # Higher Low
            if curr_l["price"] > prev_l["price"]:
                if trend == "BEARISH":
                    choch_list.append({
                        "type": "BULLISH_CHOCH",
                        "price": curr_l["price"],
                        "index": curr_l["index"],
                        "description": f"Higher Low at {curr_l['price']:.5f} - potential reversal"
                    })
                    trend = "BULLISH"
                    last_break = {"type": "BULLISH_CHOCH", "price": curr_l["price"]}
                else:
                    bos_list.append({
                        "type": "BULLISH_BOS",
                        "price": curr_l["price"],
                        "index": curr_l["index"],
                        "description": f"Break of Structure bullish at {curr_l['price']:.5f}"
                    })
            # Lower Low
            elif curr_l["price"] < prev_l["price"]:
                trend = "BEARISH"

        return {
            "bos": bos_list[-3:],    # Last 3 BOS
            "choch": choch_list[-2:], # Last 2 CHoCH
            "trend": trend,
            "last_break": last_break
        }

    # =========================================
    # 3. Order Block Detection
    # =========================================
    def _detect_order_blocks(self, candles: List[Dict], structure: Dict) -> List[Dict]:
        """
        Detect Order Blocks - last opposing candle before a strong move.
        
        Bullish OB: Last bearish candle before a strong bullish move
        Bearish OB: Last bullish candle before a strong bearish move
        """
        order_blocks = []
        current_price = candles[-1]["close"]

        for i in range(2, len(candles) - 1):
            # Calculate move size
            body_prev = abs(candles[i-1]["close"] - candles[i-1]["open"])
            body_curr = abs(candles[i]["close"] - candles[i]["open"])
            avg_body = np.mean([abs(c["close"] - c["open"]) for c in candles[max(0,i-10):i]])
            
            if avg_body == 0:
                continue
            
            # Strong move = body > 2x average
            is_strong_move = body_curr > avg_body * 2

            if not is_strong_move:
                continue

            # Bullish Order Block: bearish candle followed by strong bullish move
            if (candles[i-1]["close"] < candles[i-1]["open"] and  # Previous was bearish
                candles[i]["close"] > candles[i]["open"]):          # Current is bullish
                
                ob = {
                    "type": "BULLISH",
                    "high": candles[i-1]["high"],
                    "low": candles[i-1]["low"],
                    "index": i - 1,
                    "age": len(candles) - 1 - (i - 1),
                    "mitigated": current_price < candles[i-1]["low"],  # Price went through
                    "strength": min(100, int(body_curr / avg_body * 30))
                }
                
                # Only add if not too old and not mitigated
                if ob["age"] <= self.ob_max_age and not ob["mitigated"]:
                    order_blocks.append(ob)

            # Bearish Order Block: bullish candle followed by strong bearish move
            elif (candles[i-1]["close"] > candles[i-1]["open"] and  # Previous was bullish
                  candles[i]["close"] < candles[i]["open"]):          # Current is bearish
                
                ob = {
                    "type": "BEARISH",
                    "high": candles[i-1]["high"],
                    "low": candles[i-1]["low"],
                    "index": i - 1,
                    "age": len(candles) - 1 - (i - 1),
                    "mitigated": current_price > candles[i-1]["high"],
                    "strength": min(100, int(body_curr / avg_body * 30))
                }
                
                if ob["age"] <= self.ob_max_age and not ob["mitigated"]:
                    order_blocks.append(ob)

        # Return most recent, strongest order blocks
        order_blocks.sort(key=lambda x: (-x["strength"], x["age"]))
        return order_blocks[:5]

    # =========================================
    # 4. Fair Value Gap (FVG) Detection
    # =========================================
    def _detect_fair_value_gaps(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVG) - 3-candle imbalance zones.
        
        Bullish FVG: Candle 3 low > Candle 1 high (gap up)
        Bearish FVG: Candle 1 low > Candle 3 high (gap down)
        """
        fvgs = []
        current_price = candles[-1]["close"]

        for i in range(2, len(candles)):
            c1 = candles[i - 2]  # First candle
            c3 = candles[i]      # Third candle

            # Bullish FVG: gap between candle 1 high and candle 3 low
            if c3["low"] > c1["high"]:
                gap_size = c3["low"] - c1["high"]
                if gap_size > self.fvg_min_gap:
                    fvg = {
                        "type": "BULLISH",
                        "top": c3["low"],
                        "bottom": c1["high"],
                        "mid": (c3["low"] + c1["high"]) / 2,
                        "size": gap_size,
                        "index": i - 1,
                        "age": len(candles) - 1 - i,
                        "filled": current_price <= c1["high"],  # Price filled gap
                    }
                    if not fvg["filled"] and fvg["age"] <= 30:
                        fvgs.append(fvg)

            # Bearish FVG: gap between candle 1 low and candle 3 high
            elif c1["low"] > c3["high"]:
                gap_size = c1["low"] - c3["high"]
                if gap_size > self.fvg_min_gap:
                    fvg = {
                        "type": "BEARISH",
                        "top": c1["low"],
                        "bottom": c3["high"],
                        "mid": (c1["low"] + c3["high"]) / 2,
                        "size": gap_size,
                        "index": i - 1,
                        "age": len(candles) - 1 - i,
                        "filled": current_price >= c1["low"],
                    }
                    if not fvg["filled"] and fvg["age"] <= 30:
                        fvgs.append(fvg)

        # Return most recent FVGs
        fvgs.sort(key=lambda x: x["age"])
        return fvgs[:5]

    # =========================================
    # 5. Liquidity Analysis
    # =========================================
    def _analyze_liquidity(self, candles: List[Dict], swings: List[Dict]) -> Dict[str, Any]:
        """
        Analyze liquidity pools and sweeps.
        
        - Equal Highs/Lows: Clusters of similar price levels = liquidity pools
        - Liquidity Sweeps: When price takes out a level then reverses
        """
        sweeps = []
        equal_highs = []
        equal_lows = []
        
        swing_highs = [s for s in swings if s["type"] == "high"]
        swing_lows = [s for s in swings if s["type"] == "low"]
        
        # Find equal highs (within 0.05% of each other)
        tolerance = 0.0005
        for i in range(len(swing_highs)):
            for j in range(i + 1, len(swing_highs)):
                diff_pct = abs(swing_highs[i]["price"] - swing_highs[j]["price"]) / swing_highs[i]["price"]
                if diff_pct < tolerance:
                    avg_price = (swing_highs[i]["price"] + swing_highs[j]["price"]) / 2
                    if not any(abs(eh["price"] - avg_price) / avg_price < tolerance for eh in equal_highs):
                        equal_highs.append({
                            "price": round(avg_price, 5),
                            "count": 2,
                            "description": f"Equal Highs at {avg_price:.5f} - liquidity above"
                        })
        
        # Find equal lows
        for i in range(len(swing_lows)):
            for j in range(i + 1, len(swing_lows)):
                diff_pct = abs(swing_lows[i]["price"] - swing_lows[j]["price"]) / swing_lows[i]["price"]
                if diff_pct < tolerance:
                    avg_price = (swing_lows[i]["price"] + swing_lows[j]["price"]) / 2
                    if not any(abs(el["price"] - avg_price) / avg_price < tolerance for el in equal_lows):
                        equal_lows.append({
                            "price": round(avg_price, 5),
                            "count": 2,
                            "description": f"Equal Lows at {avg_price:.5f} - liquidity below"
                        })
        
        # Detect liquidity sweeps (price takes a level then reverses)
        current_price = candles[-1]["close"]
        for i in range(max(0, len(candles) - 10), len(candles)):
            candle = candles[i]
            
            # Check if any recent candle swept above equal highs then closed below
            for eh in equal_highs:
                if candle["high"] > eh["price"] and candle["close"] < eh["price"]:
                    sweeps.append({
                        "type": "BEARISH_SWEEP",
                        "level": eh["price"],
                        "high": candle["high"],
                        "close": candle["close"],
                        "index": i,
                        "description": f"Liquidity sweep above {eh['price']:.5f} - bearish signal"
                    })
            
            # Check if any recent candle swept below equal lows then closed above
            for el in equal_lows:
                if candle["low"] < el["price"] and candle["close"] > el["price"]:
                    sweeps.append({
                        "type": "BULLISH_SWEEP",
                        "level": el["price"],
                        "low": candle["low"],
                        "close": candle["close"],
                        "index": i,
                        "description": f"Liquidity sweep below {el['price']:.5f} - bullish signal"
                    })

        return {
            "sweeps": sweeps[-3:],
            "equal_highs": equal_highs[:3],
            "equal_lows": equal_lows[:3]
        }

    # =========================================
    # 6. Premium/Discount Zones
    # =========================================
    def _calculate_premium_discount(self, candles: List[Dict], swings: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Premium/Discount zones based on recent swing range.
        
        - Premium Zone (above 50%): Sell zone
        - Discount Zone (below 50%): Buy zone
        - Equilibrium (around 50%): Neutral
        """
        swing_highs = [s for s in swings if s["type"] == "high"]
        swing_lows = [s for s in swings if s["type"] == "low"]

        if not swing_highs or not swing_lows:
            return {"premium_discount": "NEUTRAL", "position_pct": 50}

        # Use the most recent significant swing range
        recent_high = max(s["price"] for s in swing_highs[-3:])
        recent_low = min(s["price"] for s in swing_lows[-3:])
        
        if recent_high == recent_low:
            return {"premium_discount": "NEUTRAL", "position_pct": 50}

        current_price = candles[-1]["close"]
        range_size = recent_high - recent_low
        position_pct = ((current_price - recent_low) / range_size) * 100

        if position_pct > 70:
            zone = "PREMIUM"
            description = "Price in premium zone - look for SELL setups"
        elif position_pct < 30:
            zone = "DISCOUNT"
            description = "Price in discount zone - look for BUY setups"
        elif 40 <= position_pct <= 60:
            zone = "EQUILIBRIUM"
            description = "Price at equilibrium - wait for direction"
        else:
            zone = "NEUTRAL"
            description = "Price in neutral zone"

        return {
            "premium_discount": zone,
            "position_pct": round(position_pct, 1),
            "range_high": round(recent_high, 5),
            "range_low": round(recent_low, 5),
            "equilibrium": round((recent_high + recent_low) / 2, 5),
            "description": description
        }

    # =========================================
    # 7. Composite SMC Score
    # =========================================
    def _calculate_smc_score(
        self, candles: List[Dict], order_blocks: List,
        fvgs: List, structure: Dict, liquidity: Dict, zones: Dict
    ) -> Dict[str, Any]:
        """Calculate composite Smart Money score"""
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        current_price = candles[-1]["close"]
        
        # 1. Market Structure (weight: 35%)
        trend = structure.get("trend", "NEUTRAL")
        if trend == "BULLISH":
            bullish_score += 35
            reasons.append("Market structure BULLISH")
        elif trend == "BEARISH":
            bearish_score += 35
            reasons.append("Market structure BEARISH")
        
        # CHoCH is stronger signal than BOS
        for choch in structure.get("choch", []):
            if "BULLISH" in choch["type"]:
                bullish_score += 15
                reasons.append(choch["description"])
            elif "BEARISH" in choch["type"]:
                bearish_score += 15
                reasons.append(choch["description"])
        
        # 2. Order Blocks proximity (weight: 25%)
        for ob in order_blocks[:2]:  # Check top 2
            if ob["type"] == "BULLISH":
                # Price near bullish OB = buy signal
                dist = abs(current_price - ob["low"]) / current_price * 100
                if dist < 0.5:  # Within 0.5%
                    bullish_score += 25
                    reasons.append(f"Near Bullish OB ({ob['low']:.5f})")
                elif dist < 1.0:
                    bullish_score += 12
            elif ob["type"] == "BEARISH":
                dist = abs(current_price - ob["high"]) / current_price * 100
                if dist < 0.5:
                    bearish_score += 25
                    reasons.append(f"Near Bearish OB ({ob['high']:.5f})")
                elif dist < 1.0:
                    bearish_score += 12
        
        # 3. FVG proximity (weight: 15%)
        for fvg in fvgs[:2]:
            dist = abs(current_price - fvg["mid"]) / current_price * 100
            if dist < 0.5:
                if fvg["type"] == "BULLISH":
                    bullish_score += 15
                    reasons.append(f"Near Bullish FVG ({fvg['mid']:.5f})")
                elif fvg["type"] == "BEARISH":
                    bearish_score += 15
                    reasons.append(f"Near Bearish FVG ({fvg['mid']:.5f})")
        
        # 4. Liquidity sweeps (weight: 15%)
        for sweep in liquidity.get("sweeps", []):
            if sweep["type"] == "BULLISH_SWEEP":
                bullish_score += 15
                reasons.append(sweep["description"])
            elif sweep["type"] == "BEARISH_SWEEP":
                bearish_score += 15
                reasons.append(sweep["description"])
        
        # 5. Premium/Discount (weight: 10%)
        pd_zone = zones.get("premium_discount", "NEUTRAL")
        if pd_zone == "DISCOUNT":
            bullish_score += 10
            reasons.append("Price in Discount Zone")
        elif pd_zone == "PREMIUM":
            bearish_score += 10
            reasons.append("Price in Premium Zone")
        
        return {
            "bullish": min(100, bullish_score),
            "bearish": min(100, bearish_score),
            "bias": "BULLISH" if bullish_score > bearish_score + 10 else "BEARISH" if bearish_score > bullish_score + 10 else "NEUTRAL",
            "reasons": reasons[:5]
        }


# Singleton
smart_money = SmartMoneyAnalyzer()
