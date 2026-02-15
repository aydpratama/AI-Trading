"""Account model for SQLite"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from models.base import BaseModel


class Account(BaseModel):
    """MT5 account information model"""
    __tablename__ = "accounts"

    login = Column(Integer, unique=True, nullable=False, index=True)
    balance = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    margin = Column(Float, nullable=False)
    free_margin = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    server = Column(String(100), nullable=False)
    last_update = Column(DateTime, nullable=False)
