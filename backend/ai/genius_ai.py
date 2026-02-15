"""Genius AI - Comprehensive Trading Analysis & Signal Generation"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ai.rsi_calculator import rsi_calculator
from ai.macd_calculator import macd_calculator
from ai.ma_calculator import ma_calculator
from ai.sr_detector import sr_detector
from ai.pattern_recognition import pattern_recognition
from ai.multi_timeframe import mtf_analyzer
from ai.risk_manager import risk_manager
from ai.advanced_indicators import calculate_advanced_indicators
from ai.smart_money import smart_money
from ai.market_structure import market_structure
from ai.volume_analysis import volume_analyzer
from mt5.connector import connector
import logging

logger = logging.getLogger(__name__)


class GeniusAI:
    """
    Advanced AI Trading Analysis System
    Combines multiple analysis methods for high-accuracy signals
    """

    def __init__(self):
        self.min_confidence = 70
        self.min_risk_reward = 1.5

    def analyze(self, symbol: str, timeframe: str = "H1", risk_level: str = "moderate", custom_capital: float = None, risk_percentage: float = None) -> Dict[str, Any]:
        """
        Comprehensive AI Analysis for a trading opportunity

        Returns everything needed for a trading decision:
        - Market analysis
        - Entry/SL/TP prices
        - Position sizing
        - Risk assessment
        - Confidence score
        - Reasoning
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            risk_level: Risk level (conservative/moderate/aggressive)
            custom_capital: Optional custom capital to use instead of MT5 balance
        """
        result = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "status": "ANALYZING",
            "signal": None,
            "analysis": {},
            "setup": None,
            "recommendation": None
        }

        # 1. Get candles
        candles = connector.get_candles(symbol, timeframe, 200)
        if not candles or len(candles) < 50:
            result["status"] = "ERROR"
            result["error"] = "Insufficient data"
            return result

        # Get REAL-TIME current price from tick (not from candle close)
        # Use bid for SELL signals, ask for BUY signals (we'll use mid-price)
        bid_price = connector.get_tick_price(symbol, "bid")
        ask_price = connector.get_tick_price(symbol, "ask")
        if bid_price and ask_price:
            current_price = (bid_price + ask_price) / 2  # Mid-price
        elif bid_price:
            current_price = bid_price
        elif ask_price:
            current_price = ask_price
        else:
            # Fallback to candle close
            current_price = candles[-1]["close"]

        # 2. Technical Analysis
        tech_analysis = self._technical_analysis(candles)
        result["analysis"]["technical"] = tech_analysis

        # 3. Pattern Recognition - Candlestick & Chart Patterns
        try:
            patterns = pattern_recognition.detect_all_patterns(candles)
            result["analysis"]["patterns"] = {
                "bullish": [{"name": p["name"], "type": p["type"], "strength": p["strength"], "description": p.get("description", "")}
                               for p in patterns.get("bullish", [])],
                "bearish": [{"name": p["name"], "type": p["type"], "strength": p["strength"], "description": p.get("description", "")}
                               for p in patterns.get("bearish", [])],
                "neutral": patterns.get("neutral", []),
                "signals": patterns.get("signals", []),
                "total_bullish_strength": sum(p["strength"] for p in patterns.get("bullish", [])),
                "total_bearish_strength": sum(p["strength"] for p in patterns.get("bearish", []))
            }
        except Exception as e:
            logger.error(f"Pattern recognition error for {symbol}: {e}")
            result["analysis"]["patterns"] = None

        # 4. Multi-Timeframe Analysis - Trend Confluence
        try:
            mtf = mtf_analyzer.analyze_all_timeframes(symbol, timeframe)
            result["analysis"]["multi_timeframe"] = {
                "trend_direction": mtf["confluence"]["trend_direction"],
                "alignment_score": mtf["confluence"]["alignment_score"],
                "confidence": mtf["confluence"]["confidence"],
                "bullish_count": mtf["confluence"]["bullish_count"],
                "bearish_count": mtf["confluence"]["bearish_count"],
                "neutral_count": mtf["confluence"]["neutral_count"],
                "timeframes": {tf: {
                    "trend": data["trend"],
                    "signal_strength": data["signal_strength"],
                    "momentum": data.get("momentum", {}),
                    "price": data.get("price", 0),
                    "indicators": data.get("indicators", {}),
                    "candles_count": data.get("candles_count", 0)
                } for tf, data in mtf["timeframes"].items()},
                "patterns": mtf.get("patterns", {}),
                "key_levels": mtf.get("key_levels", {})
            }

            # 5. Session Analysis - Trading Session Quality
            session = mtf_analyzer.get_best_entry_time(symbol)
            result["analysis"]["session"] = session
        except Exception as e:
            logger.error(f"MTF/Session error for {symbol}: {e}")
            result["analysis"]["multi_timeframe"] = None
            result["analysis"]["session"] = None

        # 6. Advanced Indicators (Stochastic, Bollinger Bands, ADX, ATR)
        try:
            adv_indicators = calculate_advanced_indicators(candles)
            if adv_indicators:
                result["analysis"]["advanced_indicators"] = adv_indicators
            else:
                result["analysis"]["advanced_indicators"] = None
        except Exception as e:
            logger.warning(f"Advanced indicators error for {symbol}: {e}")
            result["analysis"]["advanced_indicators"] = {
                "error": f"Advanced indicators calculation failed: {str(e)}",
                "stochastic": None,
                "bollinger_bands": None,
                "adx": None,
                "atr": None
            }

        # 7. Smart Money Concepts (Order Blocks, FVG, BOS/CHoCH, Liquidity)
        try:
            smc = smart_money.analyze(candles)
            result["analysis"]["smart_money"] = smc
        except Exception as e:
            logger.warning(f"Smart Money analysis error for {symbol}: {e}")
            result["analysis"]["smart_money"] = None

        # 8. Market Structure (Swing HH/HL/LH/LL, Fibonacci, Supply/Demand)
        try:
            mkt_struct = market_structure.analyze(candles)
            result["analysis"]["market_structure"] = mkt_struct
        except Exception as e:
            logger.warning(f"Market structure error for {symbol}: {e}")
            result["analysis"]["market_structure"] = None

        # 9. Volume Analysis (VWAP, OBV, Volume Profile, Divergence)
        try:
            vol = volume_analyzer.analyze(candles)
            result["analysis"]["volume"] = vol
        except Exception as e:
            logger.warning(f"Volume analysis error for {symbol}: {e}")
            result["analysis"]["volume"] = None

        # 10. Calculate Overall Signal (Weighted Composite Scoring)
        signal = self._calculate_signal(
            tech_analysis,
            result["analysis"].get("patterns"),
            result["analysis"].get("multi_timeframe"),
            result["analysis"].get("session"),
            result["analysis"].get("advanced_indicators"),
            result["analysis"].get("smart_money"),
            result["analysis"].get("volume")
        )

        if not signal:
            result["status"] = "NO_SIGNAL"
            result["recommendation"] = "WAIT"
            return result

        result["signal"] = signal

        # 7. Get S/R Levels
        sr_levels = sr_detector.detect(candles)

        # 8. Calculate Optimal Setup (Entry, SL, TP, Lot Size)
        setup = risk_manager.get_optimal_setup(
            symbol=symbol,
            direction=signal["direction"],
            entry=current_price,
            support=sr_levels["support"][0] if sr_levels["support"] else None,
            resistance=sr_levels["resistance"][0] if sr_levels["resistance"] else None,
            account_risk_level=risk_level,
            risk_percentage=risk_percentage,
            confidence=signal["confidence"],
            custom_capital=custom_capital
        )

        if "error" in setup:
            result["status"] = "ERROR"
            result["error"] = setup["error"]
            return result

        result["setup"] = setup

        # 9. Market Context (volatility, spread, sessions) - NEW
        symbol_info = connector.get_symbol_info(symbol)
        current_prices = connector.get_current_price(symbol)

        session = result["analysis"].get("session")
        result["analysis"]["market_context"] = {
            "spread": current_prices.get("spread", 0) if current_prices else 0,
            "spread_pips": (current_prices.get("spread", 0) * 10000) if current_prices else 0,
            "point": symbol_info.get("point", 0) if symbol_info else 0,
            "digits": symbol_info.get("digits", 5) if symbol_info else 5,
            "session_quality": session.get("quality", "UNKNOWN") if session else "UNKNOWN",
            "is_best_time": session.get("is_best_time", False) if session else False,
            "active_sessions": session.get("active_sessions", []) if session else []
        }

        # 10. Account Data (if custom capital not used) - NEW
        if custom_capital is None:
            account = connector.get_account_info()
            if account:
                result["analysis"]["account"] = {
                    "balance": account.get("balance", 0),
                    "equity": account.get("equity", 0),
                    "free_margin": account.get("free_margin", 0),
                    "margin": account.get("margin", 0),
                    "leverage": account.get("leverage", 0),
                    "profit": account.get("profit", 0),
                    "drawdown_pct": ((account["balance"] - account["equity"]) / account["balance"] * 100) if account.get("balance", 0) > 0 else 0
                }

        # 11. Final Recommendation
        if signal["confidence"] >= 80 and setup["risk_reward"] >= 2:
            recommendation = "STRONG_BUY" if signal["direction"] == "BUY" else "STRONG_SELL"
        elif signal["confidence"] >= 70 and setup["risk_reward"] >= 1.5:
            recommendation = "BUY" if signal["direction"] == "BUY" else "SELL"
        elif signal["confidence"] >= 60:
            recommendation = "CAUTIOUS_BUY" if signal["direction"] == "BUY" else "CAUTIOUS_SELL"
        else:
            recommendation = "WAIT"

        result["recommendation"] = recommendation
        result["status"] = "READY"

        # DEBUG: Log type information (safe for numpy types)
        try:
            logger.info(f"Final result keys: {list(result.keys())}")
            logger.info(f"Analysis keys: {list(result.get('analysis', {}).keys())}")
        except Exception as e:
            logger.error(f"Error logging debug info: {e}")

        return result

    def _technical_analysis(self, candles: List[Dict]) -> Dict[str, Any]:
        """Perform technical indicator analysis"""
        rsi_values = rsi_calculator.calculate(candles)
        macd_data = macd_calculator.calculate(candles)
        ma_data = ma_calculator.calculate(candles)
        sr_levels = sr_detector.detect(candles)

        current_price = candles[-1]["close"]

        # RSI Analysis
        rsi = rsi_values[-1] if rsi_values else 50
        rsi_status = "NEUTRAL"
        if rsi < 30:
            rsi_status = "OVERSOLD"
        elif rsi > 70:
            rsi_status = "OVERBOUGHT"
        elif rsi < 40:
            rsi_status = "BEARISH"
        elif rsi > 60:
            rsi_status = "BULLISH"

        # MACD Analysis
        macd = macd_data["macd"][-1] if macd_data["macd"] else 0
        signal_line = macd_data["signal"][-1] if macd_data["signal"] else 0
        histogram = macd_data["histogram"][-1] if macd_data["histogram"] else 0

        # MACD Analysis (explicit boolean conversion)
        macd_status = "BULLISH" if bool(histogram > 0) else "BEARISH"
        bull_cross = bool(macd > signal_line and len(macd_data["histogram"]) > 1 and macd_data["histogram"][-2] < 0)
        bear_cross = bool(macd < signal_line and len(macd_data["histogram"]) > 1 and macd_data["histogram"][-2] > 0)
        macd_crossover = "BULLISH_CROSS" if bull_cross else "BEARISH_CROSS" if bear_cross else "NONE"

        # EMA Analysis
        ema9 = ma_data["ema_9"][-1] if ma_data["ema_9"] else current_price
        ema21 = ma_data["ema_21"][-1] if ma_data["ema_21"] else current_price
        ema50 = ma_data["ema_50"][-1] if ma_data["ema_50"] else current_price

        # EMA Analysis (explicit comparison to avoid numpy boolean issues)
        ema_bullish = bool(ema9 > ema21 and ema21 > ema50)
        ema_bearish = bool(ema9 < ema21 and ema21 < ema50)
        ema_trend = "BULLISH" if ema_bullish else "BEARISH" if ema_bearish else "NEUTRAL"
        price_vs_ema = "ABOVE" if current_price > ema21 else "BELOW"

        # Divergence
        divergence = rsi_calculator.is_divergence(candles[-50:], 0.05)

        return {
            "rsi": {"value": round(rsi, 2), "status": rsi_status},
            "macd": {"histogram": round(histogram, 6), "status": macd_status, "crossover": macd_crossover},
            "ema": {"trend": ema_trend, "price_position": price_vs_ema, "ema9": round(ema9, 5), "ema21": round(ema21, 5), "ema50": round(ema50, 5)},
            "divergence": divergence,
            "support_resistance": sr_levels,
            "current_price": current_price
        }

    def _calculate_signal(self, tech: Dict, patterns: Dict, mtf: Dict, session: Dict, adv: Dict = None, smc: Dict = None, vol: Dict = None) -> Optional[Dict]:
        """
        Weighted Composite Scoring System for trading signals.
        
        Weight Distribution (with SMC & Volume):
        - Multi-Timeframe Confluence: 25% (institutions trade HTF direction)
        - Technical Indicators:       20% (RSI, MACD, EMA, Stochastic, ADX)
        - Smart Money Concepts:       15% (Order Blocks, FVG, BOS/CHoCH)
        - Pattern Recognition:        15% (candlestick + chart patterns)
        - Volume Analysis:            10% (VWAP, OBV, divergence)
        - Support/Resistance:         10% (proximity to key levels)
        - Session/Timing:              5% (market quality filter)
        
        Max score per category = 100, final = weighted average
        """
        reasons = []
        
        # ============================================
        # Category 1: Technical Indicators (weight 25%)
        # ============================================
        tech_bull = 0
        tech_bear = 0
        tech_max = 100
        
        # RSI (max 25 points)
        rsi = tech["rsi"]["value"]
        if tech["rsi"]["status"] == "OVERSOLD":
            tech_bull += 25
            reasons.append(f"RSI Oversold ({rsi:.1f})")
        elif tech["rsi"]["status"] == "OVERBOUGHT":
            tech_bear += 25
            reasons.append(f"RSI Overbought ({rsi:.1f})")
        elif rsi > 55:
            tech_bull += 8
        elif rsi < 45:
            tech_bear += 8
        
        # MACD (max 25 points)
        if tech["macd"]["crossover"] == "BULLISH_CROSS":
            tech_bull += 25
            reasons.append("MACD Bullish Crossover")
        elif tech["macd"]["crossover"] == "BEARISH_CROSS":
            tech_bear += 25
            reasons.append("MACD Bearish Crossover")
        elif tech["macd"]["status"] == "BULLISH":
            tech_bull += 12
        else:
            tech_bear += 12
        
        # EMA (max 25 points)
        if tech["ema"]["trend"] == "BULLISH":
            tech_bull += 25
            reasons.append("EMA Bullish Alignment")
        elif tech["ema"]["trend"] == "BEARISH":
            tech_bear += 25
            reasons.append("EMA Bearish Alignment")
        
        # Divergence (max 25 points - very strong signal)
        if tech["divergence"] == "BULLISH":
            tech_bull += 25
            reasons.append("Bullish Divergence")
        elif tech["divergence"] == "BEARISH":
            tech_bear += 25
            reasons.append("Bearish Divergence")
        
        # === Advanced Indicators Bonus (Stochastic, BB, ADX) ===
        if adv:
            # Stochastic (max 15 points)
            stoch = adv.get("stochastic")
            if stoch:
                if stoch.get("crossover") == "BULLISH_CROSS":
                    tech_bull += 15
                    reasons.append(f"Stochastic Bullish Cross ({stoch['k_value']:.0f})")
                elif stoch.get("crossover") == "BEARISH_CROSS":
                    tech_bear += 15
                    reasons.append(f"Stochastic Bearish Cross ({stoch['k_value']:.0f})")
                elif stoch.get("status") == "OVERSOLD":
                    tech_bull += 10
                elif stoch.get("status") == "OVERBOUGHT":
                    tech_bear += 10
            
            # Bollinger Bands (max 15 points)
            bb = adv.get("bollinger_bands")
            if bb:
                if bb.get("position") == "BELOW_LOWER":
                    tech_bull += 15
                    reasons.append("Price Below Lower BB (Oversold)")
                elif bb.get("position") == "ABOVE_UPPER":
                    tech_bear += 15
                    reasons.append("Price Above Upper BB (Overbought)")
                elif bb.get("squeeze"):
                    reasons.append("BB Squeeze - Breakout Imminent")
            
            # ADX - Trend Strength Filter (max 15 points)
            adx_data = adv.get("adx")
            if adx_data:
                adx_val = adx_data.get("adx", 0)
                if adx_val > 25:  # Strong trend
                    if adx_data.get("direction") == "BULLISH":
                        tech_bull += 15
                        reasons.append(f"ADX Strong Bullish Trend ({adx_val:.0f})")
                    elif adx_data.get("direction") == "BEARISH":
                        tech_bear += 15
                        reasons.append(f"ADX Strong Bearish Trend ({adx_val:.0f})")
                elif adx_val < 15:  # No trend - reduce confidence
                    tech_bull = int(tech_bull * 0.7)
                    tech_bear = int(tech_bear * 0.7)
            
            tech_max = 145  # Extended max with advanced indicators
        
        tech_bull_pct = min(100, tech_bull / tech_max * 100)
        tech_bear_pct = min(100, tech_bear / tech_max * 100)
        
        # ============================================
        # Category 2: Multi-Timeframe Confluence (weight 30%)
        # ============================================
        mtf_bull_pct = 0
        mtf_bear_pct = 0
        
        if mtf:
            # MTF data may be at top level or under "confluence" sub-key
            confluence = mtf.get("confluence", {})
            alignment = confluence.get("alignment_score", 0) or mtf.get("alignment_score", 0)
            direction = confluence.get("trend_direction", "") or mtf.get("trend_direction", "NEUTRAL")
            
            if direction == "BULLISH":
                mtf_bull_pct = min(100, alignment)
                reasons.append(f"MTF Bullish Confluence ({alignment:.0f}%)")
            elif direction == "BEARISH":
                mtf_bear_pct = min(100, alignment)
                reasons.append(f"MTF Bearish Confluence ({alignment:.0f}%)")
            elif direction == "MIXED":
                # Mixed signal reduces both scores
                mtf_bull_pct = 30
                mtf_bear_pct = 30
        
        # ============================================
        # Category 3: Pattern Recognition (weight 20%)
        # ============================================
        pat_bull_pct = 0
        pat_bear_pct = 0
        
        if patterns:
            bullish_patterns = patterns.get("bullish", [])
            bearish_patterns = patterns.get("bearish", [])
            
            if bullish_patterns:
                total_strength = sum(p["strength"] for p in bullish_patterns)
                # Cap at 100, normalize by considering typical pattern strength (60-90)
                pat_bull_pct = min(100, total_strength / max(len(bullish_patterns), 1))
                for p in bullish_patterns[:2]:  # Top 2 patterns
                    reasons.append(f"Pattern: {p['name']} ({p['strength']}%)")
            
            if bearish_patterns:
                total_strength = sum(p["strength"] for p in bearish_patterns)
                pat_bear_pct = min(100, total_strength / max(len(bearish_patterns), 1))
                for p in bearish_patterns[:2]:
                    reasons.append(f"Pattern: {p['name']} ({p['strength']}%)")
        
        # ============================================
        # Category 4: Support/Resistance Proximity (weight 15%)
        # ============================================
        sr_bull_pct = 50  # Neutral by default
        sr_bear_pct = 50
        
        sr = tech.get("support_resistance", {})
        if sr:
            support_levels = sr.get("support", [])
            resistance_levels = sr.get("resistance", [])
            current_price = tech.get("ema", {}).get("current_price", 0)
            
            if current_price > 0:
                # Near support = bullish, near resistance = bearish
                if support_levels:
                    nearest_support = min(support_levels, key=lambda x: abs(x - current_price)) if isinstance(support_levels[0], (int, float)) else support_levels[0]
                    if isinstance(nearest_support, (int, float)):
                        dist_to_support = abs(current_price - nearest_support) / current_price * 100
                        if dist_to_support < 0.3:  # Within 0.3% of support
                            sr_bull_pct = 85
                            reasons.append("Near Strong Support")
                
                if resistance_levels:
                    nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price)) if isinstance(resistance_levels[0], (int, float)) else resistance_levels[0]
                    if isinstance(nearest_resistance, (int, float)):
                        dist_to_resistance = abs(nearest_resistance - current_price) / current_price * 100
                        if dist_to_resistance < 0.3:  # Within 0.3% of resistance
                            sr_bear_pct = 85
                            reasons.append("Near Strong Resistance")
        
        # ============================================
        # Category 5: Session Quality (weight 10%)
        # ============================================
        session_multiplier = 1.0
        
        if session:
            quality = session.get("quality", "MEDIUM")
            if quality == "HIGH":
                session_multiplier = 1.15  # Boost during best sessions
                reasons.append("High Quality Session")
            elif quality == "LOW":
                session_multiplier = 0.7   # Penalize low-quality sessions
                reasons.append("⚠ Low Quality Session")
        
        # ============================================
        # Category 6: Smart Money Concepts (weight 15%)
        # ============================================
        smc_bull_pct = 0
        smc_bear_pct = 0
        
        if smc and smc.get("score"):
            smc_score = smc["score"]
            smc_bull_pct = smc_score.get("bullish", 0)
            smc_bear_pct = smc_score.get("bearish", 0)
            
            for reason in smc_score.get("reasons", [])[:2]:
                reasons.append(f"SMC: {reason}")
        
        # ============================================
        # Category 7: Volume Analysis (weight 10%)
        # ============================================
        vol_bull_pct = 50  # Neutral default
        vol_bear_pct = 50
        
        if vol and vol.get("score"):
            vol_score = vol["score"]
            vol_bull_pct = vol_score.get("bullish", 50)
            vol_bear_pct = vol_score.get("bearish", 50)
            
            for reason in vol_score.get("reasons", [])[:1]:
                reasons.append(f"Vol: {reason}")
        
        # ============================================
        # Final Weighted Composite Score
        # ============================================
        weights = {
            "mtf": 0.25,      # Multi-timeframe is king
            "tech": 0.20,     # Technical indicators
            "smc": 0.15,      # Smart Money Concepts
            "patterns": 0.15, # Pattern recognition
            "volume": 0.10,   # Volume analysis
            "sr": 0.10,       # Support/resistance
            "session": 0.05   # Session quality
        }
        
        bullish_score = (
            mtf_bull_pct * weights["mtf"] +
            tech_bull_pct * weights["tech"] +
            smc_bull_pct * weights["smc"] +
            pat_bull_pct * weights["patterns"] +
            vol_bull_pct * weights["volume"] +
            sr_bull_pct * weights["sr"]
        )
        bearish_score = (
            mtf_bear_pct * weights["mtf"] +
            tech_bear_pct * weights["tech"] +
            smc_bear_pct * weights["smc"] +
            pat_bear_pct * weights["patterns"] +
            vol_bear_pct * weights["volume"] +
            sr_bear_pct * weights["sr"]
        )
        
        # Apply session multiplier
        bullish_score *= session_multiplier
        bearish_score *= session_multiplier
        
        # Minimum threshold: need at least 45% composite score 
        # and meaningful difference between bull/bear
        min_threshold = 45
        min_diff = 10  # Minimum 10% difference to avoid noise
        
        score_diff = abs(bullish_score - bearish_score)
        
        if bullish_score > bearish_score and bullish_score >= min_threshold and score_diff >= min_diff:
            direction = "BUY"
            confidence = min(95, bullish_score)
        elif bearish_score > bullish_score and bearish_score >= min_threshold and score_diff >= min_diff:
            direction = "SELL"
            confidence = min(95, bearish_score)
        else:
            return None
        
        return {
            "direction": direction,
            "confidence": round(confidence, 1),
            "bullish_score": round(bullish_score, 1),
            "bearish_score": round(bearish_score, 1),
            "score_breakdown": {
                "mtf": round(mtf_bull_pct if direction == "BUY" else mtf_bear_pct, 1),
                "technical": round(tech_bull_pct if direction == "BUY" else tech_bear_pct, 1),
                "smart_money": round(smc_bull_pct if direction == "BUY" else smc_bear_pct, 1),
                "patterns": round(pat_bull_pct if direction == "BUY" else pat_bear_pct, 1),
                "volume": round(vol_bull_pct if direction == "BUY" else vol_bear_pct, 1),
                "sr_proximity": round(sr_bull_pct if direction == "BUY" else sr_bear_pct, 1),
                "session_quality": round(session_multiplier * 100, 0)
            },
            "reasons": reasons[:8]  # Top 8 reasons
        }


# Singleton
genius_ai = GeniusAI()