"""
数据模型定义
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class ExitReason(Enum):
    SL = "SL"
    TP = "TP"
    TIME = "TIME"
    MANUAL = "MANUAL"


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: Side
    entry_price: float
    quantity: float
    sl_price: float
    tp_price: float
    entry_time: int
    deadline: int
    rr_predicted: float
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "sl_price": self.sl_price,
            "tp_price": self.tp_price,
            "entry_time": self.entry_time,
            "deadline": self.deadline,
            "rr_predicted": self.rr_predicted
        }


@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    symbol: str
    side: Side
    entry_price: float
    exit_price: float
    sl_price: float
    tp_price: float
    quantity: float
    entry_time: int
    exit_time: int
    exit_reason: ExitReason
    pnl: float
    pnl_pct: float
    rr_predicted: float
    rr_actual: float
    mode: str
    
    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "sl_price": self.sl_price,
            "tp_price": self.tp_price,
            "quantity": self.quantity,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "exit_reason": self.exit_reason.value,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "rr_predicted": self.rr_predicted,
            "rr_actual": self.rr_actual,
            "mode": self.mode
        }


@dataclass
class OrderResult:
    """订单结果"""
    success: bool
    order_id: str
    filled_price: float
    filled_quantity: float
    timestamp: int
    error_message: Optional[str] = None


@dataclass
class AccountInfo:
    """账户信息"""
    balance: float
    equity: float
    margin_used: float
    unrealized_pnl: float
