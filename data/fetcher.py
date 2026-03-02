"""
Binance API 数据获取模块

提供从 Binance 获取 K 线数据的功能
"""

import time
import logging
import httpx
from typing import List, Optional
from datetime import datetime, timezone

from .config import config
from .models import Kline, Ticker

logger = logging.getLogger(__name__)


class BinanceFetcher:
    """Binance API 数据获取类"""
    
    INTERVAL_MS = {
        "1m": 60 * 1000,
        "3m": 3 * 60 * 1000,
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "8h": 8 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000,
        "3d": 3 * 24 * 60 * 60 * 1000,
        "1w": 7 * 24 * 60 * 60 * 1000,
        "1M": 30 * 24 * 60 * 60 * 1000,
    }
    
    def __init__(self):
        """初始化 Binance API 客户端"""
        self.base_url = config.binance.url
        self.timeout = config.request_timeout
        self.retry_count = config.retry_count
        self.retry_delay = config.retry_delay
        self.max_klines = config.max_klines_per_request
    
    def _make_request(
        self,
        endpoint: str,
        params: dict
    ) -> dict:
        """
        发送 HTTP 请求（带重试）
        
        Args:
            endpoint: API 端点
            params: 请求参数
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error {e.response.status_code}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
            except httpx.RequestError as e:
                logger.warning(f"Request error: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
        
        raise Exception("Max retries exceeded")
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        limit: int = 1500
    ) -> List[Kline]:
        """
        获取 K 线数据
        
        Args:
            symbol: 交易对
            interval: K 线周期
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 单次请求最大数量
            
        Returns:
            K 线数据列表
        """
        all_klines = []
        current_start = start_time
        
        while current_start < end_time:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": current_start,
                "endTime": end_time,
                "limit": min(limit, self.max_klines)
            }
            
            try:
                data = self._make_request("/fapi/v1/klines", params)
                
                if not data:
                    break
                
                for item in data:
                    kline = Kline.from_binance(item, symbol, interval)
                    all_klines.append(kline)
                
                last_timestamp = int(data[-1][0])
                interval_ms = self.INTERVAL_MS.get(interval, 3600000)
                current_start = last_timestamp + interval_ms
                
                if len(data) < limit:
                    break
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to fetch klines: {e}")
                raise
        
        logger.info(f"Fetched {len(all_klines)} klines from Binance")
        return all_klines
    
    def fetch_ticker(self, symbol: str) -> Ticker:
        """
        获取最新价格
        
        Args:
            symbol: 交易对
            
        Returns:
            最新价格数据
        """
        params = {"symbol": symbol}
        
        try:
            data = self._make_request("/fapi/v1/ticker/price", params)
            return Ticker(
                symbol=data["symbol"],
                price=float(data["price"]),
                timestamp=int(data.get("time", time.time() * 1000))
            )
        except Exception as e:
            logger.error(f"Failed to fetch ticker: {e}")
            raise
    
    def fetch_server_time(self) -> int:
        """
        获取服务器时间
        
        Returns:
            服务器时间戳（毫秒）
        """
        try:
            data = self._make_request("/fapi/v1/time", {})
            return int(data["serverTime"])
        except Exception as e:
            logger.error(f"Failed to fetch server time: {e}")
            raise
    
    @staticmethod
    def get_interval_ms(interval: str) -> int:
        """
        获取 K 线周期对应的毫秒数
        
        Args:
            interval: K 线周期
            
        Returns:
            毫秒数
        """
        return BinanceFetcher.INTERVAL_MS.get(interval, 3600000)


# 全局 Fetcher 实例
fetcher = BinanceFetcher()
