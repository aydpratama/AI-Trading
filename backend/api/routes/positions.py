"""
Positions API Routes
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
import MetaTrader5 as mt5
from mt5.connector import connector

router = APIRouter(prefix="/api/positions", tags=["positions"])

@router.get("/")
async def get_positions():
    """Get all open positions"""
    try:
        if not connector.is_connected():
            return []  # Return empty instead of error when not connected
        
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            return []
        
        result = []
        for pos in positions:
            try:
                open_time = ""
                try:
                    open_time = datetime.fromtimestamp(pos.time).isoformat()
                except:
                    open_time = str(pos.time)
                
                result.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "entry": pos.price_open,
                    "current": pos.price_current,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "profit": pos.profit,
                    "swap": pos.swap,
                    "comment": pos.comment if pos.comment else "",
                    "open_time": open_time
                })
            except Exception as pe:
                print(f"Error processing position {pos.ticket}: {pe}")
                continue
        
        return result
    except Exception as e:
        print(f"Error in get_positions: {e}")
        return []  # Return empty instead of error

@router.post("/close/{ticket}")
async def close_position(ticket: int):
    """Close a position"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        # Get position info
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            raise HTTPException(status_code=404, detail=f"Position {ticket} not found")
        
        pos = position[0]
        
        # Close by opposite order
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": mt5.symbol_info_tick(pos.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(pos.symbol).ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "message": f"Failed to close: {result.comment}"}
        
        return {"success": True, "message": f"Position {ticket} closed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/modify/{ticket}")
async def modify_position(ticket: int, data: dict):
    """Modify position SL/TP"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        # Get position info
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            raise HTTPException(status_code=404, detail=f"Position {ticket} not found")
        
        pos = position[0]
        
        sl = data.get("sl", pos.sl)
        tp = data.get("tp", pos.tp)
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": pos.symbol,
            "sl": sl,
            "tp": tp,
            "comment": "Modify SL/TP",
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"success": False, "message": f"Failed to modify: {result.comment}"}
        
        return {"success": True, "message": f"Position {ticket} modified"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))