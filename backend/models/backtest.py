"""Backtest models for SQLite"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from models.base import BaseModel
from datetime import datetime


class Backtest(BaseModel):
    """Backtest session model - stores configuration and results"""
    __tablename__ = "backtests"

    # Backtest parameters
    symbol = Column(String(10), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False, index=True)
    strategy = Column(String(50), nullable=False)  # GENIUS_AI, AI, CUSTOM
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Risk parameters
    risk_level = Column(String(20), nullable=False, default="moderate")
    risk_percentage = Column(Float, nullable=True)  # Explicit risk %
    initial_capital = Column(Float, nullable=False, default=10000)
    slippage_pips = Column(Float, nullable=False, default=1.0)
    spread_pips = Column(Float, nullable=False, default=1.0)

    # Status
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, ERROR
    progress = Column(Integer, nullable=False, default=0)  # Progress percentage
    error_message = Column(Text, nullable=True)

    # Results - Basic metrics
    total_trades = Column(Integer, nullable=False, default=0)
    winning_trades = Column(Integer, nullable=False, default=0)
    losing_trades = Column(Integer, nullable=False, default=0)
    break_even_trades = Column(Integer, nullable=False, default=0)
    win_rate = Column(Float, nullable=False, default=0)  # Percentage
    profit_factor = Column(Float, nullable=True)

    # Results - Financial metrics
    total_profit = Column(Float, nullable=False, default=0)
    total_loss = Column(Float, nullable=False, default=0)
    net_profit = Column(Float, nullable=False, default=0)
    net_profit_pct = Column(Float, nullable=False, default=0)  # Percentage of initial capital
    avg_profit = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    avg_trade = Column(Float, nullable=True)

    # Results - Risk metrics
    max_drawdown = Column(Float, nullable=False, default=0)
    max_drawdown_pct = Column(Float, nullable=False, default=0)
    avg_drawdown = Column(Float, nullable=True)

    # Results - Performance ratios
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    expectancy = Column(Float, nullable=True)
    profit_expectancy_pct = Column(Float, nullable=True)  # Expectancy as %

    # Results - Trade statistics
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)
    avg_winner = Column(Float, nullable=True)
    avg_loser = Column(Float, nullable=True)
    avg_win_pips = Column(Float, nullable=True)
    avg_loss_pips = Column(Float, nullable=True)

    # Results - Risk/Reward statistics
    avg_risk_reward = Column(Float, nullable=True)
    best_rr = Column(Float, nullable=True)
    worst_rr = Column(Float, nullable=True)

    # Results - Time statistics
    longest_winning_streak = Column(Integer, nullable=False, default=0)
    longest_losing_streak = Column(Integer, nullable=False, default=0)
    avg_trade_duration = Column(Float, nullable=True)  # In hours

    # Results - Exit statistics
    tp_hits = Column(Integer, nullable=False, default=0)
    sl_hits = Column(Integer, nullable=False, default=0)
    manual_exits = Column(Integer, nullable=False, default=0)
    timeout_exits = Column(Integer, nullable=False, default=0)

    # AI Configuration (for AI strategy)
    ai_provider = Column(String(20), nullable=True)  # gemini, openai, kimi, zai
    ai_model = Column(String(50), nullable=True)

    # Additional metadata
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Compressed trade data (for quick summary)
    trade_summary = Column(JSON, nullable=True)  # Stores aggregated trade data


class BacktestTrade(BaseModel):
    """Individual trade within a backtest"""
    __tablename__ = "backtest_trades"

    # Link to backtest
    backtest_id = Column(String(36), nullable=False, index=True)

    # Trade details
    symbol = Column(String(10), nullable=False)
    direction = Column(String(10), nullable=False)  # BUY, SELL
    lot_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)

    # Trade results
    pnl = Column(Float, nullable=False)
    pnl_pct = Column(Float, nullable=True)
    pips = Column(Float, nullable=True)

    # Trade timing
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Float, nullable=True)
    duration_hours = Column(Float, nullable=True)

    # Exit reason
    exit_reason = Column(String(50), nullable=False)  # TP_HIT, SL_HIT, TIMEOUT, MANUAL
    exit_candle_index = Column(Integer, nullable=True)  # Position in candle series

    # Trade analysis (from system)
    entry_confidence = Column(Float, nullable=True)  # Signal confidence at entry
    risk_reward = Column(Float, nullable=True)
    sl_distance_pips = Column(Float, nullable=True)
    tp_distance_pips = Column(Float, nullable=True)

    # Trade context
    session = Column(String(20), nullable=True)  # trading session
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday
    hour_of_day = Column(Integer, nullable=True)  # 0-23

    # Pattern/Indicator context (what triggered the trade)
    trigger_patterns = Column(JSON, nullable=True)  # List of pattern names
    trigger_rsi = Column(Float, nullable=True)
    trigger_macd = Column(Float, nullable=True)
    trigger_adx = Column(Float, nullable=True)

    # Market context at entry
    spread_at_entry = Column(Float, nullable=True)
    atr_at_entry = Column(Float, nullable=True)
    volatility_at_entry = Column(String(20), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
