"""Signal model for SQLite"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from models.base import BaseModel


class Signal(BaseModel):
    """Trading signal model"""
    __tablename__ = "signals"

    symbol = Column(String(10), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # BUY, SELL
    timeframe = Column(String(5), nullable=False)
    entry = Column(Float, nullable=False)
    sl = Column(Float, nullable=False)
    tp = Column(Float, nullable=False)
    risk_reward = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    indicators = Column(Text, nullable=True)
    support_resistance = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(10), nullable=False, default="PENDING")  # PENDING, EXECUTED, REJECTED
    executed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
