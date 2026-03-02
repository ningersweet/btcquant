"""
策略服务包初始化
"""

from .config import config
from .models import Position, Trade, Side, ExitReason, OrderResult, AccountInfo
from .state_machine import TradingStateMachine, SystemState
from .position_manager import calculate_position_size, calculate_pnl, calculate_actual_rr
from .executor import ExecutorInterface, BacktestEngine
from .api import app, create_app

__all__ = [
    "config",
    "Position", "Trade", "Side", "ExitReason", "OrderResult", "AccountInfo",
    "TradingStateMachine", "SystemState",
    "calculate_position_size", "calculate_pnl", "calculate_actual_rr",
    "ExecutorInterface", "BacktestEngine",
    "app", "create_app",
]
