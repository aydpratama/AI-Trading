"""Database engine and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from models.base import Base

# Create SQLite engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # For SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from models.position import Position
    from models.trade import Trade
    from models.signal import Signal
    from models.account import Account
    from models.backtest import Backtest, BacktestTrade
    from ai.trade_journal import JournalEntry

    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized")
