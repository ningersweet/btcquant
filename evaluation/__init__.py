"""
评估模块包初始化
"""

from .config import config
from .system_evaluator import SystemMetrics, evaluate_system
from .model_evaluator import ModelMetrics, evaluate_model

__all__ = [
    "config",
    "SystemMetrics", "evaluate_system",
    "ModelMetrics", "evaluate_model",
]
