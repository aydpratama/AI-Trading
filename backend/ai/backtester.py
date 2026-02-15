"""Backtesting Engine - Simulate trading strategies with historical data"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from ai.genius_ai import genius_ai
from ai.historical_data import historical_data_manager
from mt5.connector import connector
from database import SessionLocal
from models.backtest import Backtest, BacktestTrade

logger = logging.getLogger(__name__)


class Backtester:
    """Backtesting engine for trading strategy simulation"""

    def __init__(self):
        self.min_candles = 100
        self.max_trades = 1000  # Safety limit

    def run_backtest(
        self,
        backtest_id: str,
        symbol: str,
        timeframe: str,
        strategy: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000,
        risk_level: str = "moderate",
        risk_percentage: float = None,
        slippage_pips: float = 1.0,
        spread_pips: float = 1.0,
        ai_provider: str = None,
        ai_model: str = None,
        api_key: str = None,
        update_progress: callable = None
    ) -> Dict[str, Any]:
        """
        Run complete backtest simulation

        Args:
            backtest_id: Backtest ID
            symbol: Trading symbol
            timeframe: Chart timeframe
            strategy: Strategy type (GENIUS_AI, AI, CUSTOM)
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            risk_level: Risk level (conservative/moderate/aggressive)
            risk_percentage: Explicit risk percentage
            slippage_pips: Slippage in pips
            spread_pips: Spread in pips
            ai_provider: AI provider for AI strategy
            ai_model: AI model to use
            api_key: API key for AI provider
            update_progress: Callback function for progress updates

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest {backtest_id}: {symbol} {timeframe} {strategy}")

        # Update status to RUNNING
        self._update_backtest_status(backtest_id, "RUNNING", progress=0)

        try:
            # Step 1: Get historical candles
            if update_progress:
                update_progress(5, "Loading historical data...")

            candles = historical_data_manager.get_candles_for_backtest(
                symbol=symbol,
                timeframe=timeframe,
                count=10000,  # Get all available candles
                require_min=self.min_candles
            )

            if not candles:
                return {"error": "Insufficient historical data for backtest"}

            # Filter by date range
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            filtered_candles = [c for c in candles if start_ts <= c["time"] <= end_ts]

            if len(filtered_candles) < self.min_candles:
                return {"error": f"Insufficient candles in date range: {len(filtered_candles)}"}

            logger.info(f"Loaded {len(filtered_candles)} candles for backtest")

            # Step 2: Initialize backtest state
            balance = initial_capital
            equity = initial_capital
            trades = []
            open_position = None

            # Get symbol info for calculations
            symbol_info = connector.get_symbol_info(symbol)
            if not symbol_info:
                return {"error": f"Cannot get symbol info for {symbol}"}

            point = symbol_info.get("point", 0.00001)
            pip_size = 0.0001  # Standard forex pip

            # Calculate pip values
            if "JPY" in symbol:
                pip_size = 0.01
            elif "XAU" in symbol or "XAG" in symbol:
                pip_size = 0.1

            # Step 3: Run simulation
            total_steps = len(filtered_candles)
            for i, candle in enumerate(filtered_candles):
                # Update progress
                progress = int((i / total_steps) * 90) + 5  # 5% to 95%
                if update_progress and i % 50 == 0:
                    update_progress(progress, f"Simulating candle {i}/{total_steps}...")

                # Check for open position exit
                if open_position:
                    exit_result = self._check_exit(
                        open_position,
                        candle,
                        symbol_info,
                        slippage_pips,
                        spread_pips,
                        pip_size
                    )

                    if exit_result:
                        # Close position
                        trade = exit_result["trade"]
                        balance += trade["pnl"]
                        equity = balance

                        trades.append(trade)
                        open_position = None

                        logger.debug(f"Trade closed: {trade['direction']} {trade['pnl']:.2f}")

                        # Safety check - stop if too many trades
                        if len(trades) >= self.max_trades:
                            logger.warning(f"Reached max trades limit: {self.max_trades}")
                            break

                        continue  # Skip signal generation on this candle

                # Generate signal for new position
                if not open_position:
                    signal = self._generate_signal(
                        strategy=strategy,
                        symbol=symbol,
                        timeframe=timeframe,
                        candles=filtered_candles[:i+1],  # All candles up to current
                        current_candle=candle,
                        ai_provider=ai_provider,
                        ai_model=ai_model,
                        api_key=api_key,
                        risk_level=risk_level,
                        risk_percentage=risk_percentage
                    )

                    if signal:
                        # Open position
                        open_position = self._open_position(
                            signal=signal,
                            candle=candle,
                            balance=balance,
                            symbol_info=symbol_info,
                            slippage_pips=slippage_pips,
                            spread_pips=spread_pips,
                            pip_size=pip_size
                        )

                        logger.debug(f"Trade opened: {signal['direction']} @ {candle['close']}")

            # Step 4: Close any remaining position
            if open_position:
                last_candle = filtered_candles[-1]
                trade = self._close_position(
                    open_position,
                    last_candle,
                    "TIMEOUT",
                    symbol_info,
                    pip_size
                )
                balance += trade["pnl"]
                trades.append(trade)

            # Step 5: Calculate metrics
            if update_progress:
                update_progress(95, "Calculating metrics...")

            metrics = self._calculate_metrics(
                trades=trades,
                initial_capital=initial_capital,
                final_balance=balance
            )

            # Step 6: Store trades in database
            if update_progress:
                update_progress(98, "Saving results...")

            self._store_trades(backtest_id, trades)

            # Step 7: Update backtest record
            self._update_backtest_results(backtest_id, metrics)

            if update_progress:
                update_progress(100, "Backtest complete")

            logger.info(f"Backtest complete: {len(trades)} trades, Net PnL: ${metrics['net_profit']:.2f}")

            return {
                "success": True,
                "backtest_id": backtest_id,
                "metrics": metrics,
                "trades_count": len(trades),
                "balance": balance
            }

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            self._update_backtest_status(
                backtest_id,
                "ERROR",
                error_message=str(e)
            )
            return {"error": str(e)}

    def _generate_signal(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        candles: List[Dict[str, Any]],
        current_candle: Dict[str, Any],
        ai_provider: str = None,
        ai_model: str = None,
        api_key: str = None,
        risk_level: str = "moderate",
        risk_percentage: float = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal based on strategy

        Returns:
            Signal dictionary or None if no signal
        """
        if len(candles) < 50:
            return None

        try:
            if strategy == "GENIUS_AI":
                # Use GENIUS AI system
                analysis = genius_ai.analyze(
                    symbol=symbol,
                    timeframe=timeframe,
                    risk_level=risk_level
                )

                if analysis.get("signal") and analysis.get("signal", {}).get("confidence", 0) >= 70:
                    signal = analysis["signal"]
                    setup = analysis.get("setup", {})

                    return {
                        "direction": signal["direction"],
                        "confidence": signal["confidence"],
                        "entry": current_candle["close"],
                        "stop_loss": setup.get("stop_loss", current_candle["close"] * 0.99),
                        "take_profit": setup.get("take_profit", current_candle["close"] * 1.01),
                        "lot_size": setup.get("lot_size", 0.01),
                        "risk_reward": setup.get("risk_reward", 1.5),
                        "reasons": signal.get("reasons", []),
                        "entry_confidence": signal.get("confidence", 0)
                    }

            elif strategy == "AI":
                # Use external AI provider
                # This would require async execution, simplified here
                # In production, use ai_service.analyze_with_ai()
                pass

            return None

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None

    def _open_position(
        self,
        signal: Dict[str, Any],
        candle: Dict[str, Any],
        balance: float,
        symbol_info: Dict[str, Any],
        slippage_pips: float,
        spread_pips: float,
        pip_size: float
    ) -> Dict[str, Any]:
        """Open a new position"""
        direction = signal["direction"]
        lot_size = signal["lot_size"]
        base_price = signal["entry"]

        # Apply spread and slippage
        if direction == "BUY":
            entry_price = base_price + (spread_pips * pip_size) + (slippage_pips * pip_size)
        else:  # SELL
            entry_price = base_price - (spread_pips * pip_size) - (slippage_pips * pip_size)

        return {
            "direction": direction,
            "lot_size": lot_size,
            "entry_price": entry_price,
            "stop_loss": signal["stop_loss"],
            "take_profit": signal["take_profit"],
            "risk_reward": signal["risk_reward"],
            "entry_time": datetime.fromtimestamp(candle["time"]),
            "entry_candle_index": None,  # Would be set in caller
            "entry_confidence": signal.get("entry_confidence", 0),
            "reasons": signal.get("reasons", []),
            "pnl": 0
        }

    def _check_exit(
        self,
        position: Dict[str, Any],
        candle: Dict[str, Any],
        symbol_info: Dict[str, Any],
        slippage_pips: float,
        spread_pips: float,
        pip_size: float
    ) -> Optional[Dict[str, Any]]:
        """Check if position should be closed (SL/TP hit)"""
        direction = position["direction"]
        sl = position["stop_loss"]
        tp = position["take_profit"]

        high = candle["high"]
        low = candle["low"]

        exit_reason = None
        exit_price = None

        if direction == "BUY":
            # Check SL
            if low <= sl:
                exit_reason = "SL_HIT"
                exit_price = sl + (slippage_pips * pip_size)
            # Check TP
            elif high >= tp:
                exit_reason = "TP_HIT"
                exit_price = tp - (slippage_pips * pip_size)

        else:  # SELL
            # Check SL
            if high >= sl:
                exit_reason = "SL_HIT"
                exit_price = sl - (slippage_pips * pip_size)
            # Check TP
            elif low <= tp:
                exit_reason = "TP_HIT"
                exit_price = tp + (slippage_pips * pip_size)

        if exit_reason:
            trade = self._close_position(
                position,
                candle,
                exit_reason,
                symbol_info,
                pip_size,
                exit_price=exit_price
            )
            return {"trade": trade, "exit_reason": exit_reason}

        return None

    def _close_position(
        self,
        position: Dict[str, Any],
        candle: Dict[str, Any],
        exit_reason: str,
        symbol_info: Dict[str, Any],
        pip_size: float,
        exit_price: float = None
    ) -> Dict[str, Any]:
        """Close a position and calculate PnL"""
        direction = position["direction"]
        entry_price = position["entry_price"]

        # Use provided exit price or candle close
        if exit_price is None:
            exit_price = candle["close"]

        # Calculate PnL
        point_value = symbol_info.get("trade_tick_value", 1) / symbol_info.get("trade_tick_size", pip_size)
        sl_distance = abs(exit_price - entry_price)

        if direction == "BUY":
            pnl = (exit_price - entry_price) / pip_size * position["lot_size"] * point_value * pip_size
            pips = (exit_price - entry_price) / pip_size
        else:  # SELL
            pnl = (entry_price - exit_price) / pip_size * position["lot_size"] * point_value * pip_size
            pips = (entry_price - exit_price) / pip_size

        # Calculate duration
        entry_time = position["entry_time"]
        exit_time = datetime.fromtimestamp(candle["time"])
        duration = (exit_time - entry_time).total_seconds() / 60  # In minutes

        # Calculate risk/reward achieved
        sl_distance_pips = abs(entry_price - position["stop_loss"]) / pip_size
        tp_distance_pips = abs(position["take_profit"] - entry_price) / pip_size
        achieved_rr = abs(pips) / sl_distance_pips if sl_distance_pips > 0 else 0

        # Determine trade context
        trade_context = self._get_trade_context(entry_time, exit_time)

        return {
            "direction": direction,
            "lot_size": position["lot_size"],
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_loss": position["stop_loss"],
            "take_profit": position["take_profit"],
            "pnl": pnl,
            "pnl_pct": (pnl / 10000) * 100,  # Approximate percentage
            "pips": pips,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "duration_minutes": duration,
            "duration_hours": duration / 60,
            "exit_reason": exit_reason,
            "entry_confidence": position.get("entry_confidence", 0),
            "risk_reward": position.get("risk_reward", 0),
            "achieved_rr": achieved_rr,
            "sl_distance_pips": sl_distance_pips,
            "tp_distance_pips": tp_distance_pips,
            "session": trade_context["session"],
            "day_of_week": trade_context["day_of_week"],
            "hour_of_day": trade_context["hour_of_day"]
        }

    def _get_trade_context(self, entry_time: datetime, exit_time: datetime) -> Dict[str, Any]:
        """Determine trading session and time context"""
        hour = entry_time.hour
        day_of_week = entry_time.weekday()

        # Determine session
        if 22 <= hour or hour < 7:
            session = "SYDNEY"
        elif 0 <= hour < 9:
            session = "TOKYO"
        elif 8 <= hour < 17:
            session = "LONDON"
        elif 13 <= hour < 22:
            session = "NEW_YORK"
        else:
            session = "OVERLAP"

        return {
            "session": session,
            "day_of_week": day_of_week,
            "hour_of_day": hour
        }

    def _calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float,
        final_balance: float
    ) -> Dict[str, Any]:
        """Calculate all backtest performance metrics"""
        if not trades:
            return self._empty_metrics()

        # Basic counts
        total_trades = len(trades)
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        break_even_trades = [t for t in trades if t["pnl"] == 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        be_count = len(break_even_trades)

        # Financial metrics
        total_profit = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
        total_loss = sum(t["pnl"] for t in losing_trades) if losing_trades else 0
        net_profit = total_profit + total_loss
        net_profit_pct = (net_profit / initial_capital) * 100

        # Win rate
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

        # Average values
        avg_profit = (total_profit / win_count) if win_count > 0 else 0
        avg_loss = (total_loss / loss_count) if loss_count > 0 else 0
        avg_trade = (net_profit / total_trades) if total_trades > 0 else 0

        # Largest values
        largest_win = max(t["pnl"] for t in winning_trades) if winning_trades else 0
        largest_loss = min(t["pnl"] for t in losing_trades) if losing_trades else 0

        # Profit factor
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0

        # Expectancy
        expectancy = avg_trade
        expectancy_pct = (avg_trade / initial_capital * 100) if initial_capital > 0 else 0

        # Risk/Reward statistics
        rr_values = [t.get("achieved_rr", 0) for t in trades if t.get("achieved_rr", 0) > 0]
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0
        best_rr = max(rr_values) if rr_values else 0
        worst_rr = min(rr_values) if rr_values else 0

        # Exit statistics
        tp_hits = sum(1 for t in trades if t["exit_reason"] == "TP_HIT")
        sl_hits = sum(1 for t in trades if t["exit_reason"] == "SL_HIT")
        timeout_exits = sum(1 for t in trades if t["exit_reason"] == "TIMEOUT")
        manual_exits = sum(1 for t in trades if t["exit_reason"] == "MANUAL")

        # Streaks
        streaks = self._calculate_streaks(trades)
        longest_winning_streak = streaks["longest_winning"]
        longest_losing_streak = streaks["longest_losing"]

        # Drawdown
        drawdown_info = self._calculate_drawdown(trades, initial_capital)
        max_drawdown = drawdown_info["max_drawdown"]
        max_drawdown_pct = drawdown_info["max_drawdown_pct"]

        # Sharpe ratio (simplified - using standard deviation of returns)
        if len(trades) > 1:
            returns = [t["pnl"] / initial_capital for t in trades]
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5 if variance > 0 else 0
            sharpe_ratio = (avg_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0

        # Sortino ratio (downside deviation only)
        if len(trades) > 1:
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
                downside_std = downside_variance ** 0.5 if downside_variance > 0 else 0
                sortino_ratio = (avg_return / downside_std) * (252 ** 0.5) if downside_std > 0 else 0
            else:
                sortino_ratio = sharpe_ratio  # No losing trades
        else:
            sortino_ratio = 0

        # Average duration
        durations = [t["duration_minutes"] for t in trades]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Average PnL in pips
        winning_pips = [t["pips"] for t in winning_trades]
        losing_pips = [t["pips"] for t in losing_trades]
        avg_win_pips = sum(winning_pips) / len(winning_pips) if winning_pips else 0
        avg_loss_pips = sum(losing_pips) / len(losing_pips) if losing_pips else 0

        return {
            "total_trades": total_trades,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "break_even_trades": be_count,
            "win_rate": win_rate,
            "profit_factor": round(profit_factor, 2) if profit_factor > 0 else 0,

            "total_profit": round(total_profit, 2),
            "total_loss": round(total_loss, 2),
            "net_profit": round(net_profit, 2),
            "net_profit_pct": round(net_profit_pct, 2),
            "avg_profit": round(avg_profit, 2),
            "avg_loss": round(avg_loss, 2),
            "avg_trade": round(avg_trade, 2),

            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),

            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "expectancy": round(expectancy, 2),
            "profit_expectancy_pct": round(expectancy_pct, 2),

            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "avg_winner": round(avg_profit, 2) if win_count > 0 else 0,
            "avg_loser": round(avg_loss, 2) if loss_count > 0 else 0,
            "avg_win_pips": round(avg_win_pips, 1),
            "avg_loss_pips": round(avg_loss_pips, 1),

            "avg_risk_reward": round(avg_rr, 2),
            "best_rr": round(best_rr, 2),
            "worst_rr": round(worst_rr, 2),

            "longest_winning_streak": longest_winning_streak,
            "longest_losing_streak": longest_losing_streak,
            "avg_trade_duration": round(avg_duration, 2),

            "tp_hits": tp_hits,
            "sl_hits": sl_hits,
            "manual_exits": manual_exits,
            "timeout_exits": timeout_exits,

            "initial_capital": initial_capital,
            "final_balance": round(final_balance, 2)
        }

    def _calculate_streaks(self, trades: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate longest winning and losing streaks"""
        longest_winning = 0
        longest_losing = 0
        current_winning = 0
        current_losing = 0

        for trade in trades:
            if trade["pnl"] > 0:
                current_winning += 1
                current_losing = 0
                longest_winning = max(longest_winning, current_winning)
            elif trade["pnl"] < 0:
                current_losing += 1
                current_winning = 0
                longest_losing = max(longest_losing, current_losing)
            else:
                current_winning = 0
                current_losing = 0

        return {
            "longest_winning": longest_winning,
            "longest_losing": longest_losing
        }

    def _calculate_drawdown(self, trades: List[Dict[str, Any]], initial_capital: float) -> Dict[str, float]:
        """Calculate maximum drawdown"""
        balance = initial_capital
        peak = initial_capital
        max_drawdown = 0
        max_drawdown_pct = 0

        for trade in trades:
            balance += trade["pnl"]
            peak = max(peak, balance)

            if peak > 0:
                drawdown = peak - balance
                drawdown_pct = (drawdown / peak) * 100

                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct

        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "break_even_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_profit": 0,
            "total_loss": 0,
            "net_profit": 0,
            "net_profit_pct": 0,
            "avg_profit": 0,
            "avg_loss": 0,
            "avg_trade": 0,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "expectancy": 0,
            "profit_expectancy_pct": 0,
            "largest_win": 0,
            "largest_loss": 0,
            "avg_winner": 0,
            "avg_loser": 0,
            "avg_win_pips": 0,
            "avg_loss_pips": 0,
            "avg_risk_reward": 0,
            "best_rr": 0,
            "worst_rr": 0,
            "longest_winning_streak": 0,
            "longest_losing_streak": 0,
            "avg_trade_duration": 0,
            "tp_hits": 0,
            "sl_hits": 0,
            "manual_exits": 0,
            "timeout_exits": 0,
            "initial_capital": 10000,
            "final_balance": 10000
        }

    def _update_backtest_status(
        self,
        backtest_id: str,
        status: str,
        progress: int = None,
        error_message: str = None
    ):
        """Update backtest status in database"""
        db = SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if backtest:
                backtest.status = status
                if progress is not None:
                    backtest.progress = progress
                if error_message:
                    backtest.error_message = error_message

                db.commit()
        finally:
            db.close()

    def _update_backtest_results(self, backtest_id: str, metrics: Dict[str, Any]):
        """Update backtest with calculated metrics"""
        db = SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            if backtest:
                # Update all metric fields
                for key, value in metrics.items():
                    if hasattr(backtest, key):
                        setattr(backtest, key, value)

                backtest.status = "COMPLETED"
                backtest.completed_at = datetime.utcnow()
                backtest.progress = 100

                db.commit()
        finally:
            db.close()

    def _store_trades(self, backtest_id: str, trades: List[Dict[str, Any]]):
        """Store all trades in database"""
        db = SessionLocal()
        try:
            for trade in trades:
                db_trade = BacktestTrade(
                    backtest_id=backtest_id,
                    symbol=trade.get("symbol", "N/A"),
                    direction=trade["direction"],
                    lot_size=trade["lot_size"],
                    entry_price=trade["entry_price"],
                    exit_price=trade["exit_price"],
                    stop_loss=trade["stop_loss"],
                    take_profit=trade["take_profit"],
                    pnl=trade["pnl"],
                    pnl_pct=trade.get("pnl_pct", 0),
                    pips=trade.get("pips", 0),
                    entry_time=trade["entry_time"],
                    exit_time=trade["exit_time"],
                    duration_minutes=trade.get("duration_minutes", 0),
                    duration_hours=trade.get("duration_hours", 0),
                    exit_reason=trade["exit_reason"],
                    entry_confidence=trade.get("entry_confidence", 0),
                    risk_reward=trade.get("risk_reward", 0),
                    sl_distance_pips=trade.get("sl_distance_pips", 0),
                    tp_distance_pips=trade.get("tp_distance_pips", 0),
                    session=trade.get("session"),
                    day_of_week=trade.get("day_of_week"),
                    hour_of_day=trade.get("hour_of_day")
                )
                db.add(db_trade)

            db.commit()
            logger.info(f"Stored {len(trades)} trades for backtest {backtest_id}")
        finally:
            db.close()


# Singleton
backtester = Backtester()
