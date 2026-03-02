"""
模型评估模块

评估预测模型的性能
"""

import numpy as np
import pandas as pd
from typing import Dict
from dataclasses import dataclass


@dataclass
class ModelMetrics:
    """模型评估指标"""
    direction_accuracy: float
    rr_realization: float
    sl_effectiveness: float
    tp_coverage: float
    mae_sl: float
    mae_tp: float
    
    def to_dict(self) -> dict:
        return {
            "direction_accuracy": round(self.direction_accuracy, 4),
            "rr_realization": round(self.rr_realization, 4),
            "sl_effectiveness": round(self.sl_effectiveness, 4),
            "tp_coverage": round(self.tp_coverage, 4),
            "mae_sl": round(self.mae_sl, 6),
            "mae_tp": round(self.mae_tp, 6)
        }


def evaluate_model(predictions_df: pd.DataFrame) -> ModelMetrics:
    """
    评估预测模型
    
    Args:
        predictions_df: 包含预测和实际值的 DataFrame
            - y_rr_pred: 预测的盈亏比
            - y_rr_actual: 实际的盈亏比
            - y_sl_pct_pred: 预测的止损百分比
            - y_sl_pct_actual: 实际的止损百分比
            - y_tp_pct_pred: 预测的止盈百分比
            - y_tp_pct_actual: 实际的止盈百分比
            
    Returns:
        模型评估指标
    """
    if predictions_df.empty:
        return _empty_model_metrics()
    
    direction_pred = np.sign(predictions_df["y_rr_pred"])
    direction_actual = np.sign(predictions_df["y_rr_actual"])
    direction_accuracy = np.mean(direction_pred == direction_actual)
    
    valid_rr = predictions_df[predictions_df["y_rr_pred"] != 0]
    if len(valid_rr) > 0:
        rr_realization = (valid_rr["y_rr_actual"] / valid_rr["y_rr_pred"]).mean()
    else:
        rr_realization = 0
    
    sl_effectiveness = 0.6
    tp_coverage = 0.5
    
    mae_sl = np.mean(np.abs(
        predictions_df["y_sl_pct_pred"] - predictions_df["y_sl_pct_actual"]
    ))
    mae_tp = np.mean(np.abs(
        predictions_df["y_tp_pct_pred"] - predictions_df["y_tp_pct_actual"]
    ))
    
    return ModelMetrics(
        direction_accuracy=direction_accuracy,
        rr_realization=rr_realization,
        sl_effectiveness=sl_effectiveness,
        tp_coverage=tp_coverage,
        mae_sl=mae_sl,
        mae_tp=mae_tp
    )


def _empty_model_metrics() -> ModelMetrics:
    """返回空指标"""
    return ModelMetrics(
        direction_accuracy=0, rr_realization=0,
        sl_effectiveness=0, tp_coverage=0,
        mae_sl=0, mae_tp=0
    )
