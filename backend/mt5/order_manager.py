"""Order management operations"""
import MetaTrader5 as mt5
import logging
from typing import Optional, List, Dict, Any
from mt5.connector import connector

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages all order operations"""

    def place_limit_order(
        self,
        symbol: str,
        trade_type: str,
        volume: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a limit order
        trade_type: 'BUY' or 'SELL'
        """
        if not connector.is_connected():
            return None

        # Convert trade type to limit order type
        if trade_type.upper() == "BUY":
            mt5_type = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            mt5_type = mt5.ORDER_TYPE_SELL_LIMIT

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_type,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "AI Trading Limit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Add SL/TP if provided
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        # Send request
        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Order send returned None for {symbol}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: retcode={result.retcode}, comment={result.comment}")
            return {
                "success": False,
                "error": f"retcode={result.retcode}, comment={result.comment}"
            }

        return {
            "success": True,
            "order": result.order,
            "ticket": result.order
        }

    def place_stop_order(
        self,
        symbol: str,
        trade_type: str,
        volume: float,
        price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a stop order
        trade_type: 'BUY' or 'SELL'
        """
        if not connector.is_connected():
            return None

        # Convert trade type to stop order type
        if trade_type.upper() == "BUY":
            mt5_type = mt5.ORDER_TYPE_BUY_STOP
        else:
            mt5_type = mt5.ORDER_TYPE_SELL_STOP

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_type,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "AI Trading Stop",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Add SL/TP if provided
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        # Send request
        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Stop order send returned None for {symbol}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Stop order failed: retcode={result.retcode}, comment={result.comment}")
            return {
                "success": False,
                "error": f"retcode={result.retcode}, comment={result.comment}"
            }

        return {
            "success": True,
            "order": result.order,
            "ticket": result.order
        }

    def cancel_order(self, ticket: int) -> bool:
        """Cancel a pending order by ticket using TRADE_ACTION_REMOVE"""
        if not connector.is_connected():
            return False

        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }

        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Cancel order failed for ticket {ticket}")
            return False

        return True

    def modify_order(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Modify order SL and TP"""
        if not connector.is_connected():
            return False

        # Get order
        orders = mt5.orders_get(ticket=ticket)
        if orders is None or len(orders) == 0:
            return False

        order = orders[0]

        # Create request
        request = {
            "action": mt5.TRADE_ACTION_MODIFY,
            "order": order.ticket,
            "symbol": order.symbol,
            "price": order.price_open,
            "sl": sl if sl is not None else order.sl,
            "tp": tp if tp is not None else order.tp,
            "type_time": order.type_time,
            "type_filling": order.type_filling,
        }

        # Send request
        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Modify order failed for ticket {ticket}")
            return False

        return True

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get all open (pending) orders"""
        if not connector.is_connected():
            return []

        orders = mt5.orders_get()
        if orders is None or len(orders) == 0:
            return []

        result = []
        for order in orders:
            result.append(self._order_to_dict(order))

        return result

    def _order_to_dict(self, order) -> Dict[str, Any]:
        """Convert MT5 order to dictionary"""
        order_type_map = {
            mt5.ORDER_TYPE_BUY: "BUY",
            mt5.ORDER_TYPE_SELL: "SELL",
            mt5.ORDER_TYPE_BUY_LIMIT: "BUY_LIMIT",
            mt5.ORDER_TYPE_SELL_LIMIT: "SELL_LIMIT",
            mt5.ORDER_TYPE_BUY_STOP: "BUY_STOP",
            mt5.ORDER_TYPE_SELL_STOP: "SELL_STOP",
        }

        return {
            "ticket": order.ticket,
            "symbol": order.symbol,
            "type": order_type_map.get(order.type, "UNKNOWN"),
            "volume": order.volume_current,
            "price": order.price_open,
            "sl": order.sl,
            "tp": order.tp,
            "current_price": order.price_current,
            "magic": order.magic,
            "comment": order.comment,
            "type_time": order.type_time,
            "type_filling": order.type_filling
        }


# Singleton instance
order_manager = OrderManager()
