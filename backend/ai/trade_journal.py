"""
Trade Journal - Performance Tracking & Analytics

Records all trades and provides detailed performance analytics:
- Trade logging with full entry/exit details
- Win rate, profit factor, expectancy calculations
- Streak tracking (win/loss streaks)
- Per-symbol and per-timeframe performance
- Drawdown analysis
- Monthly/weekly P&L breakdown
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import Session
from models.base import Base
import json
import logging

logger = logging.getLogger(__name__)


class JournalEntry(Base):
    """SQLAlchemy model for trade journal entries"""
    __tablename__ = "trade_journal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Trade identification
    ticket = Column(Integer, nullable=True)  # MT5 ticket
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), default="H1")
    
    # Trade details
    direction = Column(String(4), nullable=False)  # BUY or SELL
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    lot_size = Column(Float, default=0.01)
    
    # Results
    profit = Column(Float, default=0)
    profit_pips = Column(Float, default=0)
    risk_reward_actual = Column(Float, default=0)
    outcome = Column(String(10), nullable=True)  # WIN, LOSS, BREAKEVEN
    
    # Signal data
    signal_confidence = Column(Float, default=0)
    signal_reasons = Column(Text, nullable=True)  # JSON string
    score_breakdown = Column(Text, nullable=True)  # JSON string
    
    # Timing
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    
    # Session & context
    session_quality = Column(String(10), nullable=True)
    market_structure = Column(String(20), nullable=True)
    smc_bias = Column(String(10), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    tags = Column(String(200), nullable=True)
    
    # Flags
    is_active = Column(Boolean, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ticket": self.ticket,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "lot_size": self.lot_size,
            "profit": self.profit,
            "profit_pips": self.profit_pips,
            "risk_reward_actual": self.risk_reward_actual,
            "outcome": self.outcome,
            "signal_confidence": self.signal_confidence,
            "signal_reasons": json.loads(self.signal_reasons) if self.signal_reasons else [],
            "score_breakdown": json.loads(self.score_breakdown) if self.score_breakdown else {},
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "duration_minutes": self.duration_minutes,
            "session_quality": self.session_quality,
            "market_structure": self.market_structure,
            "smc_bias": self.smc_bias,
            "notes": self.notes,
            "tags": self.tags,
            "is_active": self.is_active
        }


class TradeJournal:
    """Trade Journal service for recording and analyzing trades"""

    def log_trade_open(self, db: Session, trade_data: Dict[str, Any]) -> JournalEntry:
        """Log a new trade opening"""
        entry = JournalEntry(
            ticket=trade_data.get("ticket"),
            symbol=trade_data.get("symbol", ""),
            timeframe=trade_data.get("timeframe", "H1"),
            direction=trade_data.get("direction", "BUY"),
            entry_price=trade_data.get("entry_price", 0),
            stop_loss=trade_data.get("stop_loss"),
            take_profit=trade_data.get("take_profit"),
            lot_size=trade_data.get("lot_size", 0.01),
            signal_confidence=trade_data.get("signal_confidence", 0),
            signal_reasons=json.dumps(trade_data.get("signal_reasons", [])),
            score_breakdown=json.dumps(trade_data.get("score_breakdown", {})),
            session_quality=trade_data.get("session_quality"),
            market_structure=trade_data.get("market_structure"),
            smc_bias=trade_data.get("smc_bias"),
            notes=trade_data.get("notes"),
            tags=trade_data.get("tags"),
            is_active=True
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info(f"Trade journal: Opened {entry.direction} {entry.symbol} @ {entry.entry_price}")
        return entry

    def log_trade_close(self, db: Session, journal_id: int, close_data: Dict[str, Any]) -> Optional[JournalEntry]:
        """Log a trade closing"""
        entry = db.query(JournalEntry).filter(JournalEntry.id == journal_id).first()
        if not entry:
            return None

        entry.exit_price = close_data.get("exit_price", 0)
        entry.profit = close_data.get("profit", 0)
        entry.profit_pips = close_data.get("profit_pips", 0)
        entry.closed_at = datetime.utcnow()
        entry.is_active = False
        
        # Calculate duration
        if entry.opened_at:
            delta = entry.closed_at - entry.opened_at
            entry.duration_minutes = int(delta.total_seconds() / 60)
        
        # Calculate actual R:R
        risk = abs(entry.entry_price - entry.stop_loss) if entry.stop_loss else 0
        if risk > 0 and entry.exit_price:
            if entry.direction == "BUY":
                reward = entry.exit_price - entry.entry_price
            else:
                reward = entry.entry_price - entry.exit_price
            entry.risk_reward_actual = round(reward / risk, 2)
        
        # Determine outcome
        if entry.profit > 0:
            entry.outcome = "WIN"
        elif entry.profit < 0:
            entry.outcome = "LOSS"
        else:
            entry.outcome = "BREAKEVEN"
        
        entry.notes = close_data.get("notes", entry.notes)
        
        db.commit()
        db.refresh(entry)
        logger.info(f"Trade journal: Closed {entry.symbol} P&L: {entry.profit}")
        return entry

    def get_analytics(self, db: Session, days: int = 30, symbol: str = None) -> Dict[str, Any]:
        """Get comprehensive trading analytics"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(JournalEntry).filter(
            JournalEntry.is_active == False,
            JournalEntry.closed_at >= cutoff
        )
        if symbol:
            query = query.filter(JournalEntry.symbol == symbol)
        
        trades = query.order_by(JournalEntry.closed_at.desc()).all()
        
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_profit": 0,
                "message": "No closed trades in this period"
            }
        
        # Basic stats
        wins = [t for t in trades if t.outcome == "WIN"]
        losses = [t for t in trades if t.outcome == "LOSS"]
        
        total = len(trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total * 100) if total > 0 else 0
        
        # Profit stats
        total_profit = sum(t.profit for t in trades)
        gross_profit = sum(t.profit for t in wins)
        gross_loss = abs(sum(t.profit for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        avg_win = (gross_profit / win_count) if win_count > 0 else 0
        avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0
        
        # Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)
        
        # Streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        temp_win = 0
        temp_loss = 0
        
        for t in reversed(trades):
            if t.outcome == "WIN":
                temp_win += 1
                temp_loss = 0
                max_win_streak = max(max_win_streak, temp_win)
            elif t.outcome == "LOSS":
                temp_loss += 1
                temp_win = 0
                max_loss_streak = max(max_loss_streak, temp_loss)
        
        # Current streak
        for t in trades:
            if t.outcome == trades[0].outcome:
                current_streak += 1
            else:
                break
        
        # Per-symbol breakdown
        symbol_stats = {}
        for t in trades:
            s = t.symbol
            if s not in symbol_stats:
                symbol_stats[s] = {"trades": 0, "wins": 0, "profit": 0}
            symbol_stats[s]["trades"] += 1
            if t.outcome == "WIN":
                symbol_stats[s]["wins"] += 1
            symbol_stats[s]["profit"] += t.profit
        
        for s in symbol_stats:
            stats = symbol_stats[s]
            stats["win_rate"] = round(stats["wins"] / stats["trades"] * 100, 1) if stats["trades"] > 0 else 0
            stats["profit"] = round(stats["profit"], 2)
        
        # Best/worst trades
        best_trade = max(trades, key=lambda t: t.profit)
        worst_trade = min(trades, key=lambda t: t.profit)
        
        # Average duration
        durations = [t.duration_minutes for t in trades if t.duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Average confidence of winning vs losing trades
        avg_win_confidence = sum(t.signal_confidence for t in wins) / len(wins) if wins else 0
        avg_loss_confidence = sum(t.signal_confidence for t in losses) / len(losses) if losses else 0
        
        return {
            "period_days": days,
            "total_trades": total,
            "wins": win_count,
            "losses": loss_count,
            "breakeven": total - win_count - loss_count,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "total_profit": round(total_profit, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "best_trade": {
                "symbol": best_trade.symbol,
                "profit": round(best_trade.profit, 2),
                "direction": best_trade.direction
            },
            "worst_trade": {
                "symbol": worst_trade.symbol,
                "profit": round(worst_trade.profit, 2),
                "direction": worst_trade.direction
            },
            "streaks": {
                "current": current_streak,
                "current_type": trades[0].outcome if trades else "NONE",
                "max_win": max_win_streak,
                "max_loss": max_loss_streak
            },
            "avg_duration_minutes": round(avg_duration, 0),
            "avg_win_confidence": round(avg_win_confidence, 1),
            "avg_loss_confidence": round(avg_loss_confidence, 1),
            "symbol_breakdown": symbol_stats,
            "recent_trades": [t.to_dict() for t in trades[:10]]
        }

    def get_active_trades(self, db: Session) -> List[Dict]:
        """Get all active (open) journal entries"""
        entries = db.query(JournalEntry).filter(JournalEntry.is_active == True).all()
        return [e.to_dict() for e in entries]


# Singleton
trade_journal = TradeJournal()
