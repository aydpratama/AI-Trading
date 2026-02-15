"""Trade history model for SQLite"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from models.base import BaseModel


class Trade(BaseModel):
    """Closed trade history model"""
    __tablename__ = "trades"

    ticket = Column(Integer, unique=True, nullable=False)
    symbol = Column(String(10), nullable=False)
    type = Column(String(10), nullable=False)
    volume = Column(Float, nullable=False)
    entry = Column(Float, nullable=False)
    exit = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    pnl = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    status = Column(String(10), nullable=False)
    open_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime, nullable=False)
    timeframe = Column(String(5), nullable=False)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
