"""
数据库操作模块

提供 SQLite 数据库的 CRUD 操作
"""

import sqlite3
import logging
from typing import List, Optional, Tuple
from contextlib import contextmanager
from pathlib import Path

from .config import config
from .models import Kline

logger = logging.getLogger(__name__)


class Database:
    """SQLite 数据库操作类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or config.database.db_path
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_tables(self) -> None:
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS klines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, timestamp)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_klines_symbol_interval_timestamp 
                ON klines(symbol, interval, timestamp)
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id VARCHAR(50) UNIQUE NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    sl_price REAL NOT NULL,
                    tp_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    entry_time INTEGER NOT NULL,
                    exit_time INTEGER,
                    exit_reason VARCHAR(20),
                    pnl REAL,
                    pnl_pct REAL,
                    rr_predicted REAL NOT NULL,
                    rr_actual REAL,
                    mode VARCHAR(20) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol_entry_time 
                ON trades(symbol, entry_time)
            """)
            
            logger.info("Database tables initialized")
    
    def query_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int
    ) -> List[Kline]:
        """
        查询 K 线数据
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            
        Returns:
            K 线数据列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, open, high, low, close, volume, symbol, interval
                FROM klines
                WHERE symbol = ? AND interval = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (symbol, interval, start_time, end_time))
            
            rows = cursor.fetchall()
            return [
                Kline(
                    timestamp=row["timestamp"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    symbol=row["symbol"],
                    interval=row["interval"]
                )
                for row in rows
            ]
    
    def insert_klines(self, klines: List[Kline]) -> int:
        """
        批量插入 K 线数据
        
        Args:
            klines: K 线数据列表
            
        Returns:
            插入的记录数
        """
        if not klines:
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            
            for kline in klines:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO klines 
                        (symbol, interval, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        kline.symbol,
                        kline.interval,
                        kline.timestamp,
                        kline.open,
                        kline.high,
                        kline.low,
                        kline.close,
                        kline.volume
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except sqlite3.IntegrityError:
                    pass
            
            logger.info(f"Inserted {inserted} klines")
            return inserted
    
    def get_kline_time_range(
        self,
        symbol: str,
        interval: str
    ) -> Optional[Tuple[int, int]]:
        """
        获取数据库中 K 线数据的时间范围
        
        Args:
            symbol: 交易对
            interval: K 线周期
            
        Returns:
            (最早时间戳, 最晚时间戳) 或 None（如果没有数据）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp)
                FROM klines
                WHERE symbol = ? AND interval = ?
            """, (symbol, interval))
            
            row = cursor.fetchone()
            if row and row[0] is not None:
                return (row[0], row[1])
            return None
    
    def get_kline_count(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> int:
        """
        获取 K 线数据数量
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_time: 开始时间戳（可选）
            end_time: 结束时间戳（可选）
            
        Returns:
            数据数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if start_time is not None and end_time is not None:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM klines
                    WHERE symbol = ? AND interval = ? AND timestamp >= ? AND timestamp <= ?
                """, (symbol, interval, start_time, end_time))
            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM klines
                    WHERE symbol = ? AND interval = ?
                """, (symbol, interval))
            
            return cursor.fetchone()[0]
    
    def delete_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> int:
        """
        删除 K 线数据
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_time: 开始时间戳（可选）
            end_time: 结束时间戳（可选）
            
        Returns:
            删除的记录数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if start_time is not None and end_time is not None:
                cursor.execute("""
                    DELETE FROM klines
                    WHERE symbol = ? AND interval = ? AND timestamp >= ? AND timestamp <= ?
                """, (symbol, interval, start_time, end_time))
            else:
                cursor.execute("""
                    DELETE FROM klines
                    WHERE symbol = ? AND interval = ?
                """, (symbol, interval))
            
            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} klines")
            return deleted


# 全局数据库实例
db = Database()
