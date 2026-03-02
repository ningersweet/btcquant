"""
仓位管理模块
"""

import logging
from typing import Dict

from .config import config

logger = logging.getLogger(__name__)


def calculate_position_size(
    risk_amount: float,
    entry_price: float,
    sl_price: float,
    leverage: int = None
) -> Dict:
    """
    计算仓位大小
    
    Args:
        risk_amount: 单笔风险金额 (USDT)
        entry_price: 入场价格
        sl_price: 止损价格
        leverage: 杠杆倍数
        
    Returns:
        仓位信息字典
    """
    leverage = leverage or config.strategy.leverage
    
    sl_distance = abs(entry_price - sl_price)
    sl_pct = sl_distance / entry_price
    
    quantity = risk_amount / sl_distance
    notional = quantity * entry_price
    margin = notional / leverage
    
    return {
        "quantity": round(quantity, 6),
        "margin": round(margin, 2),
        "notional": round(notional, 2),
        "sl_distance": round(sl_distance, 2),
        "sl_pct": round(sl_pct, 6)
    }


def calculate_pnl(
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float
) -> Dict:
    """
    计算盈亏
    
    Args:
        side: 方向 (LONG/SHORT)
        entry_price: 入场价格
        exit_price: 出场价格
        quantity: 数量
        
    Returns:
        盈亏信息
    """
    if side == "LONG":
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = (exit_price - entry_price) / entry_price
    else:
        pnl = (entry_price - exit_price) * quantity
        pnl_pct = (entry_price - exit_price) / entry_price
    
    return {
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 6)
    }


def calculate_actual_rr(
    side: str,
    entry_price: float,
    exit_price: float,
    sl_price: float
) -> float:
    """
    计算实际盈亏比
    
    Args:
        side: 方向
        entry_price: 入场价格
        exit_price: 出场价格
        sl_price: 止损价格
        
    Returns:
        实际盈亏比
    """
    sl_distance = abs(entry_price - sl_price)
    
    if side == "LONG":
        profit_distance = exit_price - entry_price
    else:
        profit_distance = entry_price - exit_price
    
    if sl_distance > 0:
        return round(profit_distance / sl_distance, 4)
    return 0.0
