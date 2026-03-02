"""
系统评估模块

计算交易系统的各项指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass

from .config import config


@dataclass
class SystemMetrics:
    """系统评估指标"""
    total_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    cagr: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    sl_rate: float
    tp_rate: float
    time_rate: float
    
    def to_dict(self) -> dict:
        return {
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate, 4),
            "profit_factor": round(self.profit_factor, 4),
            "total_pnl": round(self.total_pnl, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "cagr": round(self.cagr, 4),
            "avg_trade_pnl": round(self.avg_trade_pnl, 2),
            "avg_win": round(self.avg_win, 2),
            "avg_loss": round(self.avg_loss, 2),
            "sl_rate": round(self.sl_rate, 4),
            "tp_rate": round(self.tp_rate, 4),
            "time_rate": round(self.time_rate, 4)
        }


def evaluate_system(trades_df: pd.DataFrame, initial_balance: float) -> SystemMetrics:
    """
    评估交易系统
    
    Args:
        trades_df: 交易记录 DataFrame
        initial_balance: 初始资金
        
    Returns:
        系统评估指标
    """
    if trades_df.empty:
        return _empty_metrics()
    
    total_trades = len(trades_df)
    
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    
    total_profit = wins["pnl"].sum() if len(wins) > 0 else 0
    total_loss = abs(losses["pnl"].sum()) if len(losses) > 0 else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    total_pnl = trades_df["pnl"].sum()
    avg_trade_pnl = trades_df["pnl"].mean()
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
    avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
    
    equity_curve = initial_balance + trades_df["pnl"].cumsum()
    peak = equity_curve.expanding().max()
    drawdown = peak - equity_curve
    max_drawdown = drawdown.max()
    max_drawdown_pct = (max_drawdown / peak.max()) if peak.max() > 0 else 0
    
    returns = trades_df["pnl_pct"]
    if len(returns) > 1:
        sharpe_ratio = (returns.mean() * np.sqrt(config.trading_days_per_year * config.hours_per_day)) / returns.std() if returns.std() > 0 else 0
    else:
        sharpe_ratio = 0
    
    if total_trades > 0 and "entry_time" in trades_df.columns:
        start_time = trades_df["entry_time"].min()
        end_time = trades_df["exit_time"].max()
        years = (end_time - start_time) / (365.25 * 24 * 3600 * 1000)
        final_balance = initial_balance + total_pnl
        cagr = (final_balance / initial_balance) ** (1 / years) - 1 if years > 0 else 0
    else:
        cagr = 0
    
    exit_reasons = trades_df["exit_reason"].value_counts()
    sl_rate = exit_reasons.get("SL", 0) / total_trades if total_trades > 0 else 0
    tp_rate = exit_reasons.get("TP", 0) / total_trades if total_trades > 0 else 0
    time_rate = exit_reasons.get("TIME", 0) / total_trades if total_trades > 0 else 0
    
    return SystemMetrics(
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_pnl=total_pnl,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=sharpe_ratio,
        cagr=cagr,
        avg_trade_pnl=avg_trade_pnl,
        avg_win=avg_win,
        avg_loss=avg_loss,
        sl_rate=sl_rate,
        tp_rate=tp_rate,
        time_rate=time_rate
    )


def _empty_metrics() -> SystemMetrics:
    """返回空指标"""
    return SystemMetrics(
        total_trades=0, win_rate=0, profit_factor=0, total_pnl=0,
        max_drawdown=0, max_drawdown_pct=0, sharpe_ratio=0, cagr=0,
        avg_trade_pnl=0, avg_win=0, avg_loss=0,
        sl_rate=0, tp_rate=0, time_rate=0
    )
