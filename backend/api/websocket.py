"""
WebSocket Manager for Realtime MT5 Data Streaming
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import MetaTrader5 as mt5


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._streaming_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")
        
        # Start streaming if first client
        if len(self.active_connections) == 1 and self._streaming_task is None:
            self._streaming_task = asyncio.create_task(self._stream_market_data())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")
        
        # Stop streaming if no clients
        if len(self.active_connections) == 0 and self._streaming_task:
            self._streaming_task.cancel()
            self._streaming_task = None

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] Error sending: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for dc in dead_connections:
            if dc in self.active_connections:
                self.active_connections.remove(dc)

    async def _stream_market_data(self):
        """Stream realtime market data to all clients"""
        print("[WS] Starting market data stream...")
        
        while True:
            try:
                if not self.active_connections:
                    await asyncio.sleep(1)
                    continue
                
                # Get current prices for common symbols
                symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30", "US500"]
                prices = {}
                
                for symbol in symbols:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        prices[symbol] = {
                            "bid": tick.bid,
                            "ask": tick.ask,
                            "spread": round((tick.ask - tick.bid) * 100000, 1) if "JPY" not in symbol else round((tick.ask - tick.bid) * 100, 1),
                            "time": tick.time
                        }
                
                # Get positions with realtime PnL
                positions = mt5.positions_get()
                positions_data = []
                total_pnl = 0.0
                
                if positions:
                    for pos in positions:
                        pnl = pos.profit
                        total_pnl += pnl
                        positions_data.append({
                            "ticket": pos.ticket,
                            "symbol": pos.symbol,
                            "type": "BUY" if pos.type == 0 else "SELL",
                            "volume": pos.volume,
                            "entry": pos.price_open,
                            "current": pos.price_current,
                            "sl": pos.sl,
                            "tp": pos.tp,
                            "pnl": round(pnl, 2),
                            "swap": getattr(pos, 'swap', 0) or 0,
                        })
                
                # Get account info
                account = mt5.account_info()
                account_data = None
                if account:
                    account_data = {
                        "balance": account.balance,
                        "equity": account.equity,
                        "margin": account.margin,
                        "free_margin": account.margin_free,
                        "margin_level": account.margin_level if account.margin > 0 else 0,
                        "leverage": account.leverage
                    }
                
                # Broadcast to all clients
                await self.broadcast({
                    "type": "market_update",
                    "prices": prices,
                    "positions": positions_data,
                    "total_pnl": round(total_pnl, 2),
                    "account": account_data,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Stream every 500ms for smooth updates
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                print("[WS] Stream cancelled")
                break
            except Exception as e:
                print(f"[WS] Stream error: {e}")
                await asyncio.sleep(1)


# Global manager instance
ws_manager = ConnectionManager()