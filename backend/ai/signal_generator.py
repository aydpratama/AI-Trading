"""Signal Generator - AI Trading Signals"""
from typing import List, Dict, Any
from ai.rsi_calculator import rsi_calculator
from ai.macd_calculator import macd_calculator
from ai.ma_calculator import ma_calculator
from ai.sr_detector import sr_detector
from datetime import datetime
import uuid


class SignalGenerator:
    """Generates trading signals based on technical analysis"""

    def __init__(self):
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30

    def generate_signals(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a symbol and timeframe
        Returns list of signals with confidence scores
        """
        # Get candles
        candles = self._get_candles(symbol, timeframe, count=100)

        if not candles:
            return []

        # Calculate indicators
        rsi_values = rsi_calculator.calculate(candles)
        macd_data = macd_calculator.calculate(candles)
        ma_data = ma_calculator.calculate(candles)
        sr_levels = sr_detector.detect(candles)

        current_rsi = rsi_values[-1]
        current_macd = macd_data["macd"][-1]
        current_signal = macd_data["signal"][-1]
        current_histogram = macd_data["histogram"][-1]

        current_ema_9 = ma_data["ema_9"][-1]
        current_ema_21 = ma_data["ema_21"][-1]
        current_ema_50 = ma_data["ema_50"][-1]

        current_price = candles[-1]["close"]
        sl_price = candles[-1]["close"] * 0.995
        tp_price = candles[-1]["close"] * 1.005

        signals = []

        # Generate BUY signals
        buy_signals = self._check_buy_conditions(
            symbol, timeframe, current_price, sl_price, tp_price,
            current_rsi, current_macd, current_signal, current_histogram,
            current_ema_9, current_ema_21, current_ema_50, sr_levels
        )
        signals.extend(buy_signals)

        # Generate SELL signals
        sell_signals = self._check_sell_conditions(
            symbol, timeframe, current_price, sl_price, tp_price,
            current_rsi, current_macd, current_signal, current_histogram,
            current_ema_9, current_ema_21, current_ema_50, sr_levels
        )
        signals.extend(sell_signals)

        return signals

    def _get_candles(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict[str, Any]]:
        """Get candles from MT5"""
        from mt5.connector import connector

        if not connector.is_connected():
            return []

        candles = connector.get_candles(symbol, timeframe, count)
        return candles

    def _check_buy_conditions(
        self,
        symbol: str,
        timeframe: str,
        current_price: float,
        sl_price: float,
        tp_price: float,
        rsi: float,
        macd: float,
        signal: float,
        histogram: float,
        ema_9: float,
        ema_21: float,
        ema_50: float,
        sr_levels: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Check BUY signal conditions"""
        conditions = []
        reasons = []

        # RSI conditions
        if rsi < 30:
            conditions.append(True)
            reasons.append(f"RSI Oversold ({rsi:.1f})")
        elif rsi < 40:
            conditions.append(True)
            reasons.append(f"RSI Weak ({rsi:.1f})")

        # MACD conditions
        if histogram > 0 and macd > signal:
            conditions.append(True)
            reasons.append("MACD Bullish Crossover")
        elif histogram > 0:
            conditions.append(True)
            reasons.append("MACD Bullish")

        # EMA conditions
        if ema_9 > ema_21 > ema_50:
            conditions.append(True)
            reasons.append("EMA Bullish Alignment")
        elif ema_9 > ema_21:
            conditions.append(True)
            reasons.append("EMA Bullish Cross")

        # Support level
        support_1 = sr_levels["support"][0] if sr_levels["support"] else None
        if support_1 and current_price < support_1 * 1.002:
            conditions.append(True)
            reasons.append(f"Near Support ({support_1:.5f})")

        # Divergence
        divergence = rsi_calculator.is_divergence(
            self._get_candles(symbol, timeframe, 50), threshold=0.05
        )
        if divergence == "BULLISH":
            conditions.append(True)
            reasons.append(f"RSI Bullish Divergence")

        # Calculate confidence
        confidence = self._calculate_confidence(
            conditions, rsi, macd, ema_9, ema_21, ema_50
        )

        if confidence >= 70 and len(conditions) >= 2:
            risk_reward = (tp_price - current_price) / (current_price - sl_price)

            return [{
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "type": "BUY",
                "timeframe": timeframe,
                "entry": current_price,
                "sl": sl_price,
                "tp": tp_price,
                "risk_reward": round(risk_reward, 2),
                "confidence": round(confidence, 1),
                "indicators": {
                    "rsi": round(rsi, 2),
                    "macd": round(macd, 5),
                    "signal": round(signal, 5),
                    "histogram": round(histogram, 5),
                    "ema_9": round(ema_9, 5),
                    "ema_21": round(ema_21, 5),
                    "ema_50": round(ema_50, 5)
                },
                "support_resistance": {
                    "resistance_1": sr_levels["resistance"][0] if sr_levels["resistance"] else None,
                    "resistance_2": sr_levels["resistance"][1] if len(sr_levels["resistance"]) > 1 else None,
                    "support_1": support_1,
                    "support_2": sr_levels["support"][1] if len(sr_levels["support"]) > 1 else None
                },
                "reason": reasons
            }]

        return []

    def _check_sell_conditions(
        self,
        symbol: str,
        timeframe: str,
        current_price: float,
        sl_price: float,
        tp_price: float,
        rsi: float,
        macd: float,
        signal: float,
        histogram: float,
        ema_9: float,
        ema_21: float,
        ema_50: float,
        sr_levels: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Check SELL signal conditions"""
        conditions = []
        reasons = []

        # RSI conditions
        if rsi > 70:
            conditions.append(True)
            reasons.append(f"RSI Overbought ({rsi:.1f})")
        elif rsi > 60:
            conditions.append(True)
            reasons.append(f"RSI Strong ({rsi:.1f})")

        # MACD conditions
        if histogram < 0 and macd < signal:
            conditions.append(True)
            reasons.append("MACD Bearish Crossover")
        elif histogram < 0:
            conditions.append(True)
            reasons.append("MACD Bearish")

        # EMA conditions
        if ema_9 < ema_21 < ema_50:
            conditions.append(True)
            reasons.append("EMA Bearish Alignment")
        elif ema_9 < ema_21:
            conditions.append(True)
            reasons.append("EMA Bearish Cross")

        # Resistance level
        resistance_1 = sr_levels["resistance"][0] if sr_levels["resistance"] else None
        if resistance_1 and current_price > resistance_1 * 0.998:
            conditions.append(True)
            reasons.append(f"Near Resistance ({resistance_1:.5f})")

        # Divergence
        divergence = rsi_calculator.is_divergence(
            self._get_candles(symbol, timeframe, 50), threshold=0.05
        )
        if divergence == "BEARISH":
            conditions.append(True)
            reasons.append(f"RSI Bearish Divergence")

        # Calculate confidence
        confidence = self._calculate_confidence(
            conditions, rsi, macd, ema_9, ema_21, ema_50
        )

        if confidence >= 70 and len(conditions) >= 2:
            risk_reward = (current_price - sl_price) / (tp_price - current_price)

            return [{
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "type": "SELL",
                "timeframe": timeframe,
                "entry": current_price,
                "sl": sl_price,
                "tp": tp_price,
                "risk_reward": round(risk_reward, 2),
                "confidence": round(confidence, 1),
                "indicators": {
                    "rsi": round(rsi, 2),
                    "macd": round(macd, 5),
                    "signal": round(signal, 5),
                    "histogram": round(histogram, 5),
                    "ema_9": round(ema_9, 5),
                    "ema_21": round(ema_21, 5),
                    "ema_50": round(ema_50, 5)
                },
                "support_resistance": {
                    "resistance_1": resistance_1,
                    "resistance_2": sr_levels["resistance"][1] if len(sr_levels["resistance"]) > 1 else None,
                    "support_1": sr_levels["support"][0] if sr_levels["support"] else None,
                    "support_2": sr_levels["support"][1] if len(sr_levels["support"]) > 1 else None
                },
                "reason": reasons
            }]

        return []

    def _calculate_confidence(
        self,
        conditions: List[bool],
        rsi: float,
        macd: float,
        ema_9: float,
        ema_21: float,
        ema_50: float
    ) -> float:
        """Calculate signal confidence score based on how many conditions are met"""
        if len(conditions) == 0:
            return 0.0

        # Base score from number of conditions matched
        # Each condition is worth up to 20 points, max 5 conditions
        condition_score = min(len(conditions) * 20, 100)

        # RSI extremes add conviction (0-15 points)
        rsi_bonus = 0
        if rsi < 25 or rsi > 75:
            rsi_bonus = 15
        elif rsi < 30 or rsi > 70:
            rsi_bonus = 10
        elif rsi < 35 or rsi > 65:
            rsi_bonus = 5

        # EMA alignment adds conviction (0-15 points)
        ema_bonus = 0
        if ema_9 > ema_21 > ema_50:
            ema_bonus = 15  # Full bullish alignment
        elif ema_9 < ema_21 < ema_50:
            ema_bonus = 15  # Full bearish alignment
        elif ema_9 > ema_21 or ema_9 < ema_21:
            ema_bonus = 8   # Partial alignment

        # Weighted final score
        score = (condition_score * 0.6) + (rsi_bonus * 0.2) + (ema_bonus * 0.2)

        # Scale to 0-100
        return min(max(score, 0), 100)


# Singleton instance
signal_generator = SignalGenerator()
