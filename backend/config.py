"""Configuration module for MT5 backend"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # MT5 Connection - NO hardcoded defaults for security
    MT5_LOGIN: int = 0
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = ""
    MT5_PATH: str = r"C:\Program Files\MetaTrader 5"

    # WebSocket
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8765

    # REST API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Database
    DATABASE_URL: str = "sqlite:///./aitrading.db"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Risk Management
    MAX_POSITION_SIZE_PERCENT: float = 2.0
    MAX_TOTAL_EXPOSURE_PERCENT: float = 10.0
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    MIN_RISK_REWARD: float = 1.5
    MAX_OPEN_POSITIONS: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
