"""
状态机模块
"""

import logging
from enum import Enum
from typing import Optional
from datetime import datetime

from .models import Position, Side
from .config import config

logger = logging.getLogger(__name__)


class SystemState(Enum):
    IDLE = "idle"
    WAITING_SIGNAL = "waiting"
    POSITION_OPEN = "open"
    CLOSING = "closing"


class TradingStateMachine:
    """交易状态机"""
    
    def __init__(self):
        self.state = SystemState.IDLE
        self.current_position: Optional[Position] = None
        self.total_trades = 0
        self.total_pnl = 0.0
        self.last_trade_time: Optional[int] = None
    
    def can_open_position(self) -> bool:
        """是否可以开仓"""
        return self.state == SystemState.IDLE and self.current_position is None
    
    def open_position(self, position: Position) -> bool:
        """
        开仓
        
        Args:
            position: 持仓信息
            
        Returns:
            是否成功
        """
        if not self.can_open_position():
            logger.warning("Cannot open position: already has position or wrong state")
            return False
        
        self.current_position = position
        self.state = SystemState.POSITION_OPEN
        logger.info(f"Position opened: {position.side.value} @ {position.entry_price}")
        return True
    
    def close_position(self, exit_price: float, exit_time: int, pnl: float) -> bool:
        """
        平仓
        
        Args:
            exit_price: 出场价格
            exit_time: 出场时间
            pnl: 盈亏
            
        Returns:
            是否成功
        """
        if self.current_position is None:
            logger.warning("No position to close")
            return False
        
        self.total_trades += 1
        self.total_pnl += pnl
        self.last_trade_time = exit_time
        
        logger.info(f"Position closed @ {exit_price}, PnL: {pnl}")
        
        self.current_position = None
        self.state = SystemState.IDLE
        return True
    
    def check_exit_conditions(
        self,
        current_price: float,
        current_time: int
    ) -> Optional[str]:
        """
        检查出场条件
        
        Args:
            current_price: 当前价格
            current_time: 当前时间
            
        Returns:
            触发的出场原因 (SL/TP/TIME) 或 None
        """
        if self.current_position is None:
            return None
        
        pos = self.current_position
        
        if pos.side == Side.LONG:
            if current_price <= pos.sl_price:
                return "SL"
            if current_price >= pos.tp_price:
                return "TP"
        else:
            if current_price >= pos.sl_price:
                return "SL"
            if current_price <= pos.tp_price:
                return "TP"
        
        if current_time >= pos.deadline:
            return "TIME"
        
        return None
    
    def get_status(self) -> dict:
        """获取状态"""
        return {
            "state": self.state.value,
            "mode": config.strategy.mode,
            "current_position": self.current_position.to_dict() if self.current_position else None,
            "total_trades": self.total_trades,
            "total_pnl": round(self.total_pnl, 2),
            "last_trade_time": self.last_trade_time
        }
