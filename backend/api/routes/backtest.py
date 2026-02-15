"""Backtest API Routes - Run and manage trading strategy backtests"""
import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ai.backtester import backtester
from ai.historical_data import historical_data_manager
from database import SessionLocal
from models.backtest import Backtest, BacktestTrade

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["backtest"])


# === Request Models ===

class BacktestRequest(BaseModel):
    """Request model for running a backtest"""
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD, XAUUSD)")
    timeframe: str = Field(default="H1", description="Chart timeframe (M5, M15, H1, H4, D1)")
    strategy: str = Field(..., description="Strategy type: GENIUS_AI, AI, CUSTOM")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(default=10000, description="Starting capital")
    risk_level: str = Field(default="moderate", description="Risk level: conservative, moderate, aggressive")
    risk_percentage: Optional[float] = Field(default=None, description="Explicit risk percentage")
    slippage_pips: float = Field(default=1.0, description="Slippage in pips")
    spread_pips: float = Field(default=1.0, description="Spread in pips")
    ai_provider: Optional[str] = Field(default=None, description="AI provider for AI strategy")
    ai_model: Optional[str] = Field(default=None, description="AI model to use")
    api_key: Optional[str] = Field(default=None, description="API key for AI provider")
    notes: Optional[str] = Field(default=None, description="Backtest notes")


class CompareRequest(BaseModel):
    """Request model for comparing backtests"""
    backtest_ids: List[str] = Field(..., description="List of backtest IDs to compare")


# === API Endpoints ===

@router.post("/run")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Start a new backtest

    The backtest runs in the background. Use GET /api/backtest/{id} to check status.
    """
    try:
        # Validate dates
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        # Validate strategy
        valid_strategies = ["GENIUS_AI", "AI", "CUSTOM"]
        if request.strategy.upper() not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
            )

        # Check if historical data exists
        date_range = historical_data_manager.get_date_range(request.symbol, request.timeframe)
        if not date_range:
            # Download historical data
            logger.info(f"Downloading historical data for {request.symbol} {request.timeframe}")
            count = historical_data_manager.download_from_mt5(
                symbol=request.symbol,
                timeframe=request.timeframe,
                max_candles=5000
            )
            if count < 100:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient historical data available for {request.symbol} {request.timeframe}"
                )

        # Create backtest record
        backtest_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            backtest = Backtest(
                id=backtest_id,
                symbol=request.symbol,
                timeframe=request.timeframe,
                strategy=request.strategy.upper(),
                start_date=start_date,
                end_date=end_date,
                risk_level=request.risk_level,
                risk_percentage=request.risk_percentage,
                initial_capital=request.initial_capital,
                slippage_pips=request.slippage_pips,
                spread_pips=request.spread_pips,
                ai_provider=request.ai_provider,
                ai_model=request.ai_model,
                status="PENDING",
                progress=0,
                notes=request.notes
            )
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
        finally:
            db.close()

        # Define progress callback
        def update_progress(progress: int, message: str):
            db = SessionLocal()
            try:
                bt = db.query(Backtest).filter(Backtest.id == backtest_id).first()
                if bt:
                    bt.progress = progress
                    db.commit()
            finally:
                db.close()
            logger.info(f"Backtest {backtest_id}: {progress}% - {message}")

        # Run backtest in background
        def run_backtest_bg():
            try:
                backtester.run_backtest(
                    backtest_id=backtest_id,
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    strategy=request.strategy.upper(),
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=request.initial_capital,
                    risk_level=request.risk_level,
                    risk_percentage=request.risk_percentage,
                    slippage_pips=request.slippage_pips,
                    spread_pips=request.spread_pips,
                    ai_provider=request.ai_provider,
                    ai_model=request.ai_model,
                    api_key=request.api_key,
                    update_progress=update_progress
                )
            except Exception as e:
                logger.error(f"Backtest error: {e}")
                # Update status to ERROR
                db = SessionLocal()
                try:
                    bt = db.query(Backtest).filter(Backtest.id == backtest_id).first()
                    if bt:
                        bt.status = "ERROR"
                        bt.error_message = str(e)
                        db.commit()
                finally:
                    db.close()

        background_tasks.add_task(run_backtest_bg)

        return {
            "success": True,
            "backtest_id": backtest_id,
            "message": "Backtest started",
            "status": "PENDING"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_backtests(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    """
    List all backtests with optional filters

    Filters:
    - symbol: Filter by trading symbol
    - timeframe: Filter by timeframe
    - strategy: Filter by strategy
    - status: Filter by status (PENDING, RUNNING, COMPLETED, ERROR)
    - limit: Maximum results to return
    """
    try:
        db = SessionLocal()
        try:
            query = db.query(Backtest)

            # Apply filters
            if symbol:
                query = query.filter(Backtest.symbol == symbol.upper())
            if timeframe:
                query = query.filter(Backtest.timeframe == timeframe.upper())
            if strategy:
                query = query.filter(Backtest.strategy == strategy.upper())
            if status:
                query = query.filter(Backtest.status == status.upper())

            # Order by most recent
            query = query.order_by(Backtest.created_at.desc())

            # Apply limit
            query = query.limit(limit)

            backtests = query.all()

            # Convert to dict
            results = []
            for bt in backtests:
                results.append({
                    "id": bt.id,
                    "symbol": bt.symbol,
                    "timeframe": bt.timeframe,
                    "strategy": bt.strategy,
                    "start_date": bt.start_date.isoformat(),
                    "end_date": bt.end_date.isoformat(),
                    "initial_capital": bt.initial_capital,
                    "status": bt.status,
                    "progress": bt.progress,
                    "total_trades": bt.total_trades,
                    "win_rate": bt.win_rate,
                    "net_profit": bt.net_profit,
                    "net_profit_pct": bt.net_profit_pct,
                    "profit_factor": bt.profit_factor,
                    "max_drawdown_pct": bt.max_drawdown_pct,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "created_at": bt.created_at.isoformat(),
                    "completed_at": bt.completed_at.isoformat() if bt.completed_at else None,
                    "error_message": bt.error_message
                })

            return {"backtests": results, "count": len(results)}

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}")
async def get_backtest(backtest_id: str):
    """
    Get detailed backtest results

    Returns complete metrics and basic trade summary.
    Use GET /api/backtest/{id}/trades for detailed trade list.
    """
    try:
        db = SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise HTTPException(status_code=404, detail="Backtest not found")

            return {
                "id": backtest.id,
                "symbol": backtest.symbol,
                "timeframe": backtest.timeframe,
                "strategy": backtest.strategy,
                "start_date": backtest.start_date.isoformat(),
                "end_date": backtest.end_date.isoformat(),

                # Parameters
                "risk_level": backtest.risk_level,
                "risk_percentage": backtest.risk_percentage,
                "initial_capital": backtest.initial_capital,
                "slippage_pips": backtest.slippage_pips,
                "spread_pips": backtest.spread_pips,
                "ai_provider": backtest.ai_provider,
                "ai_model": backtest.ai_model,

                # Status
                "status": backtest.status,
                "progress": backtest.progress,
                "error_message": backtest.error_message,
                "notes": backtest.notes,

                # Results - Basic
                "total_trades": backtest.total_trades,
                "winning_trades": backtest.winning_trades,
                "losing_trades": backtest.losing_trades,
                "break_even_trades": backtest.break_even_trades,
                "win_rate": backtest.win_rate,
                "profit_factor": backtest.profit_factor,

                # Results - Financial
                "total_profit": backtest.total_profit,
                "total_loss": backtest.total_loss,
                "net_profit": backtest.net_profit,
                "net_profit_pct": backtest.net_profit_pct,
                "avg_profit": backtest.avg_profit,
                "avg_loss": backtest.avg_loss,
                "avg_trade": backtest.avg_trade,

                # Results - Risk
                "max_drawdown": backtest.max_drawdown,
                "max_drawdown_pct": backtest.max_drawdown_pct,
                "avg_drawdown": backtest.avg_drawdown,

                # Results - Ratios
                "sharpe_ratio": backtest.sharpe_ratio,
                "sortino_ratio": backtest.sortino_ratio,
                "expectancy": backtest.expectancy,
                "profit_expectancy_pct": backtest.profit_expectancy_pct,

                # Results - Trade Statistics
                "largest_win": backtest.largest_win,
                "largest_loss": backtest.largest_loss,
                "avg_winner": backtest.avg_winner,
                "avg_loser": backtest.avg_loser,
                "avg_win_pips": backtest.avg_win_pips,
                "avg_loss_pips": backtest.avg_loss_pips,

                # Results - Risk/Reward
                "avg_risk_reward": backtest.avg_risk_reward,
                "best_rr": backtest.best_rr,
                "worst_rr": backtest.worst_rr,

                # Results - Time Statistics
                "longest_winning_streak": backtest.longest_winning_streak,
                "longest_losing_streak": backtest.longest_losing_streak,
                "avg_trade_duration": backtest.avg_trade_duration,

                # Results - Exit Statistics
                "tp_hits": backtest.tp_hits,
                "sl_hits": backtest.sl_hits,
                "manual_exits": backtest.manual_exits,
                "timeout_exits": backtest.timeout_exits,

                # Timestamps
                "created_at": backtest.created_at.isoformat(),
                "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None,
                "duration_seconds": backtest.duration_seconds
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    """
    Get detailed trade list for a backtest

    Supports pagination with limit and offset parameters.
    """
    try:
        db = SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise HTTPException(status_code=404, detail="Backtest not found")

            # Get trades
            trades_query = db.query(BacktestTrade).filter(
                BacktestTrade.backtest_id == backtest_id
            ).order_by(BacktestTrade.entry_time.desc())

            # Apply pagination
            trades_query = trades_query.offset(offset).limit(limit)
            trades = trades_query.all()

            # Get total count
            total_count = db.query(BacktestTrade).filter(
                BacktestTrade.backtest_id == backtest_id
            ).count()

            # Convert to dict
            results = []
            for trade in trades:
                results.append({
                    "id": trade.id,
                    "direction": trade.direction,
                    "lot_size": trade.lot_size,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "stop_loss": trade.stop_loss,
                    "take_profit": trade.take_profit,
                    "pnl": trade.pnl,
                    "pnl_pct": trade.pnl_pct,
                    "pips": trade.pips,
                    "entry_time": trade.entry_time.isoformat(),
                    "exit_time": trade.exit_time.isoformat(),
                    "duration_minutes": trade.duration_minutes,
                    "duration_hours": trade.duration_hours,
                    "exit_reason": trade.exit_reason,
                    "entry_confidence": trade.entry_confidence,
                    "risk_reward": trade.risk_reward,
                    "sl_distance_pips": trade.sl_distance_pips,
                    "tp_distance_pips": trade.tp_distance_pips,
                    "session": trade.session,
                    "day_of_week": trade.day_of_week,
                    "hour_of_day": trade.hour_of_day,
                    "notes": trade.notes
                })

            return {
                "backtest_id": backtest_id,
                "trades": results,
                "count": len(results),
                "total_count": total_count,
                "offset": offset,
                "limit": limit
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str):
    """
    Delete a backtest and all its trades
    """
    try:
        db = SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if not backtest:
                raise HTTPException(status_code=404, detail="Backtest not found")

            # Delete trades first (foreign key)
            db.query(BacktestTrade).filter(
                BacktestTrade.backtest_id == backtest_id
            ).delete()

            # Delete backtest
            db.delete(backtest)
            db.commit()

            return {
                "success": True,
                "message": f"Backtest {backtest_id} deleted"
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_backtests(request: CompareRequest):
    """
    Compare multiple backtests side by side

    Returns a comparison of key metrics across all specified backtests.
    """
    try:
        if len(request.backtest_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 backtest IDs are required for comparison"
            )

        if len(request.backtest_ids) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 backtests can be compared at once"
            )

        db = SessionLocal()
        try:
            # Fetch all backtests
            backtests = db.query(Backtest).filter(
                Backtest.id.in_(request.backtest_ids)
            ).all()

            if len(backtests) != len(request.backtest_ids):
                raise HTTPException(
                    status_code=404,
                    detail="One or more backtests not found"
                )

            # Build comparison
            comparison = {
                "backtests": [],
                "summary": {
                    "best_net_profit": None,
                    "best_win_rate": None,
                    "best_sharpe_ratio": None,
                    "lowest_drawdown": None,
                    "highest_profit_factor": None
                }
            }

            best_net_profit = -float('inf')
            best_win_rate = -1
            best_sharpe_ratio = -float('inf')
            lowest_drawdown = float('inf')
            highest_profit_factor = -1

            for bt in backtests:
                bt_data = {
                    "id": bt.id,
                    "symbol": bt.symbol,
                    "timeframe": bt.timeframe,
                    "strategy": bt.strategy,
                    "status": bt.status,
                    "net_profit": bt.net_profit,
                    "net_profit_pct": bt.net_profit_pct,
                    "win_rate": bt.win_rate,
                    "total_trades": bt.total_trades,
                    "profit_factor": bt.profit_factor,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "max_drawdown_pct": bt.max_drawdown_pct,
                    "expectancy": bt.expectancy
                }
                comparison["backtests"].append(bt_data)

                # Track best values
                if bt.net_profit is not None and bt.net_profit > best_net_profit:
                    best_net_profit = bt.net_profit
                    comparison["summary"]["best_net_profit"] = bt.id

                if bt.win_rate is not None and bt.win_rate > best_win_rate:
                    best_win_rate = bt.win_rate
                    comparison["summary"]["best_win_rate"] = bt.id

                if bt.sharpe_ratio is not None and bt.sharpe_ratio > best_sharpe_ratio:
                    best_sharpe_ratio = bt.sharpe_ratio
                    comparison["summary"]["best_sharpe_ratio"] = bt.id

                if bt.max_drawdown_pct is not None and bt.max_drawdown_pct < lowest_drawdown:
                    lowest_drawdown = bt.max_drawdown_pct
                    comparison["summary"]["lowest_drawdown"] = bt.id

                if bt.profit_factor is not None and bt.profit_factor > highest_profit_factor:
                    highest_profit_factor = bt.profit_factor
                    comparison["summary"]["highest_profit_factor"] = bt.id

            return comparison

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/status")
async def get_data_status():
    """
    Get historical data availability status

    Returns information about available symbols and timeframes.
    """
    try:
        metadata = historical_data_manager.get_metadata()
        db_info = historical_data_manager.get_database_size()

        # Group by symbol
        symbols_data = {}
        for meta in metadata:
            symbol = meta["symbol"]
            if symbol not in symbols_data:
                symbols_data[symbol] = {
                    "symbol": symbol,
                    "timeframes": []
                }
            symbols_data[symbol]["timeframes"].append({
                "timeframe": meta["timeframe"],
                "oldest_date": meta["oldest_date"],
                "newest_date": meta["newest_date"],
                "candle_count": meta["candle_count"],
                "last_updated": meta["last_updated"]
            })

        return {
            "database_info": db_info,
            "symbols": list(symbols_data.values()),
            "total_symbol_tf_pairs": len(metadata)
        }

    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/download")
async def download_historical_data(
    symbol: str,
    timeframe: str = "H1",
    max_candles: int = Query(default=5000, ge=100, le=10000)
):
    """
    Download historical data from MT5

    Use this endpoint to populate the historical data database before running backtests.
    """
    try:
        # Download from MT5
        count = historical_data_manager.download_from_mt5(
            symbol=symbol.upper(),
            timeframe=timeframe.upper(),
            max_candles=max_candles
        )

        if count == 0:
            raise HTTPException(
                status_code=400,
                detail="No data downloaded. Check MT5 connection and symbol availability."
            )

        return {
            "success": True,
            "message": f"Downloaded {count} candles for {symbol} {timeframe}",
            "symbol": symbol,
            "timeframe": timeframe,
            "candles_downloaded": count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
