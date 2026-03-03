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
    生成训练标签（含趋势强度过滤和 RR 截断）
    
    对于每个时刻 t，查看未来 window 个周期的数据：
    1. 获取 max_high 和 min_low
    2. 趋势强度过滤：弱趋势（upside ≈ downside）标为 NaN 不参与训练
    3. 判断方向，计算 TP/SL 百分比
    4. sl_pct 设最小保护值，防止除零产生极端 RR
    5. RR 做截断，限制在合理范围
    
    Args:
        df: 包含 OHLCV 的 DataFrame
        window: 预测窗口（周期数）
        
    Returns:
        添加了标签列的 DataFrame
    """
    window = window or config.label.window_size
    min_trend_strength = config.label.min_trend_strength
    rr_clip = config.label.rr_clip_range
    sl_floor = config.label.min_sl_pct_floor
    
    result = df.copy()
    n = len(df)
    y_rr = np.full(n, np.nan)
    y_sl_pct = np.full(n, np.nan)
    y_tp_pct = np.full(n, np.nan)
    y_direction = np.full(n, np.nan)
    
    skipped_weak = 0
    
    for i in range(n - window):
        current_close = df["close"].iloc[i]
        future_slice = df.iloc[i+1:i+1+window]
        
        max_high = future_slice["high"].max()
        min_low = future_slice["low"].min()
        
        upside = max_high - current_close
        downside = current_close - min_low
        
        trend_strength = abs(upside - downside) / current_close
        if trend_strength < min_trend_strength:
            skipped_weak += 1
            continue
        
        if upside > downside:
            direction = 1
            tp_pct = upside / current_close
            sl_pct = downside / current_close
        else:
            direction = -1
            tp_pct = downside / current_close
            sl_pct = upside / current_close
        
        sl_pct = max(sl_pct, sl_floor)
        
        rr = np.clip(
            tp_pct / sl_pct * direction,
            -rr_clip, rr_clip
        )
        
        y_rr[i] = rr
        y_sl_pct[i] = sl_pct
        y_tp_pct[i] = tp_pct
        y_direction[i] = direction
    
    result["y_rr"] = y_rr
    result["y_sl_pct"] = y_sl_pct
    result["y_tp_pct"] = y_tp_pct
    result["y_direction"] = y_direction
    
    valid_count = np.sum(~np.isnan(y_rr))
    total_candidates = n - window
    logger.info(
        f"Labels generated: {valid_count}/{total_candidates} valid, "
        f"{skipped_weak} weak trends filtered (threshold={min_trend_strength}), "
        f"RR clipped to [{-rr_clip}, {rr_clip}], sl_pct floor={sl_floor}"
    )
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
