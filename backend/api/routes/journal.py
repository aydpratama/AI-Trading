"""
Trade Journal API Routes - Performance tracking & analytics
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
from database import get_db
from sqlalchemy.orm import Session
from ai.trade_journal import trade_journal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.get("/analytics")
async def get_analytics(
    days: int = Query(default=30, ge=1, le=365),
    symbol: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive trading analytics.
    
    Parameters:
    - days: Number of days to analyze (default 30)
    - symbol: Filter by specific symbol (optional)
    """
    try:
        analytics = trade_journal.get_analytics(db, days=days, symbol=symbol)
        return JSONResponse(content={
            "status": "success",
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_trades(db: Session = Depends(get_db)):
    """Get all active (open) journal entries"""
    try:
        trades = trade_journal.get_active_trades(db)
        return JSONResponse(content={
            "status": "success",
            "data": trades,
            "count": len(trades)
        })
    except Exception as e:
        logger.error(f"Active trades error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-open")
async def log_trade_open(trade_data: dict, db: Session = Depends(get_db)):
    """Log a new trade opening in the journal"""
    try:
        entry = trade_journal.log_trade_open(db, trade_data)
        return JSONResponse(content={
            "status": "success",
            "data": entry.to_dict(),
            "message": f"Trade logged: {entry.direction} {entry.symbol}"
        })
    except Exception as e:
        logger.error(f"Log trade open error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-close/{journal_id}")
async def log_trade_close(journal_id: int, close_data: dict, db: Session = Depends(get_db)):
    """Log a trade closing in the journal"""
    try:
        entry = trade_journal.log_trade_close(db, journal_id, close_data)
        if not entry:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        return JSONResponse(content={
            "status": "success",
            "data": entry.to_dict(),
            "message": f"Trade closed: {entry.outcome} ${entry.profit:.2f}"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log trade close error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
