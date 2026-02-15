"""Historical Data Management - Store and retrieve candle data from SQLite"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from mt5.connector import connector

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manage historical candle data in SQLite database"""

    def __init__(self, db_path: str = None):
        """
        Initialize historical data manager

        Args:
            db_path: Path to SQLite database file (default: data/historical_candles.db)
        """
        if db_path is None:
            # Create data directory if it doesn't exist
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "historical_candles.db"

        self.db_path = str(db_path)
        self._initialize_database()

    def _initialize_database(self):
        """Create database schema if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create candles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                tick_volume INTEGER,
                real_volume INTEGER,
                spread REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)

        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_tf
            ON candles(symbol, timeframe)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_tf_timestamp
            ON candles(symbol, timeframe, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON candles(timestamp)
        """)

        # Create metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_metadata (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                oldest_timestamp INTEGER,
                newest_timestamp INTEGER,
                candle_count INTEGER,
                last_updated DATETIME,
                PRIMARY KEY(symbol, timeframe)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Historical data database initialized: {self.db_path}")

    def download_from_mt5(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime = None,
        end_date: datetime = None,
        max_candles: int = None
    ) -> int:
        """
        Download historical candles from MT5 and store in database

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M5, M15, H1, H4, D1)
            start_date: Start date for data download
            end_date: End date for data download
            max_candles: Maximum candles to download

        Returns:
            Number of candles downloaded
        """
        if not connector.is_connected():
            logger.error("MT5 not connected, cannot download historical data")
            return 0

        # Determine number of candles to download
        if max_candles is None:
            # Default to 5000 candles (about 1 year for H1)
            max_candles = 5000

        # Get candles from MT5
        candles = connector.get_candles(symbol, timeframe, max_candles)
        if not candles:
            logger.warning(f"No candles received from MT5 for {symbol} {timeframe}")
            return 0

        # Filter by date range if specified
        if start_date:
            start_ts = int(start_date.timestamp())
            candles = [c for c in candles if c["time"] >= start_ts]

        if end_date:
            end_ts = int(end_date.timestamp())
            candles = [c for c in candles if c["time"] <= end_ts]

        # Store candles in database
        stored_count = self.store_candles(candles, symbol, timeframe)

        logger.info(f"Downloaded {stored_count} candles for {symbol} {timeframe}")
        return stored_count

    def store_candles(
        self,
        candles: List[Dict[str, Any]],
        symbol: str,
        timeframe: str
    ) -> int:
        """
        Store candles in database (handles duplicates with INSERT OR REPLACE)

        Args:
            candles: List of candle dictionaries
            symbol: Trading symbol
            timeframe: Timeframe

        Returns:
            Number of candles stored
        """
        if not candles:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stored_count = 0
        for candle in candles:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO candles
                    (symbol, timeframe, timestamp, open, high, low, close, volume, tick_volume, real_volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    timeframe,
                    candle["time"],
                    candle["open"],
                    candle["high"],
                    candle["low"],
                    candle["close"],
                    candle.get("volume", candle.get("tick_volume", 0)),
                    candle.get("tick_volume", 0),
                    candle.get("real_volume", 0)
                ))
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing candle: {e}")
                continue

        conn.commit()

        # Update metadata
        self._update_metadata(cursor, symbol, timeframe)

        conn.close()
        return stored_count

    def _update_metadata(self, cursor, symbol: str, timeframe: str):
        """Update metadata for symbol/timeframe"""
        cursor.execute("""
            SELECT
                MIN(timestamp) as oldest,
                MAX(timestamp) as newest,
                COUNT(*) as count
            FROM candles
            WHERE symbol = ? AND timeframe = ?
        """, (symbol, timeframe))

        row = cursor.fetchone()
        if row and row[2] > 0:
            cursor.execute("""
                INSERT OR REPLACE INTO historical_metadata
                (symbol, timeframe, oldest_timestamp, newest_timestamp, candle_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol, timeframe, row[0], row[1], row[2], datetime.utcnow()))

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime = None,
        end_date: datetime = None,
        count: int = None,
        descending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve candles from database

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date filter
            end_date: End date filter
            count: Maximum number of candles to return
            descending: If True, return newest candles first

        Returns:
            List of candle dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT timestamp, open, high, low, close, volume, tick_volume, real_volume
            FROM candles
            WHERE symbol = ? AND timeframe = ?
        """
        params = [symbol, timeframe]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(int(start_date.timestamp()))

        if end_date:
            query += " AND timestamp <= ?"
            params.append(int(end_date.timestamp()))

        query += " ORDER BY timestamp " + ("DESC" if descending else "ASC")

        if count:
            query += " LIMIT ?"
            params.append(count)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dictionaries
        candles = []
        for row in rows:
            candles.append({
                "time": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "tick_volume": row[6],
                "real_volume": row[7]
            })

        conn.close()
        return candles

    def get_candles_for_backtest(
        self,
        symbol: str,
        timeframe: str,
        count: int,
        require_min: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get candles for backtesting (sorted by timestamp, oldest first)

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            count: Number of candles to return
            require_min: Minimum required candles (returns None if not enough)

        Returns:
            List of candles sorted by timestamp (oldest first)
        """
        candles = self.get_candles(symbol, timeframe, count=count, descending=False)

        if require_min and len(candles) < require_min:
            return None

        return candles

    def get_metadata(
        self,
        symbol: str = None,
        timeframe: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get metadata for historical data

        Args:
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)

        Returns:
            List of metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM historical_metadata WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        metadata = []
        for row in rows:
            metadata.append({
                "symbol": row[0],
                "timeframe": row[1],
                "oldest_timestamp": row[2],
                "newest_timestamp": row[3],
                "candle_count": row[4],
                "last_updated": row[5],
                "oldest_date": datetime.fromtimestamp(row[2]).isoformat() if row[2] else None,
                "newest_date": datetime.fromtimestamp(row[3]).isoformat() if row[3] else None
            })

        conn.close()
        return metadata

    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT symbol FROM candles ORDER BY symbol")
        rows = cursor.fetchall()

        symbols = [row[0] for row in rows]
        conn.close()
        return symbols

    def get_date_range(
        self,
        symbol: str,
        timeframe: str
    ) -> Optional[Tuple[datetime, datetime, int]]:
        """
        Get date range and count for symbol/timeframe

        Returns:
            Tuple of (oldest_date, newest_date, candle_count) or None
        """
        metadata = self.get_metadata(symbol, timeframe)
        if not metadata:
            return None

        meta = metadata[0]
        if meta["oldest_timestamp"]:
            oldest = datetime.fromtimestamp(meta["oldest_timestamp"])
            newest = datetime.fromtimestamp(meta["newest_timestamp"])
            return (oldest, newest, meta["candle_count"])
        return None

    def delete_data(
        self,
        symbol: str = None,
        timeframe: str = None,
        before_date: datetime = None
    ) -> int:
        """
        Delete historical data

        Args:
            symbol: Symbol to delete (optional, if None deletes all)
            timeframe: Timeframe to delete (optional)
            before_date: Delete candles before this date (optional)

        Returns:
            Number of candles deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "DELETE FROM candles WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if timeframe:
            query += " AND timeframe = ?"
            params.append(timeframe)

        if before_date:
            query += " AND timestamp < ?"
            params.append(int(before_date.timestamp()))

        cursor.execute(query, params)
        deleted_count = cursor.rowcount
        conn.commit()

        # Update metadata
        self._update_metadata(cursor, symbol or "ALL", timeframe or "ALL")

        conn.close()
        logger.info(f"Deleted {deleted_count} candles from historical database")
        return deleted_count

    def vacuum_database(self):
        """Optimize database by rebuilding and reducing file size"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")

        conn.commit()
        conn.close()
        logger.info("Database vacuumed and analyzed")

    def get_database_size(self) -> Dict[str, Any]:
        """Get database size and statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get total candle count
        cursor.execute("SELECT COUNT(*) FROM candles")
        total_candles = cursor.fetchone()[0]

        # Get file size
        db_path = Path(self.db_path)
        file_size = db_path.stat().st_size if db_path.exists() else 0

        # Get symbol/timeframe count
        cursor.execute("SELECT COUNT(DISTINCT CONCAT(symbol, '_', timeframe)) FROM candles")
        unique_pairs = cursor.fetchone()[0]

        conn.close()

        return {
            "path": str(self.db_path),
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "total_candles": total_candles,
            "symbol_timeframe_pairs": unique_pairs
        }


# Singleton
historical_data_manager = HistoricalDataManager()
