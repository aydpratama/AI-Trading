"""Main entry point for MT5 backend"""
import MetaTrader5 as mt5
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import signal
import sys

from config import settings
from mt5.connector import connector
from mt5.position_manager import position_manager
from database import init_db
from notification.telegram import telegram_notifier
from api.routes import market, positions, orders, signals, ai, backtest, journal
from api.websocket import ws_manager
from fastapi import WebSocket

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("=" * 50)
    logger.info("🚀 Starting AI Trading Backend...")
    logger.info("=" * 50)

    # Initialize database
    init_db()

    # Connect to MT5
    if connector.connect():
        logger.info("✅ Connected to MT5 successfully!")
    else:
        logger.error("❌ Failed to connect to MT5")

    # Get and display account info
    account = connector.get_account_info()
    if account:
        logger.info(f"Account: {account['login']} @ {account['server']}")
        logger.info(f"Balance: ${account['balance']:.2f}")
        logger.info(f"Equity: ${account['equity']:.2f}")

    # Start Telegram bot if configured
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        logger.info("📱 Starting Telegram bot...")
        telegram_notifier.start_bot()
    else:
        logger.warning("⚠️ Telegram bot not configured")

    yield

    # Shutdown
    logger.info("🛑 Shutting down AI Trading Backend...")
    connector.disconnect()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Trading Backend",
    description="Backend untuk MT5 trading dengan AI signals (EURUSD + Telegram)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (prefix already defined in route files)
app.include_router(market.router)
app.include_router(positions.router)
app.include_router(orders.router)
app.include_router(signals.router)
app.include_router(ai.router)
app.include_router(backtest.router)
app.include_router(journal.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for realtime market data streaming"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for any client messages
            data = await websocket.receive_text()
            # Client can send commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except Exception as e:
        logger.info(f"WebSocket disconnected: {e}")
    finally:
        ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "name": "AI Trading Backend",
        "version": "1.0.0",
        "mt5_connected": connector.is_connected(),
        "endpoints": {
            "health": "/api/market/health",
            "prices": "/api/market/prices",
            "candles": "/api/market/candles",
            "signals": "/api/signals",
            "positions": "/api/positions",
            "orders": "/api/orders"
        }
    }


# Health check endpoint is in market.py router


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("\n👋 Received shutdown signal...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
try:
    signal.signal(signal.SIGTERM, signal_handler)
except (OSError, AttributeError):
    pass  # SIGTERM not available on Windows


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
