"""Position model for SQLite"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from models.base import BaseModel


class Position(BaseModel):
    """Trading position model"""
    __tablename__ = "positions"

    ticket = Column(Integer, unique=True, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # BUY, SELL
    volume = Column(Float, nullable=False)
    entry = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    current = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0)
    margin = Column(Float, nullable=False)
    profit = Column(Float, default=0.0)
    status = Column(String(10), nullable=False, default="OPEN")  # OPEN, CLOSED
    open_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime, nullable=True)
    timeframe = Column(String(5), nullable=False)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
