"""
数据预处理模块

提供数据清洗、时间对齐等功能
"""

import logging
from typing import List, Tuple, Optional
from datetime import datetime, timezone

from .models import Kline
from .fetcher import BinanceFetcher

logger = logging.getLogger(__name__)


def align_to_interval(timestamp_ms: int, interval: str) -> int:
    """
    将时间戳对齐到指定周期的起始时间
    
    Args:
        timestamp_ms: 毫秒时间戳
        interval: K 线周期
        
    Returns:
        对齐后的毫秒时间戳
    """
    interval_ms = BinanceFetcher.get_interval_ms(interval)
    return (timestamp_ms // interval_ms) * interval_ms


def align_to_hour(timestamp_ms: int) -> int:
    """
    将时间戳对齐到整点
    
    Args:
        timestamp_ms: 毫秒时间戳
        
    Returns:
        对齐到整点的毫秒时间戳
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    aligned = dt.replace(minute=0, second=0, microsecond=0)
    return int(aligned.timestamp() * 1000)


def find_missing_ranges(
    klines: List[Kline],
    start_time: int,
    end_time: int,
    interval: str
) -> List[Tuple[int, int]]:
    """
    找出缺失的时间段
    
    Args:
        klines: 已有的 K 线数据
        start_time: 请求的开始时间
        end_time: 请求的结束时间
        interval: K 线周期
        
    Returns:
        缺失时间段列表 [(start1, end1), (start2, end2), ...]
    """
    if not klines:
        return [(start_time, end_time)]
    
    interval_ms = BinanceFetcher.get_interval_ms(interval)
    existing_timestamps = set(k.timestamp for k in klines)
    
    missing_ranges = []
    current_start = None
    
    aligned_start = align_to_interval(start_time, interval)
    aligned_end = align_to_interval(end_time, interval)
    
    current_time = aligned_start
    while current_time <= aligned_end:
        if current_time not in existing_timestamps:
            if current_start is None:
                current_start = current_time
        else:
            if current_start is not None:
                missing_ranges.append((current_start, current_time - interval_ms))
                current_start = None
        
        current_time += interval_ms
    
    if current_start is not None:
        missing_ranges.append((current_start, aligned_end))
    
    return missing_ranges


def fill_missing_klines(
    klines: List[Kline],
    start_time: int,
    end_time: int,
    interval: str
) -> List[Kline]:
    """
    填充缺失的 K 线数据（向前填充）
    
    Args:
        klines: K 线数据列表
        start_time: 开始时间
        end_time: 结束时间
        interval: K 线周期
        
    Returns:
        填充后的 K 线数据列表
    """
    if not klines:
        return []
    
    interval_ms = BinanceFetcher.get_interval_ms(interval)
    klines_dict = {k.timestamp: k for k in klines}
    
    aligned_start = align_to_interval(start_time, interval)
    aligned_end = align_to_interval(end_time, interval)
    
    result = []
    last_kline = None
    
    current_time = aligned_start
    while current_time <= aligned_end:
        if current_time in klines_dict:
            last_kline = klines_dict[current_time]
            result.append(last_kline)
        elif last_kline is not None:
            filled_kline = Kline(
                timestamp=current_time,
                open=last_kline.close,
                high=last_kline.close,
                low=last_kline.close,
                close=last_kline.close,
                volume=0.0,
                symbol=last_kline.symbol,
                interval=last_kline.interval
            )
            result.append(filled_kline)
            logger.debug(f"Filled missing kline at {current_time}")
        
        current_time += interval_ms
    
    return result


def validate_klines(klines: List[Kline]) -> List[Kline]:
    """
    验证 K 线数据的有效性
    
    Args:
        klines: K 线数据列表
        
    Returns:
        有效的 K 线数据列表
    """
    valid_klines = []
    
    for kline in klines:
        if kline.high < kline.low:
            logger.warning(f"Invalid kline at {kline.timestamp}: high < low")
            continue
        
        if kline.open < 0 or kline.close < 0:
            logger.warning(f"Invalid kline at {kline.timestamp}: negative price")
            continue
        
        if kline.volume < 0:
            logger.warning(f"Invalid kline at {kline.timestamp}: negative volume")
            continue
        
        valid_klines.append(kline)
    
    return valid_klines


def calculate_expected_count(start_time: int, end_time: int, interval: str) -> int:
    """
    计算时间范围内预期的 K 线数量
    
    Args:
        start_time: 开始时间戳（毫秒）
        end_time: 结束时间戳（毫秒）
        interval: K 线周期
        
    Returns:
        预期的 K 线数量
    """
    interval_ms = BinanceFetcher.get_interval_ms(interval)
    return ((end_time - start_time) // interval_ms) + 1
