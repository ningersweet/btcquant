"""
回测撮合引擎
"""

import logging
import uuid
from typing import List, Optional
import pandas as pd
import numpy as np

from .interface import ExecutorInterface
from ..models import OrderResult, AccountInfo, Position, Trade, Side, ExitReason
from ..config import config

logger = logging.getLogger(__name__)


class BacktestEngine(ExecutorInterface):
    """回测撮合引擎"""
    
    def __init__(self, initial_balance: float, klines: pd.DataFrame = None):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.klines = klines
        self.current_idx = 0
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.margin_used = 0.0
        self.unrealized_pnl = 0.0
    
    def set_klines(self, klines: pd.DataFrame) -> None:
        """设置 K 线数据"""
        self.klines = klines
        self.current_idx = 0
    
    def set_time(self, timestamp: int) -> None:
        """设置当前时间"""
        if self.klines is None:
            return
        
        idx = self.klines[self.klines["timestamp"] <= timestamp].index
        if len(idx) > 0:
            self.current_idx = idx[-1]
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        if self.klines is None or self.current_idx >= len(self.klines):
            return 0.0
        return float(self.klines.iloc[self.current_idx]["close"])
    
    def get_current_kline(self) -> Optional[dict]:
        """获取当前 K 线"""
        if self.klines is None or self.current_idx >= len(self.klines):
            return None
        return self.klines.iloc[self.current_idx].to_dict()
    
    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        sl_price: float,
        tp_price: float
    ) -> OrderResult:
        """开仓"""
        if self.position is not None:
            return OrderResult(
                success=False,
                order_id="",
                filled_price=0,
                filled_quantity=0,
                timestamp=0,
                error_message="Already has position"
            )
        
        current_price = self.get_current_price(symbol)
        current_kline = self.get_current_kline()
        timestamp = int(current_kline["timestamp"]) if current_kline else 0
        
        deadline = timestamp + (config.label.window_size * 3600 * 1000)
        
        self.position = Position(
            symbol=symbol,
            side=Side[side],
            entry_price=current_price,
            quantity=quantity,
            sl_price=sl_price,
            tp_price=tp_price,
            entry_time=timestamp,
            deadline=deadline,
            rr_predicted=0.0
        )
        
        notional = quantity * current_price
        self.margin_used = notional / config.strategy.leverage
        
        order_id = str(uuid.uuid4())[:8]
        logger.info(f"Backtest: Opened {side} position @ {current_price}")
        
        return OrderResult(
            success=True,
            order_id=order_id,
            filled_price=current_price,
            filled_quantity=quantity,
            timestamp=timestamp
        )
    
    def close_position(self, symbol: str, reason: str) -> OrderResult:
        """平仓"""
        if self.position is None:
            return OrderResult(
                success=False,
                order_id="",
                filled_price=0,
                filled_quantity=0,
                timestamp=0,
                error_message="No position to close"
            )
        
        current_price = self.get_current_price(symbol)
        current_kline = self.get_current_kline()
        timestamp = int(current_kline["timestamp"]) if current_kline else 0
        
        pos = self.position
        
        if pos.side == Side.LONG:
            pnl = (current_price - pos.entry_price) * pos.quantity
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price
        else:
            pnl = (pos.entry_price - current_price) * pos.quantity
            pnl_pct = (pos.entry_price - current_price) / pos.entry_price
        
        sl_distance = abs(pos.entry_price - pos.sl_price)
        if pos.side == Side.LONG:
            profit_distance = current_price - pos.entry_price
        else:
            profit_distance = pos.entry_price - current_price
        rr_actual = profit_distance / sl_distance if sl_distance > 0 else 0
        
        trade = Trade(
            trade_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=current_price,
            sl_price=pos.sl_price,
            tp_price=pos.tp_price,
            quantity=pos.quantity,
            entry_time=pos.entry_time,
            exit_time=timestamp,
            exit_reason=ExitReason[reason],
            pnl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 6),
            rr_predicted=pos.rr_predicted,
            rr_actual=round(rr_actual, 4),
            mode="backtest"
        )
        self.trades.append(trade)
        
        self.balance += pnl
        self.equity = self.balance
        self.margin_used = 0.0
        self.unrealized_pnl = 0.0
        self.position = None
        
        logger.info(f"Backtest: Closed position @ {current_price}, PnL: {pnl:.2f}")
        
        return OrderResult(
            success=True,
            order_id=str(uuid.uuid4())[:8],
            filled_price=current_price,
            filled_quantity=pos.quantity,
            timestamp=timestamp
        )
    
    def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        return AccountInfo(
            balance=round(self.balance, 2),
            equity=round(self.equity, 2),
            margin_used=round(self.margin_used, 2),
            unrealized_pnl=round(self.unrealized_pnl, 2)
        )
    
    def step(self) -> bool:
        """前进一步"""
        if self.klines is None:
            return False
        
        self.current_idx += 1
        return self.current_idx < len(self.klines)
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录 DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame([t.to_dict() for t in self.trades])
