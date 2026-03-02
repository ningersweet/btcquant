"""
数据模型定义

定义数据服务使用的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Kline:
    """K 线数据模型"""
    timestamp: int          # 毫秒时间戳
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol,
            "interval": self.interval
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Kline":
        """从字典创建"""
        return cls(
            timestamp=data["timestamp"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            symbol=data.get("symbol", "BTCUSDT"),
            interval=data.get("interval", "1h")
        )
    
    @classmethod
    def from_binance(cls, data: list, symbol: str = "BTCUSDT", interval: str = "1h") -> "Kline":
        """从 Binance API 响应创建"""
        return cls(
            timestamp=int(data[0]),
            open=float(data[1]),
            high=float(data[2]),
            low=float(data[3]),
            close=float(data[4]),
            volume=float(data[5]),
            symbol=symbol,
            interval=interval
        )


@dataclass
class Ticker:
    """最新价格数据模型"""
    symbol: str
    price: float
    timestamp: int
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp
        }


@dataclass
class SyncResult:
    """数据同步结果"""
    synced_count: int
    start_time: int
    end_time: int
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "synced_count": self.synced_count,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


@dataclass
class ApiResponse:
    """统一 API 响应格式"""
    code: int
    data: Optional[dict] = None
    message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = {"code": self.code}
        if self.data is not None:
            result["data"] = self.data
        if self.message is not None:
            result["message"] = self.message
        return result
    
    @classmethod
    def success(cls, data: dict) -> "ApiResponse":
        """创建成功响应"""
        return cls(code=0, data=data)
    
    @classmethod
    def error(cls, code: int, message: str) -> "ApiResponse":
        """创建错误响应"""
        return cls(code=code, message=message, data=None)


class ErrorCode:
    """错误码定义"""
    SUCCESS = 0
    PARAM_ERROR = 1001
    DATA_NOT_FOUND = 1002
    INTERNAL_ERROR = 1003
    BINANCE_API_ERROR = 3003
