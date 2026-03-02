"""
统一交易接口
"""

from abc import ABC, abstractmethod
from ..models import OrderResult, AccountInfo


class ExecutorInterface(ABC):
    """统一交易接口"""
    
    @abstractmethod
    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        sl_price: float,
        tp_price: float
    ) -> OrderResult:
        """开仓"""
        pass
    
    @abstractmethod
    def close_position(
        self,
        symbol: str,
        reason: str
    ) -> OrderResult:
        """平仓"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        pass
