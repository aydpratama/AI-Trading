"""
Market Data API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import MetaTrader5 as mt5
from mt5.connector import connector

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/health")
async def health_check():
    """Check MT5 connection health"""
    try:
        connected = connector.is_connected()
        return {
            "status": "healthy" if connected else "unhealthy",
            "mt5_connected": connected,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "mt5_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/account")
async def get_account():
    """Get account information"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        account_info = mt5.account_info()
        if account_info is None:
            raise HTTPException(status_code=404, detail="Account info not available")
        
        return {
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "profit": account_info.profit,
            "currency": account_info.currency,
            "leverage": account_info.leverage,
            "server": account_info.server,
            "name": account_info.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brokers")
async def get_brokers():
    """Get broker information"""
    try:
        connected = connector.is_connected()
        
        if connected:
            account_info = mt5.account_info()
            return {
                "current": {
                    "connected": True,
                    "server": account_info.server if account_info else "Unknown",
                    "company": account_info.company if account_info else "Unknown",
                    "login": account_info.login if account_info else None
                },
                "available": []
            }
        return {
            "current": {"connected": False, "server": None},
            "available": []
        }
    except Exception as e:
        return {
            "current": {"connected": False, "server": None, "error": str(e)},
            "available": []
        }

@router.get("/symbols")
async def get_symbols():
    """Get all available symbols"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        
        result = []
        for s in symbols[:500]:  # Limit to 500 symbols
            category = "other"
            if "USD" in s.name or "EUR" in s.name or "GBP" in s.name or "JPY" in s.name:
                if "XAU" not in s.name and "XAG" not in s.name:
                    category = "forex"
            elif "XAU" in s.name:
                category = "metals"
            elif "XAG" in s.name:
                category = "metals"
            elif any(idx in s.name for idx in ["US30", "US500", "US100", "DE30", "UK100", "JP225"]):
                category = "indices"
            elif "BTC" in s.name or "ETH" in s.name:
                category = "crypto"
            
            result.append({
                "name": s.name,
                "description": s.description,
                "category": category,
                "digits": s.digits,
                "point": s.point,
                "trade_contract_size": s.trade_contract_size
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/candles")
async def get_candles(
    symbol: str = Query(...),
    timeframe: str = Query(default="1H"),
    count: int = Query(default=500)
):
    """Get candlestick data"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        # Map timeframe string to MT5 constant
        tf_map = {
            "1M": mt5.TIMEFRAME_M1,
            "5M": mt5.TIMEFRAME_M5,
            "15M": mt5.TIMEFRAME_M15,
            "30M": mt5.TIMEFRAME_M30,
            "1H": mt5.TIMEFRAME_H1,
            "4H": mt5.TIMEFRAME_H4,
            "1D": mt5.TIMEFRAME_D1,
        }
        
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        # Normalize symbol for broker (add suffix if needed)
        normalized_symbol = connector._normalize_symbol(symbol)
        
        # Ensure symbol is visible in Market Watch
        if not mt5.symbol_select(normalized_symbol, True):
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not available")
        
        # Get symbol info for digits
        symbol_info = mt5.symbol_info(normalized_symbol)
        digits = symbol_info.digits if symbol_info else 5
        
        # Get candles
        candles = mt5.copy_rates_from_pos(normalized_symbol, tf, 0, count)
        if candles is None:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        
        result = []
        for c in candles:
            result.append({
                "time": int(c['time']),
                "open": float(c['open']),
                "high": float(c['high']),
                "low": float(c['low']),
                "close": float(c['close']),
                "tick_volume": int(c['tick_volume']),
                "volume": int(c['real_volume']) if c['real_volume'] > 0 else int(c['tick_volume'])
            })
        
        return {"candles": result, "digits": digits}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prices")
async def get_prices(symbols: str = Query(...)):
    """Get current prices for symbols"""
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 not connected")
        
        symbol_list = symbols.split(",")
        result = {}
        
        for symbol in symbol_list:
            tick = mt5.symbol_info_tick(symbol.strip())
            if tick:
                symbol_info = mt5.symbol_info(symbol.strip())
                digits = symbol_info.digits if symbol_info else 5
                result[symbol.strip()] = {
                    "bid": round(tick.bid, digits),
                    "ask": round(tick.ask, digits),
                    "spread": round((tick.ask - tick.bid) * (10 ** digits), 1),
                    "time": int(tick.time)
                }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login_broker(data: dict):
    """Login to broker"""
    try:
        login = data.get("login")
        password = data.get("password")
        server = data.get("server")
        
        if not all([login, password, server]):
            raise HTTPException(status_code=400, detail="Missing credentials")
        
        success = connector.login(int(login), password, server)
        
        if success:
            return {"success": True, "message": "Login successful"}
        return {"success": False, "message": "Login failed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))