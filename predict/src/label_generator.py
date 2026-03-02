"""
标签生成模块

生成训练标签：y_rr, y_sl_pct, y_tp_pct
"""

import logging
import numpy as np
import pandas as pd
from typing import Tuple

from ..config import config

logger = logging.getLogger(__name__)


def generate_labels(df: pd.DataFrame, window: int = None) -> pd.DataFrame:
    """
    生成训练标签
    
    对于每个时刻 t，查看未来 window 个周期的数据：
    1. 获取 max_high 和 min_low
    2. 判断方向
    3. 计算标签
    
    Args:
        df: 包含 OHLCV 的 DataFrame
        window: 预测窗口（周期数）
        
    Returns:
        添加了标签列的 DataFrame
    """
    window = window or config.label.window_size
    result = df.copy()
    
    n = len(df)
    y_rr = np.full(n, np.nan)
    y_sl_pct = np.full(n, np.nan)
    y_tp_pct = np.full(n, np.nan)
    y_direction = np.full(n, np.nan)
    
    for i in range(n - window):
        current_close = df["close"].iloc[i]
        future_slice = df.iloc[i+1:i+1+window]
        
        max_high = future_slice["high"].max()
        min_low = future_slice["low"].min()
        
        upside = max_high - current_close
        downside = current_close - min_low
        
        if upside > downside:
            direction = 1
            tp_pct = upside / current_close
            sl_pct = downside / current_close
        else:
            direction = -1
            tp_pct = downside / current_close
            sl_pct = upside / current_close
        
        if sl_pct > 0:
            rr = tp_pct / sl_pct * direction
        else:
            rr = 0
        
        y_rr[i] = rr
        y_sl_pct[i] = sl_pct
        y_tp_pct[i] = tp_pct
        y_direction[i] = direction
    
    result["y_rr"] = y_rr
    result["y_sl_pct"] = y_sl_pct
    result["y_tp_pct"] = y_tp_pct
    result["y_direction"] = y_direction
    
    logger.info(f"Generated labels for {n - window} samples")
    return result


def compute_sample_weights(
    timestamps: pd.Series,
    decay_lambda: float = None
) -> np.ndarray:
    """
    计算样本权重（时间衰减）
    
    Weight = exp(-λ × ΔDays)
    
    Args:
        timestamps: 时间戳序列
        decay_lambda: 衰减系数
        
    Returns:
        权重数组
    """
    decay_lambda = decay_lambda or config.label.decay_lambda
    
    if timestamps.dtype == 'int64':
        dt = pd.to_datetime(timestamps, unit='ms')
    else:
        dt = pd.to_datetime(timestamps)
    
    latest = dt.max()
    delta_days = (latest - dt).dt.days
    weights = np.exp(-decay_lambda * delta_days)
    
    return weights.values
