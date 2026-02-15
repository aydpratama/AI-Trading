"""Position management operations"""
import MetaTrader5 as mt5
import logging
from typing import List, Dict, Any, Optional
from mt5.connector import connector
from datetime import datetime

logger = logging.getLogger(__name__)


class PositionManager:
    """Manages all position operations"""

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions from MT5"""
        if not connector.is_connected():
            return []

        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            return []

        result = []
        for pos in positions:
            result.append(self._position_to_dict(pos))

        return result

    def get_position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Get position by ticket number"""
        if not connector.is_connected():
            return None

        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return None

        return self._position_to_dict(position[0])

    def open_position(
        self,
        symbol: str,
        trade_type: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Open a new position (market order)
        trade_type: 'BUY' or 'SELL'
        """
        if not connector.is_connected():
            return None

        # Convert trade type
        mt5_type = mt5.ORDER_TYPE_BUY if trade_type.upper() == "BUY" else mt5.ORDER_TYPE_SELL

        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}")
            return None

        price = tick.ask if trade_type.upper() == "BUY" else tick.bid

        # Get symbol info for proper volume rounding
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Failed to get symbol info for {symbol}")
            return None

        # Ensure symbol is selected in Market Watch
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None

        # Calculate default SL and TP if not provided
        point = symbol_info.point
        digits = symbol_info.digits

        if sl is None:
            if trade_type.upper() == "BUY":
                sl = round(price - 50 * point, digits)
            else:
                sl = round(price + 50 * point, digits)

        if tp is None:
            if trade_type.upper() == "BUY":
                tp = round(price + 100 * point, digits)
            else:
                tp = round(price - 100 * point, digits)

        # Risk-based position sizing (2% of balance)
        account = mt5.account_info()
        if account is not None and volume > 0:
            risk_amount = account.balance * 0.02
            sl_distance = abs(price - sl)
            if sl_distance > 0:
                tick_value = symbol_info.trade_tick_value
                tick_size = symbol_info.trade_tick_size
                if tick_value > 0 and tick_size > 0:
                    max_volume = risk_amount / (sl_distance / tick_size * tick_value)
                    max_volume = round(max_volume / symbol_info.volume_step) * symbol_info.volume_step
                    max_volume = max(symbol_info.volume_min, min(max_volume, symbol_info.volume_max))
                    if volume > max_volume:
                        volume = max_volume

        # Ensure minimum volume
        volume = max(symbol_info.volume_min, volume)
        volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "comment": "AI Trading",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send request
        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Order send returned None for {symbol}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Open position failed: retcode={result.retcode}, comment={result.comment}")
            return {
                "success": False,
                "error": f"retcode={result.retcode}, comment={result.comment}"
            }

        # Get the created position
        position = mt5.positions_get(ticket=result.order)
        if position and len(position) > 0:
            pos_dict = self._position_to_dict(position[0])
            pos_dict["success"] = True
            return pos_dict

        return {"success": True, "ticket": result.order}

    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not connector.is_connected():
            return False

        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            logger.error(f"Position {ticket} not found")
            return False

        pos = position[0]

        # Get current price
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {pos.symbol}")
            return False

        # Calculate close price (opposite of open)
        close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": close_price,
            "deviation": 20,
            "magic": 123456,
            "comment": "AI Trading Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Send request
        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close position failed for ticket {ticket}: {result}")
            return False

        return True

    def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Modify position SL and TP"""
        if not connector.is_connected():
            return False

        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return False

        pos = position[0]

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "sl": sl if sl is not None else pos.sl,
            "tp": tp if tp is not None else pos.tp,
        }

        # Send request
        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Modify position failed for ticket {ticket}")
            return False

        return True

    def _position_to_dict(self, pos) -> Dict[str, Any]:
        """Convert MT5 position to dictionary"""
        return {
            "ticket": pos.ticket,
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
            "volume": pos.volume,
            "entry": pos.price_open,
            "sl": pos.sl,
            "tp": pos.tp,
            "current": pos.price_current,
            "pnl": pos.profit,
            "margin": 0.0,  # Margin is per-account, not per-position in MT5
            "profit": pos.profit,
            "status": "OPEN",
            "open_time": datetime.fromtimestamp(pos.time).isoformat(),
            "close_time": None,
            "timeframe": "1H",  # Default, MT5 positions don't have timeframe
            "reason": f"Magic: {pos.magic}",
            "confidence": None
        }


# Singleton instance
position_manager = PositionManager()
