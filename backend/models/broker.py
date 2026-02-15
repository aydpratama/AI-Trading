"""Broker configuration models"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum


class BrokerType(str, Enum):
    DEMO = "demo"
    LIVE = "live"


class BrokerInfo(BaseModel):
    """Broker information from MT5"""
    name: str
    server: str
    company: str
    leverage: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    currency: str = "USD"
    broker_type: BrokerType = BrokerType.DEMO


class BrokerConfig(BaseModel):
    """Broker configuration for multiple accounts"""
    id: str
    name: str
    server: str
    login: int
    password: str  # Will be encrypted in production
    is_active: bool = False


class InstrumentInfo(BaseModel):
    """Trading instrument information"""
    symbol: str
    description: str
    tick_size: float
    tick_value: float
    point: float
    spread: float
    digits: int
    contract_size: float
    min_lot: float = 0.01
    max_lot: float = 100.0
    lot_step: float = 0.01
    stop_level: float = 0
    margin_initial: float = 0
    margin_maintenance: float = 0


# Connected brokers only - populated from .env configuration
# This will show only brokers that are actually configured and connected
DEFAULT_BROKERS: Dict[str, dict] = {}

def update_connected_broker(broker_id: str, name: str, server: str):
    """Update the connected broker list"""
    DEFAULT_BROKERS[broker_id] = {
        "name": name,
        "server": server,
        "description": f"{name} Account"
    }

def clear_brokers():
    """Clear all brokers"""
    DEFAULT_BROKERS.clear()
