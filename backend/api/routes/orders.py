"""
Orders API Routes
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional
import MetaTrader5 as mt5
from mt5.connector import connector

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("/")
async def get_orders():
    """Get all pending orders"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        orders = mt5.orders_get()
        if orders is None:
            return []
        
        result = []
        for order in orders:
            result.append({
                "ticket": order.ticket,
                "symbol": order.symbol,
                "type": str(order.type),
                "volume": order.volume_current,
                "price": order.price_open,
                "sl": order.sl,
                "tp": order.tp,
                "comment": order.comment,
                "open_time": datetime.fromtimestamp(order.time_setup).isoformat()
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def place_order(order: dict):
    """Place a new market order"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbol = order.get("symbol")
        order_type = order.get("type")  # BUY or SELL
        volume = order.get("volume", 0.01)
        sl = order.get("sl", 0)
        tp = order.get("tp", 0)
        comment = order.get("comment", "")
        
        # Determine order type
        if order_type == "BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        else:
            mt5_order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "message": f"Order failed: {result.comment}"}
        
        return {"success": True, "order": result.order, "message": "Order placed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pending")
async def place_pending_order(order: dict):
    """Place a pending order"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbol = order.get("symbol")
        order_type = order.get("type")  # BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP
        volume = order.get("volume", 0.01)
        price = order.get("price")
        sl = order.get("sl", 0)
        tp = order.get("tp", 0)
        comment = order.get("comment", "")
        
        # Map order types
        type_map = {
            "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
            "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
            "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
            "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
        }
        
        mt5_order_type = type_map.get(order_type)
        if mt5_order_type is None:
            raise HTTPException(status_code=400, detail=f"Invalid order type: {order_type}")
        
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "message": f"Order failed: {result.comment}"}
        
        return {"success": True, "order": result.order, "message": "Pending order placed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{ticket}")
async def cancel_order(ticket: int):
    """Cancel a pending order"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "message": f"Cancel failed: {result.comment}"}
        
        return {"success": True, "message": f"Order {ticket} cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def find_symbol(symbol: str) -> str:
    """
    Find symbol in MT5, trying variations if not found directly.
    Handles cases like AUDJPY -> AUDJPY.u or AUDJPYm
    """
    # First try exact match
    info = mt5.symbol_info(symbol)
    if info is not None:
        return symbol
    
    # Try common suffixes
    suffixes = ['.u', 'u', 'm', '.m', 'T', '.raw', 'raw']
    for suffix in suffixes:
        test_symbol = f"{symbol}{suffix}"
        info = mt5.symbol_info(test_symbol)
        if info is not None:
            return test_symbol
    
    # Try to find similar symbol
    all_symbols = mt5.symbols_get()
    if all_symbols:
        symbol_upper = symbol.upper()
        for s in all_symbols:
            if s.name.upper().startswith(symbol_upper):
                return s.name
    
    return symbol  # Return original if nothing found


@router.post("/execute")
async def execute_market_order(order: dict):
    """
    Execute a market order directly from AI signal
    This is used by AYDP AI to execute trades
    """
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbol = order.get("symbol")
        trade_type = order.get("trade_type")  # BUY or SELL
        volume = order.get("volume", 0.01)
        sl = order.get("sl", 0)
        tp = order.get("tp", 0)
        comment = order.get("comment", "AYDP AI Trade")
        
        if not symbol or not trade_type:
            raise HTTPException(status_code=400, detail="symbol and trade_type are required")
        
        # Find the correct symbol name in MT5
        mt5_symbol = find_symbol(symbol)
        
        # Get current tick
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick is None:
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not found (tried {mt5_symbol})")
        
        # Determine order type and price
        if trade_type.upper() == "BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            mt5_order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        
        # Check symbol filling mode
        symbol_info = mt5.symbol_info(mt5_symbol)
        filling_type = mt5.ORDER_FILLING_IOC
        if symbol_info:
            if symbol_info.filling_mode & mt5.ORDER_FILLING_FOK:
                filling_type = mt5.ORDER_FILLING_FOK
            elif symbol_info.filling_mode & mt5.ORDER_FILLING_RETURN:
                filling_type = mt5.ORDER_FILLING_RETURN
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": mt5_symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "error": f"Order failed: {result.comment}", "retcode": result.retcode}
        
        return {
            "success": True,
            "ticket": result.order,
            "message": f"Order executed successfully: {result.order}",
            "price": price,
            "volume": volume
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/limit")
async def place_limit_order(order: dict):
    """Place a limit order"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbol = order.get("symbol")
        trade_type = order.get("trade_type")  # BUY or SELL
        volume = order.get("volume", 0.01)
        price = order.get("price")
        sl = order.get("sl", 0)
        tp = order.get("tp", 0)
        comment = order.get("comment", "AYDP AI Limit")
        
        if not symbol or not trade_type or not price:
            raise HTTPException(status_code=400, detail="symbol, trade_type, and price are required")
        
        # Determine order type
        if trade_type.upper() == "BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            mt5_order_type = mt5.ORDER_TYPE_SELL_LIMIT
        
        # Check symbol filling mode
        symbol_info = mt5.symbol_info(symbol)
        filling_type = mt5.ORDER_FILLING_RETURN
        if symbol_info:
            if symbol_info.filling_mode & mt5.ORDER_FILLING_FOK:
                filling_type = mt5.ORDER_FILLING_FOK
            elif symbol_info.filling_mode & mt5.ORDER_FILLING_IOC:
                filling_type = mt5.ORDER_FILLING_IOC
        
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "error": f"Order failed: {result.comment}", "retcode": result.retcode}
        
        return {
            "success": True,
            "ticket": result.order,
            "message": f"Limit order placed: {result.order}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
