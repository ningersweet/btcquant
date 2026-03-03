"""
数据服务核心模块

实现数据库优先查询策略，提供统一的数据访问接口
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from .config import config
from .models import Kline, Ticker, SyncResult
from .database import Database, db
from .fetcher import BinanceFetcher, fetcher
from .preprocessor import (
    find_missing_ranges,
    fill_missing_klines,
    validate_klines,
    calculate_expected_count,
    align_to_interval
)

logger = logging.getLogger(__name__)


class DataService:
    """
    数据服务类
    
    实现数据库优先查询策略：
    1. 首先查询本地 SQLite 数据库
    2. 检查数据完整性（是否有缺失的时间段）
    3. 对于缺失的数据，从 Binance API 获取
    4. 将新获取的数据保存到数据库
    5. 返回完整的数据集
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        fetcher_instance: Optional[BinanceFetcher] = None
    ):
        """
        初始化数据服务
        
        Args:
            database: 数据库实例，默认使用全局实例
            fetcher_instance: Binance API 实例，默认使用全局实例
        """
        self.db = database or db
        self.fetcher = fetcher_instance or fetcher
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        fill_missing: bool = False
    ) -> List[Kline]:
        """
        获取 K 线数据（数据库优先策略）
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            fill_missing: 是否填充缺失数据
            
        Returns:
            K 线数据列表
        """
        logger.info(f"Getting klines: {symbol} {interval} {start_time}-{end_time}")
        
        # 查询数据库
        db_klines = self.db.query_klines(symbol, interval, start_time, end_time)
        logger.info(f"Found {len(db_klines)} klines in database")
        
        # 检查缺失范围
        missing_ranges = find_missing_ranges(db_klines, start_time, end_time, interval)
        
        if not missing_ranges:
            logger.info("Data is complete, returning from database")
            return db_klines
        
        logger.info(f"Found {len(missing_ranges)} missing ranges, fetching from Binance")
        
        all_klines = list(db_klines)
        
        # 分批获取缺失数据，避免一次性加载过多数据到内存
        for range_start, range_end in missing_ranges:
            try:
                # 限制单次获取的时间范围，避免内存溢出
                interval_ms = BinanceFetcher.get_interval_ms(interval)
                max_batch_size = 2000
                max_time_range = max_batch_size * interval_ms
                
                current_start = range_start
                while current_start < range_end:
                    batch_end = min(current_start + max_time_range, range_end)
                    
                    api_klines = self.fetcher.fetch_klines(
                        symbol, interval, current_start, batch_end
                    )
                    
                    valid_klines = validate_klines(api_klines)
                    
                    if valid_klines:
                        # 立即保存到数据库，释放内存
                        self.db.insert_klines(valid_klines)
                        all_klines.extend(valid_klines)
                    
                    if not api_klines or len(api_klines) < max_batch_size:
                        break
                    
                    current_start = batch_end
                    
            except Exception as e:
                logger.error(f"Failed to fetch klines for range {range_start}-{range_end}: {e}")
        
        # 排序和去重
        all_klines.sort(key=lambda x: x.timestamp)
        
        seen = set()
        unique_klines = []
        for kline in all_klines:
            if kline.timestamp not in seen:
                seen.add(kline.timestamp)
                unique_klines.append(kline)
        
        if fill_missing:
            unique_klines = fill_missing_klines(unique_klines, start_time, end_time, interval)
        
        logger.info(f"Returning {len(unique_klines)} klines")
        return unique_klines
    
    def get_latest_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Kline]:
        """
        获取最新的 K 线数据
        
        Args:
            symbol: 交易对
            interval: K 线周期
            limit: 返回数量
            
        Returns:
            K 线数据列表
        """
        interval_ms = BinanceFetcher.get_interval_ms(interval)
        current_time = int(datetime.now().timestamp() * 1000)
        start_time = current_time - (limit * interval_ms)
        
        return self.get_klines(symbol, interval, start_time, current_time)
    
    def get_ticker(self, symbol: str) -> Ticker:
        """
        获取最新价格
        
        Args:
            symbol: 交易对
            
        Returns:
            最新价格数据
        """
        return self.fetcher.fetch_ticker(symbol)
    
    def sync_historical_data(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: Optional[str] = None
    ) -> SyncResult:
        """
        同步历史数据
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为当前时间
            
        Returns:
            同步结果
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_time = int(start_dt.timestamp() * 1000)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_time = int(end_dt.timestamp() * 1000)
        else:
            end_time = int(datetime.now().timestamp() * 1000)
        
        logger.info(f"Syncing historical data: {symbol} {interval} {start_date} to {end_date or 'now'}")
        
        klines = self.get_klines(symbol, interval, start_time, end_time)
        
        return SyncResult(
            synced_count=len(klines),
            start_time=start_time,
            end_time=end_time
        )
    
    def get_data_status(
        self,
        symbol: str,
        interval: str
    ) -> dict:
        """
        获取数据状态
        
        Args:
            symbol: 交易对
            interval: K 线周期
            
        Returns:
            数据状态信息
        """
        time_range = self.db.get_kline_time_range(symbol, interval)
        count = self.db.get_kline_count(symbol, interval)
        
        if time_range:
            expected_count = calculate_expected_count(
                time_range[0], time_range[1], interval
            )
            completeness = count / expected_count if expected_count > 0 else 0
        else:
            expected_count = 0
            completeness = 0
        
        return {
            "symbol": symbol,
            "interval": interval,
            "count": count,
            "start_time": time_range[0] if time_range else None,
            "end_time": time_range[1] if time_range else None,
            "expected_count": expected_count,
            "completeness": round(completeness, 4)
        }


# 全局数据服务实例
data_service = DataService()
