"""
Volume Analysis - VWAP, OBV, Volume Profile, Volume Divergence

Institutional-grade volume analysis:
- VWAP (Volume Weighted Average Price)
- OBV (On Balance Volume)
- Volume Profile (POC, VAH, VAL)
- Volume Divergence detection
"""
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VolumeAnalyzer:
    """Analyze volume for institutional trading insights"""

    def analyze(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete volume analysis"""
        if len(candles) < 20:
            return {
                "vwap": None, "obv": None,
                "volume_profile": None, "divergence": None,
                "score": {"bullish": 0, "bearish": 0}
            }

        try:
            # Check if volume data is available
            has_volume = any(c.get("tick_volume", 0) > 0 or c.get("volume", 0) > 0 for c in candles)
            
            if not has_volume:
                return {
                    "vwap": None, "obv": None,
                    "volume_profile": None, "divergence": None,
                    "score": {"bullish": 0, "bearish": 0},
                    "note": "No volume data available from broker"
                }
            
            vwap = self._calculate_vwap(candles)
            obv = self._calculate_obv(candles)
            profile = self._calculate_volume_profile(candles)
            divergence = self._detect_volume_divergence(candles)
            score = self._calculate_volume_score(candles, vwap, obv, divergence)

            return {
                "vwap": vwap,
                "obv": obv,
                "volume_profile": profile,
                "divergence": divergence,
                "score": score
            }
        except Exception as e:
            logger.error(f"Volume analysis error: {e}")
            return {
                "vwap": None, "obv": None,
                "volume_profile": None, "divergence": None,
                "score": {"bullish": 0, "bearish": 0}
            }

    def _get_volume(self, candle: Dict) -> float:
        """Get volume from candle (tick_volume or volume)"""
        return candle.get("tick_volume", candle.get("volume", 0))

    def _calculate_vwap(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        Formula: VWAP = Cumulative(Typical Price × Volume) / Cumulative(Volume)
        Typical Price = (High + Low + Close) / 3
        """
        cumulative_tp_vol = 0
        cumulative_vol = 0
        vwap_values = []

        for candle in candles:
            typical_price = (candle["high"] + candle["low"] + candle["close"]) / 3
            vol = self._get_volume(candle)
            
            cumulative_tp_vol += typical_price * vol
            cumulative_vol += vol
            
            if cumulative_vol > 0:
                vwap = cumulative_tp_vol / cumulative_vol
                vwap_values.append(round(vwap, 5))
            else:
                vwap_values.append(round(typical_price, 5))

        current_vwap = vwap_values[-1] if vwap_values else 0
        current_price = candles[-1]["close"]
        
        # Position relative to VWAP
        if current_price > current_vwap * 1.001:
            position = "ABOVE"
            bias = "BULLISH"
        elif current_price < current_vwap * 0.999:
            position = "BELOW"
            bias = "BEARISH"
        else:
            position = "AT_VWAP"
            bias = "NEUTRAL"

        return {
            "value": current_vwap,
            "position": position,
            "bias": bias,
            "distance_pct": round(abs(current_price - current_vwap) / current_price * 100, 3),
            "history": vwap_values[-20:]
        }

    def _calculate_obv(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Calculate On Balance Volume (OBV).
        
        OBV increases when close > prev close (buying pressure)
        OBV decreases when close < prev close (selling pressure)
        """
        obv_values = [0]
        
        for i in range(1, len(candles)):
            vol = self._get_volume(candles[i])
            
            if candles[i]["close"] > candles[i-1]["close"]:
                obv_values.append(obv_values[-1] + vol)
            elif candles[i]["close"] < candles[i-1]["close"]:
                obv_values.append(obv_values[-1] - vol)
            else:
                obv_values.append(obv_values[-1])
        
        # OBV trend (last 10 vs previous 10)
        if len(obv_values) >= 20:
            recent_avg = np.mean(obv_values[-10:])
            older_avg = np.mean(obv_values[-20:-10])
            
            if recent_avg > older_avg * 1.05:
                trend = "RISING"
                bias = "BULLISH"
            elif recent_avg < older_avg * 0.95:
                trend = "FALLING"
                bias = "BEARISH"
            else:
                trend = "FLAT"
                bias = "NEUTRAL"
        else:
            trend = "INSUFFICIENT_DATA"
            bias = "NEUTRAL"

        return {
            "value": obv_values[-1],
            "trend": trend,
            "bias": bias,
            "history": obv_values[-20:]
        }

    def _calculate_volume_profile(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Calculate Volume Profile - distribution of volume across price levels.
        
        Key levels:
        - POC (Point of Control): Price with highest volume
        - VAH (Value Area High): Upper boundary of 70% volume area
        - VAL (Value Area Low): Lower boundary of 70% volume area
        """
        if len(candles) < 10:
            return None
        
        # Create price bins
        all_highs = [c["high"] for c in candles]
        all_lows = [c["low"] for c in candles]
        price_min = min(all_lows)
        price_max = max(all_highs)
        
        if price_max == price_min:
            return None
        
        num_bins = 30
        bin_size = (price_max - price_min) / num_bins
        bins = [0.0] * num_bins
        bin_prices = [price_min + (i + 0.5) * bin_size for i in range(num_bins)]
        
        # Distribute volume across bins
        for candle in candles:
            vol = self._get_volume(candle)
            typical = (candle["high"] + candle["low"] + candle["close"]) / 3
            
            bin_idx = min(int((typical - price_min) / bin_size), num_bins - 1)
            bins[bin_idx] += vol
        
        # POC - highest volume bin
        poc_idx = bins.index(max(bins))
        poc_price = bin_prices[poc_idx]
        
        # Value Area (70% of total volume)
        total_vol = sum(bins)
        if total_vol == 0:
            return None
        
        target_vol = total_vol * 0.7
        cumulative = bins[poc_idx]
        left = poc_idx
        right = poc_idx
        
        while cumulative < target_vol and (left > 0 or right < num_bins - 1):
            left_vol = bins[left - 1] if left > 0 else 0
            right_vol = bins[right + 1] if right < num_bins - 1 else 0
            
            if left_vol >= right_vol and left > 0:
                left -= 1
                cumulative += bins[left]
            elif right < num_bins - 1:
                right += 1
                cumulative += bins[right]
            else:
                break
        
        vah = bin_prices[right]
        val_ = bin_prices[left]
        
        current_price = candles[-1]["close"]
        
        if current_price > vah:
            position = "ABOVE_VA"
        elif current_price < val_:
            position = "BELOW_VA"
        elif abs(current_price - poc_price) / current_price < 0.002:
            position = "AT_POC"
        else:
            position = "INSIDE_VA"

        return {
            "poc": round(poc_price, 5),
            "vah": round(vah, 5),
            "val": round(val_, 5),
            "position": position,
            "description": f"POC at {poc_price:.5f}, VA: {val_:.5f} - {vah:.5f}"
        }

    def _detect_volume_divergence(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Detect Volume Divergence - price making new highs/lows but volume declining.
        This signals weakening momentum and potential reversal.
        """
        if len(candles) < 10:
            return {"type": "NONE"}
        
        recent = candles[-10:]
        prices = [c["close"] for c in recent]
        volumes = [self._get_volume(c) for c in recent]
        
        # Check if price is rising but volume is falling (bearish divergence)
        price_rising = prices[-1] > prices[0] and prices[-1] > prices[-5]
        vol_avg_recent = np.mean(volumes[-3:])
        vol_avg_older = np.mean(volumes[:3])
        vol_falling = vol_avg_recent < vol_avg_older * 0.7
        
        if price_rising and vol_falling:
            return {
                "type": "BEARISH_DIVERGENCE",
                "description": "Price rising but volume declining - weakness signal",
                "strength": min(100, int((1 - vol_avg_recent / max(vol_avg_older, 1)) * 100))
            }
        
        # Check if price is falling but volume is falling (bullish divergence)
        price_falling = prices[-1] < prices[0] and prices[-1] < prices[-5]
        
        if price_falling and vol_falling:
            return {
                "type": "BULLISH_DIVERGENCE",
                "description": "Price falling but volume declining - selling exhaustion",
                "strength": min(100, int((1 - vol_avg_recent / max(vol_avg_older, 1)) * 100))
            }
        
        # Volume surge (confirmation of move)
        vol_surge = vol_avg_recent > vol_avg_older * 1.5
        if vol_surge and price_rising:
            return {
                "type": "BULLISH_CONFIRMATION",
                "description": "Price rising with increasing volume - strong move",
                "strength": min(100, int((vol_avg_recent / max(vol_avg_older, 1) - 1) * 50))
            }
        elif vol_surge and price_falling:
            return {
                "type": "BEARISH_CONFIRMATION",
                "description": "Price falling with increasing volume - strong selloff",
                "strength": min(100, int((vol_avg_recent / max(vol_avg_older, 1) - 1) * 50))
            }
        
        return {"type": "NONE", "description": "No significant volume divergence"}

    def _calculate_volume_score(self, candles: List[Dict], vwap: Dict,
                                 obv: Dict, divergence: Dict) -> Dict[str, Any]:
        """Calculate composite volume score"""
        bullish = 0
        bearish = 0
        reasons = []
        
        # VWAP bias (weight: 35%)
        if vwap:
            if vwap.get("bias") == "BULLISH":
                bullish += 35
                reasons.append(f"Price above VWAP ({vwap['value']:.5f})")
            elif vwap.get("bias") == "BEARISH":
                bearish += 35
                reasons.append(f"Price below VWAP ({vwap['value']:.5f})")
        
        # OBV trend (weight: 30%)
        if obv:
            if obv.get("bias") == "BULLISH":
                bullish += 30
                reasons.append("OBV Rising - buying pressure")
            elif obv.get("bias") == "BEARISH":
                bearish += 30
                reasons.append("OBV Falling - selling pressure")
        
        # Volume divergence (weight: 35%)
        if divergence:
            div_type = divergence.get("type", "NONE")
            if "BULLISH" in div_type:
                bullish += 35
                reasons.append(divergence.get("description", ""))
            elif "BEARISH" in div_type:
                bearish += 35
                reasons.append(divergence.get("description", ""))
        
        return {
            "bullish": min(100, bullish),
            "bearish": min(100, bearish),
            "bias": "BULLISH" if bullish > bearish + 10 else "BEARISH" if bearish > bullish + 10 else "NEUTRAL",
            "reasons": reasons[:3]
        }


# Singleton
volume_analyzer = VolumeAnalyzer()
