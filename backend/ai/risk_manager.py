"""Risk Manager - Position Sizing & Risk Management"""
from typing import Dict, Any, Optional, List
from mt5.connector import connector
import math


class RiskManager:
    """Calculate position sizing and manage risk"""

    # Default risk settings
    DEFAULT_RISK_PERCENT = 1.0  # 1% per trade
    MAX_RISK_PERCENT = 5.0      # Max 5% per trade
    MAX_DAILY_RISK = 10.0       # Max 10% daily
    MAX_DRAWDOWN = 20.0         # Max 20% drawdown before stop

    # Risk levels
    RISK_LEVELS = {
        "conservative": {"risk": 0.5, "rr_min": 2.0, "confidence_min": 80},
        "moderate": {"risk": 1.0, "rr_min": 1.5, "confidence_min": 70},
        "aggressive": {"risk": 2.0, "rr_min": 1.0, "confidence_min": 60}
    }

    def __init__(self):
        self.account_info = None

    def calculate_position_size(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        risk_percent: float = None,
        risk_level: str = "moderate",
        max_lot: float = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk parameters

        Args:
            symbol: Trading symbol
            entry: Entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage (optional, uses risk_level if not provided)
            risk_level: Risk level (conservative/moderate/aggressive)
            max_lot: Maximum lot size allowed

        Returns:
            Position sizing details
        """
        # Get account info
        account = connector.get_account_info()
        if not account:
            return {"error": "Cannot get account info"}

        balance = account.get("balance", 0)
        equity = account.get("equity", balance)

        # Get symbol info for lot calculation
        symbol_info = connector.get_symbol_info(symbol)
        if not symbol_info:
            return {"error": f"Cannot get symbol info for {symbol}"}

        # Determine risk percentage
        if risk_percent is None:
            risk_percent = self.RISK_LEVELS.get(risk_level, self.RISK_LEVELS["moderate"])["risk"]

        # Cap risk at maximum
        risk_percent = min(risk_percent, self.MAX_RISK_PERCENT)

        # Calculate risk amount in account currency
        risk_amount = balance * (risk_percent / 100)

        # Calculate stop loss distance in points
        sl_distance = abs(entry - stop_loss)

        # Get point value and contract size
        point = symbol_info.get("point", 0.00001)
        contract_size = symbol_info.get("contract_size", 100000)
        tick_value = symbol_info.get("tick_value", 1)
        tick_size = symbol_info.get("tick_size", point)

        # Calculate pip value per lot
        if tick_value and tick_size:
            pip_value_per_lot = tick_value / tick_size * point
        else:
            # Fallback calculation
            pip_value_per_lot = contract_size * point

        # Calculate lot size
        # Lot = Risk Amount / (SL Distance * Pip Value per Lot)
        sl_points = sl_distance / point if point > 0 else 0
        if sl_distance > 0 and pip_value_per_lot > 0 and sl_points > 0:
            lot_size = risk_amount / (sl_points * pip_value_per_lot)
        else:
            lot_size = 0.01

        # Round to proper lot step
        lot_step = symbol_info.get("lot_step", 0.01)
        lot_size = math.floor(lot_size / lot_step) * lot_step

        # Apply min/max lot limits
        min_lot = symbol_info.get("lot_min", 0.01)
        max_lot_limit = symbol_info.get("lot_max", 100)

        lot_size = max(min_lot, min(lot_size, max_lot_limit))
        if max_lot:
            lot_size = min(lot_size, max_lot)

        # Round to 2 decimal places
        lot_size = round(lot_size, 2)

        # Calculate actual risk with this lot size
        actual_risk_amount = lot_size * sl_points * pip_value_per_lot
        actual_risk_percent = (actual_risk_amount / balance) * 100

        # Calculate margin required
        leverage = account.get("leverage", 100)
        margin_required = (lot_size * contract_size * entry) / leverage

        # Free margin check
        free_margin = equity - margin_required

        return {
            "symbol": symbol,
            "lot_size": lot_size,
            "risk_amount": round(actual_risk_amount, 2),
            "risk_percent": round(actual_risk_percent, 2),
            "entry_price": entry,
            "stop_loss": stop_loss,
            "sl_distance_pips": round(sl_distance / (point * 10), 1),  # In pips
            "sl_distance_points": round(sl_points, 1),
            "margin_required": round(margin_required, 2),
            "free_margin_after": round(free_margin, 2),
            "can_open": free_margin > 0 and actual_risk_percent <= self.MAX_RISK_PERCENT,
            "risk_level": risk_level,
            "account_balance": balance,
            "account_equity": equity
        }

    def calculate_risk_reward(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float
    ) -> Dict[str, Any]:
        """Calculate risk/reward ratio"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)

        if risk == 0:
            return {"ratio": 0, "risk": 0, "reward": 0, "is_favorable": False}

        ratio = reward / risk

        return {
            "ratio": round(ratio, 2),
            "risk_pips": round(risk * 10000, 1),  # Approximate pips
            "reward_pips": round(reward * 10000, 1),
            "is_favorable": ratio >= 1.5,
            "quality": "EXCELLENT" if ratio >= 3 else "GOOD" if ratio >= 2 else "FAIR" if ratio >= 1.5 else "POOR"
        }

    def calculate_take_profit_levels(
        self,
        entry: float,
        stop_loss: float,
        direction: str,
        levels: List[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate multiple take profit levels
        Default: TP1 at 1:1, TP2 at 1:2, TP3 at 1:3
        """
        if levels is None:
            levels = [1.0, 2.0, 3.0]

        risk = abs(entry - stop_loss)
        results = []

        for i, rr in enumerate(levels):
            if direction.upper() == "BUY":
                tp = entry + (risk * rr)
            else:
                tp = entry - (risk * rr)

            results.append({
                "level": i + 1,
                "price": round(tp, 5),
                "risk_reward": rr,
                "pips_from_entry": round(risk * rr * 10000, 1)
            })

        return results

    def assess_trade_risk(
        self,
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        lot_size: float = None,
        risk_percent: float = 1.0
    ) -> Dict[str, Any]:
        """
        Comprehensive trade risk assessment
        """
        # Get account info
        account = connector.get_account_info()
        if not account:
            return {"error": "Cannot get account info"}

        balance = account.get("balance", 0)
        equity = account.get("equity", balance)

        # Calculate risk/reward
        rr = self.calculate_risk_reward(entry, stop_loss, take_profit)

        # Calculate position size if not provided
        if lot_size is None:
            pos_size = self.calculate_position_size(
                symbol, entry, stop_loss, risk_percent
            )
            lot_size = pos_size.get("lot_size", 0.01)
            risk_info = pos_size
        else:
            risk_info = self.calculate_position_size(
                symbol, entry, stop_loss, risk_percent
            )

        # Daily risk check (simplified - would need trade history)
        daily_risk_ok = True  # Placeholder

        # Drawdown check
        drawdown_pct = ((balance - equity) / balance * 100) if balance > 0 else 0
        drawdown_ok = drawdown_pct < self.MAX_DRAWDOWN

        # Overall risk score (0-100, higher is safer)
        risk_score = 100
        warnings = []
        recommendations = []

        # Check R:R
        if rr["ratio"] < 1.5:
            risk_score -= 20
            warnings.append(f"Risk/Reward ratio {rr['ratio']} is below 1.5")
            recommendations.append("Consider wider take profit or tighter stop loss")

        # Check risk percent
        if risk_info.get("risk_percent", 0) > 2:
            risk_score -= 15
            warnings.append(f"Risk {risk_info.get('risk_percent')}% is above recommended 2%")
            recommendations.append("Reduce position size")

        # Check margin
        if risk_info.get("free_margin_after", 0) < balance * 0.1:
            risk_score -= 25
            warnings.append("Low free margin after trade")
            recommendations.append("Reduce lot size or wait for more margin")

        # Check drawdown
        if drawdown_pct > 10:
            risk_score -= 20
            warnings.append(f"Account drawdown is {drawdown_pct:.1f}%")
            recommendations.append("Consider reducing risk until equity recovers")

        # Final assessment
        if risk_score >= 80:
            assessment = "LOW RISK"
        elif risk_score >= 60:
            assessment = "MODERATE RISK"
        elif risk_score >= 40:
            assessment = "HIGH RISK"
        else:
            assessment = "VERY HIGH RISK"

        return {
            "assessment": assessment,
            "risk_score": max(0, risk_score),
            "can_proceed": risk_score >= 40 and drawdown_ok,
            "lot_size": lot_size,
            "risk_reward": rr,
            "position_details": risk_info,
            "warnings": warnings,
            "recommendations": recommendations,
            "account_drawdown": round(drawdown_pct, 2),
            "daily_risk_ok": daily_risk_ok,
            "drawdown_ok": drawdown_ok
        }

    def get_optimal_setup(
        self,
        symbol: str,
        direction: str,
        entry: float,
        support: float = None,
        resistance: float = None,
        account_risk_level: str = "moderate",
        risk_percentage: float = None,
        confidence: float = 70,
        custom_capital: float = None
    ) -> Dict[str, Any]:
        """
        Get optimal trading setup with entry, SL, TP, and lot size
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
            entry: Entry price
            support: Support level (optional)
            resistance: Resistance level (optional)
            account_risk_level: Risk level (conservative/moderate/aggressive)
            risk_percentage: Explicit risk percentage (overrides level)
            confidence: Signal confidence (0-100)
            custom_capital: Optional custom capital to use instead of MT5 balance
        """
        # Get account info
        account = connector.get_account_info()
        if not account:
            return {"error": "Cannot get account info"}

        # Use custom capital if provided, otherwise use MT5 balance
        balance = custom_capital if custom_capital and custom_capital > 0 else account.get("balance", 0)

        # Get risk settings based on level or percentage
        if risk_percentage is not None and risk_percentage > 0:
            # Explicit percentage provided by user - DO NOT adjust with confidence
            risk_percent = risk_percentage
            risk_settings = {"rr_min": 1.5} # Default RR
        else:
            # Dynamic risk based on level and confidence
            risk_settings = self.RISK_LEVELS.get(account_risk_level, self.RISK_LEVELS["moderate"])
            base_risk = risk_settings["risk"]
            
            # Adjust risk based on confidence
            if confidence >= 90:
                risk_multiplier = 1.2
            elif confidence >= 80:
                risk_multiplier = 1.0
            elif confidence >= 70:
                risk_multiplier = 0.8
            else:
                risk_multiplier = 0.5
                
            risk_percent = base_risk * risk_multiplier

        # Default SL distance in pips (based on symbol type)
        # Get symbol info for proper pip calculation
        symbol_info = connector.get_symbol_info(symbol)
        point = symbol_info.get("point", 0.00001) if symbol_info else 0.00001
        
        # Default SL distances in pips
        if "JPY" in symbol:
            default_sl_pips = 50  # 50 pips for JPY pairs
            pip_size = 0.01
        elif "XAU" in symbol or "XAG" in symbol:
            default_sl_pips = 300  # $3 for gold
            pip_size = 0.1
        elif any(idx in symbol for idx in ["US30", "US500", "US100", "DE30", "UK100"]):
            default_sl_pips = 100  # 100 points for indices
            pip_size = 1.0
        else:
            default_sl_pips = 30  # 30 pips for major forex
            pip_size = 0.0001
        
        # Calculate SL based on direction and support/resistance
        if direction.upper() == "BUY":
            # For BUY: SL must be BELOW entry
            # Only use support if it's actually below entry
            valid_support = support if (support and support < entry) else None
            
            if valid_support:
                # Place SL below support with some buffer
                sl = valid_support - (pip_size * 10)  # 10 pips below support
            else:
                # Use default SL distance
                sl = entry - (default_sl_pips * pip_size)
            
            # VALIDATION: SL must be below entry for BUY
            if sl >= entry:
                sl = entry - (default_sl_pips * pip_size)
                
        else:  # SELL
            # For SELL: SL must be ABOVE entry
            # Only use resistance if it's actually above entry
            valid_resistance = resistance if (resistance and resistance > entry) else None
            
            if valid_resistance:
                # Place SL above resistance with some buffer
                sl = valid_resistance + (pip_size * 10)  # 10 pips above resistance
            else:
                # Use default SL distance
                sl = entry + (default_sl_pips * pip_size)
            
            # VALIDATION: SL must be above entry for SELL
            if sl <= entry:
                sl = entry + (default_sl_pips * pip_size)

        # Calculate TP based on minimum R:R
        min_rr = risk_settings["rr_min"]
        risk = abs(entry - sl)

        if direction.upper() == "BUY":
            # For BUY: TP must be ABOVE entry
            tp = entry + (risk * min_rr)
            
            # Only adjust TP if resistance is above entry and below calculated TP
            valid_resistance = resistance if (resistance and resistance > entry) else None
            if valid_resistance and valid_resistance < tp:
                # Don't use resistance if it gives less than 1:1 R:R
                resistance_rr = (valid_resistance - entry) / risk if risk > 0 else 0
                if resistance_rr >= 1.0:
                    tp = valid_resistance - (pip_size * 5)  # 5 pips before resistance
            
            # VALIDATION: TP must be above entry for BUY
            if tp <= entry:
                tp = entry + (risk * min_rr)
                
        else:  # SELL
            # For SELL: TP must be BELOW entry
            tp = entry - (risk * min_rr)
            
            # Only adjust TP if support is below entry and above calculated TP
            valid_support = support if (support and support < entry) else None
            if valid_support and valid_support > tp:
                # Don't use support if it gives less than 1:1 R:R
                support_rr = (entry - valid_support) / risk if risk > 0 else 0
                if support_rr >= 1.0:
                    tp = valid_support + (pip_size * 5)  # 5 pips before support
            
            # VALIDATION: TP must be below entry for SELL
            if tp >= entry:
                tp = entry - (risk * min_rr)

        # Calculate position size with custom capital
        pos_size = self._calculate_position_size_with_capital(
            symbol, entry, sl, risk_percent, account_risk_level, balance
        )

        # Calculate TP levels
        tp_levels = self.calculate_take_profit_levels(entry, sl, direction)

        # Assess trade risk with custom capital
        risk_assessment = self._assess_trade_risk_with_capital(
            symbol, direction, entry, sl, tp,
            pos_size.get("lot_size"), risk_percent, balance
        )

        return {
            "symbol": symbol,
            "direction": direction,
            "entry": round(entry, 5),
            "stop_loss": round(sl, 5),
            "take_profit": round(tp, 5),
            "lot_size": pos_size.get("lot_size", 0.01),
            "risk_percent": round(pos_size.get("risk_percent", 1), 2),
            "risk_amount": pos_size.get("risk_amount", 0),
            "risk_reward": round(abs(tp - entry) / abs(entry - sl), 2) if abs(entry - sl) > 0 else 0,
            "take_profit_levels": tp_levels,
            "position_details": pos_size,
            "risk_assessment": risk_assessment,
            "confidence_adjusted_risk": round(risk_percent, 2),
            "custom_capital_used": custom_capital is not None
        }

    def _calculate_position_size_with_capital(
        self,
        symbol: str,
        entry: float,
        stop_loss: float,
        risk_percent: float = None,
        risk_level: str = "moderate",
        custom_balance: float = None
    ) -> Dict[str, Any]:
        """Calculate position size with custom capital support"""
        # Get account info for symbol info
        account = connector.get_account_info()
        if not account:
            return {"error": "Cannot get account info"}

        # Use custom balance if provided
        balance = custom_balance if custom_balance and custom_balance > 0 else account.get("balance", 0)
        equity = account.get("equity", balance)

        # Get symbol info for lot calculation
        symbol_info = connector.get_symbol_info(symbol)
        if not symbol_info:
            return {"error": f"Cannot get symbol info for {symbol}"}

        # Determine risk percentage
        if risk_percent is None:
            risk_percent = self.RISK_LEVELS.get(risk_level, self.RISK_LEVELS["moderate"])["risk"]

        # Cap risk at maximum
        risk_percent = min(risk_percent, self.MAX_RISK_PERCENT)

        # Calculate risk amount in account currency
        risk_amount = balance * (risk_percent / 100)

        # Calculate stop loss distance in points
        sl_distance = abs(entry - stop_loss)

        # Get point value and contract size
        point = symbol_info.get("point", 0.00001)
        contract_size = symbol_info.get("contract_size", 100000)
        tick_value = symbol_info.get("tick_value", 1)
        tick_size = symbol_info.get("tick_size", point)

        # Calculate pip value per lot
        if tick_value and tick_size:
            pip_value_per_lot = tick_value / tick_size * point
        else:
            pip_value_per_lot = contract_size * point

        # Calculate lot size
        sl_points = sl_distance / point if point > 0 else 0
        if sl_distance > 0 and pip_value_per_lot > 0 and sl_points > 0:
            lot_size = risk_amount / (sl_points * pip_value_per_lot)
        else:
            lot_size = 0.01

        # Round to proper lot step
        lot_step = symbol_info.get("lot_step", 0.01)
        lot_size = math.floor(lot_size / lot_step) * lot_step

        # Apply min/max lot limits
        min_lot = symbol_info.get("lot_min", 0.01)
        max_lot_limit = symbol_info.get("lot_max", 100)

        lot_size = max(min_lot, min(lot_size, max_lot_limit))

        # Round to 2 decimal places
        lot_size = round(lot_size, 2)

        # Calculate actual risk with this lot size
        actual_risk_amount = lot_size * sl_points * pip_value_per_lot
        actual_risk_percent = (actual_risk_amount / balance) * 100

        # Calculate margin required
        leverage = account.get("leverage", 100)
        margin_required = (lot_size * contract_size * entry) / leverage

        return {
            "symbol": symbol,
            "lot_size": lot_size,
            "risk_amount": round(actual_risk_amount, 2),
            "risk_percent": round(actual_risk_percent, 2),
            "entry_price": entry,
            "stop_loss": stop_loss,
            "sl_distance_pips": round(sl_distance / (point * 10), 1),
            "sl_distance_points": round(sl_points, 1),
            "margin_required": round(margin_required, 2),
            "can_open": actual_risk_percent <= self.MAX_RISK_PERCENT,
            "risk_level": risk_level,
            "account_balance": balance,
            "account_equity": equity
        }

    def _assess_trade_risk_with_capital(
        self,
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        lot_size: float = None,
        risk_percent: float = 1.0,
        custom_balance: float = None
    ) -> Dict[str, Any]:
        """Assess trade risk with custom capital support"""
        # Calculate risk/reward
        rr = self.calculate_risk_reward(entry, stop_loss, take_profit)

        # Calculate position size if not provided
        if lot_size is None:
            pos_size = self._calculate_position_size_with_capital(
                symbol, entry, stop_loss, risk_percent, "moderate", custom_balance
            )
            lot_size = pos_size.get("lot_size", 0.01)
            risk_info = pos_size
        else:
            risk_info = self._calculate_position_size_with_capital(
                symbol, entry, stop_loss, risk_percent, "moderate", custom_balance
            )

        # Overall risk score (0-100, higher is safer)
        risk_score = 100
        warnings = []
        recommendations = []

        # Check R:R
        if rr["ratio"] < 1.5:
            risk_score -= 20
            warnings.append(f"Risk/Reward ratio {rr['ratio']} is below 1.5")
            recommendations.append("Consider wider take profit or tighter stop loss")

        # Check risk percent
        if risk_info.get("risk_percent", 0) > 2:
            risk_score -= 15
            warnings.append(f"Risk {risk_info.get('risk_percent')}% is above recommended 2%")
            recommendations.append("Reduce position size")

        # Final assessment
        if risk_score >= 80:
            assessment = "LOW RISK"
        elif risk_score >= 60:
            assessment = "MODERATE RISK"
        elif risk_score >= 40:
            assessment = "HIGH RISK"
        else:
            assessment = "VERY HIGH RISK"

        return {
            "assessment": assessment,
            "risk_score": max(0, risk_score),
            "can_proceed": risk_score >= 40,
            "lot_size": lot_size,
            "risk_reward": rr,
            "position_details": risk_info,
            "warnings": warnings,
            "recommendations": recommendations
        }

    def check_daily_limits(self) -> Dict[str, Any]:
        """Check if daily risk limits have been reached"""
        account = connector.get_account_info()
        if not account:
            return {"can_trade": False, "reason": "Cannot get account info"}

        balance = account.get("balance", 0)
        equity = account.get("equity", balance)

        # Calculate daily P&L (simplified - would need trade history)
        # For now, use equity vs balance as proxy
        daily_pnl = equity - balance
        daily_pnl_percent = (daily_pnl / balance * 100) if balance > 0 else 0

        # Check limits
        can_trade = True
        warnings = []

        if daily_pnl_percent < -self.MAX_DAILY_RISK:
            can_trade = False
            warnings.append(f"Daily loss limit reached: {daily_pnl_percent:.1f}%")

        if daily_pnl_percent < -self.MAX_DAILY_RISK / 2:
            warnings.append(f"Approaching daily loss limit: {daily_pnl_percent:.1f}%")

        return {
            "can_trade": can_trade,
            "daily_pnl": round(daily_pnl, 2),
            "daily_pnl_percent": round(daily_pnl_percent, 2),
            "max_daily_loss_percent": self.MAX_DAILY_RISK,
            "warnings": warnings
        }


    def calculate_atr_stop_loss(
        self,
        entry: float,
        direction: str,
        atr_value: float,
        atr_multiplier: float = 1.5,
        symbol: str = ""
    ) -> Dict[str, Any]:
        """
        Calculate stop loss based on ATR (Average True Range).
        
        ATR-based SL adapts to market volatility automatically:
        - High volatility → wider stops (avoid noise)
        - Low volatility → tighter stops (capture moves)
        
        Args:
            entry: Entry price
            direction: BUY or SELL
            atr_value: Current ATR value
            atr_multiplier: Multiplier for ATR (default 1.5x)
            symbol: Symbol name for pip calculation
        """
        sl_distance = atr_value * atr_multiplier
        
        if direction.upper() == "BUY":
            sl = entry - sl_distance
        else:
            sl = entry + sl_distance
        
        # Calculate TP levels at different R:R ratios
        tp1 = entry + sl_distance * 1.0 if direction.upper() == "BUY" else entry - sl_distance * 1.0
        tp2 = entry + sl_distance * 2.0 if direction.upper() == "BUY" else entry - sl_distance * 2.0
        tp3 = entry + sl_distance * 3.0 if direction.upper() == "BUY" else entry - sl_distance * 3.0
        
        return {
            "type": "ATR_BASED",
            "entry": round(entry, 5),
            "stop_loss": round(sl, 5),
            "sl_distance": round(sl_distance, 5),
            "atr_value": round(atr_value, 5),
            "atr_multiplier": atr_multiplier,
            "take_profits": {
                "tp1": {"price": round(tp1, 5), "rr": 1.0},
                "tp2": {"price": round(tp2, 5), "rr": 2.0},
                "tp3": {"price": round(tp3, 5), "rr": 3.0}
            }
        }

    def calculate_trailing_stop(
        self,
        entry: float,
        current_price: float,
        direction: str,
        initial_sl: float,
        trail_method: str = "atr",
        atr_value: float = 0,
        trail_pips: float = 20,
        trail_percent: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate trailing stop for an open position.
        
        Methods:
        - 'atr': Trail by ATR distance (adapts to volatility)
        - 'pips': Trail by fixed pip distance
        - 'percent': Trail by percentage of price
        - 'breakeven': Move SL to breakeven after reaching 1:1
        
        Args:
            entry: Original entry price
            current_price: Current market price
            direction: BUY or SELL
            initial_sl: Original stop loss
            trail_method: Method to use
            atr_value: Current ATR (for ATR method)
            trail_pips: Pips distance (for pips method)
            trail_percent: Percent distance (for percent method)
        """
        is_buy = direction.upper() == "BUY"
        risk = abs(entry - initial_sl)
        
        # Calculate profit in direction
        if is_buy:
            profit_distance = current_price - entry
        else:
            profit_distance = entry - current_price
        
        # Only trail if in profit
        if profit_distance <= 0:
            return {
                "new_sl": initial_sl,
                "action": "HOLD",
                "reason": "Position not in profit yet",
                "profit_distance": round(profit_distance, 5)
            }
        
        # Calculate trail distance based on method
        if trail_method == "atr" and atr_value > 0:
            trail_distance = atr_value * 1.0
        elif trail_method == "pips":
            # Convert pips to price
            pip_size = 0.01 if "JPY" in direction else 0.0001
            trail_distance = trail_pips * pip_size
        elif trail_method == "percent":
            trail_distance = current_price * (trail_percent / 100)
        elif trail_method == "breakeven":
            # Move to breakeven after 1R profit
            if profit_distance >= risk:
                if is_buy:
                    new_sl = entry + (risk * 0.1)  # Slightly above entry
                else:
                    new_sl = entry - (risk * 0.1)
                return {
                    "new_sl": round(new_sl, 5),
                    "action": "MOVE_TO_BREAKEVEN",
                    "reason": f"1R profit reached ({profit_distance:.5f})",
                    "profit_distance": round(profit_distance, 5)
                }
            else:
                return {
                    "new_sl": initial_sl,
                    "action": "HOLD",
                    "reason": f"Waiting for 1R ({risk:.5f}) to move to breakeven",
                    "profit_distance": round(profit_distance, 5)
                }
        else:
            trail_distance = risk * 0.5  # Default: trail by half of risk
        
        # Calculate new SL
        if is_buy:
            new_sl = current_price - trail_distance
            # Only move SL up, never down
            new_sl = max(new_sl, initial_sl)
        else:
            new_sl = current_price + trail_distance
            # Only move SL down, never up
            new_sl = min(new_sl, initial_sl)
        
        # Determine action
        if abs(new_sl - initial_sl) < 0.00001:
            action = "HOLD"
            reason = "Trail distance not reached yet"
        else:
            action = "TRAIL"
            reason = f"Trailing SL from {initial_sl:.5f} to {new_sl:.5f}"
        
        return {
            "new_sl": round(new_sl, 5),
            "action": action,
            "reason": reason,
            "method": trail_method,
            "trail_distance": round(trail_distance, 5),
            "profit_distance": round(profit_distance, 5),
            "profit_rr": round(profit_distance / risk, 2) if risk > 0 else 0
        }

    def calculate_partial_tp(
        self,
        entry: float,
        stop_loss: float,
        direction: str,
        lot_size: float,
        current_price: float = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate partial take profit levels for scaling out.
        
        Strategy:
        - TP1 (1:1 R:R): Close 40% — lock in some profit
        - TP2 (2:1 R:R): Close 30% — let winners run
        - TP3 (3:1 R:R): Close 30% — maximum extraction
        - After TP1: Move SL to breakeven
        - After TP2: Trail SL to TP1 level
        """
        risk = abs(entry - stop_loss)
        is_buy = direction.upper() == "BUY"
        
        # Calculate TP levels
        if is_buy:
            tp1_price = entry + risk * 1.0
            tp2_price = entry + risk * 2.0
            tp3_price = entry + risk * 3.0
        else:
            tp1_price = entry - risk * 1.0
            tp2_price = entry - risk * 2.0
            tp3_price = entry - risk * 3.0
        
        # Calculate lot allocation
        lot_step = 0.01
        tp1_lots = max(lot_step, round(lot_size * 0.40 / lot_step) * lot_step)
        tp2_lots = max(lot_step, round(lot_size * 0.30 / lot_step) * lot_step)
        tp3_lots = max(lot_step, lot_size - tp1_lots - tp2_lots)
        
        levels = [
            {
                "level": 1,
                "price": round(tp1_price, 5),
                "lots": round(tp1_lots, 2),
                "percent": 40,
                "rr": 1.0,
                "action_after": "Move SL to breakeven",
                "status": "PENDING"
            },
            {
                "level": 2,
                "price": round(tp2_price, 5),
                "lots": round(tp2_lots, 2),
                "percent": 30,
                "rr": 2.0,
                "action_after": "Trail SL to TP1 level",
                "status": "PENDING"
            },
            {
                "level": 3,
                "price": round(tp3_price, 5),
                "lots": round(tp3_lots, 2),
                "percent": 30,
                "rr": 3.0,
                "action_after": "Position fully closed",
                "status": "PENDING"
            }
        ]
        
        # Update status if current price is provided
        if current_price:
            for level in levels:
                if is_buy and current_price >= level["price"]:
                    level["status"] = "HIT"
                elif not is_buy and current_price <= level["price"]:
                    level["status"] = "HIT"
        
        return levels


# Singleton
risk_manager = RiskManager()