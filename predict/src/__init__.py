"""
预测服务核心模块

目录结构:
- models/      模型架构和训练器
- data/        数据加载和标签生成
- evaluation/  回测和推理
- utils/       工具函数
"""

# 模型
from .models import TCNModel, ModelTrainer

# 数据
from .data import (
    load_klines_from_service,
    split_data,
    LabelGenerator,
    generate_labels_from_klines
)

# 评估
from .evaluation import (
    Backtester,
    load_inference_model
)

# 工具
from .utils import tune_hyperparameters

__all__ = [
    'TCNModel',
    'ModelTrainer',
    'load_klines_from_service',
    'split_data',
    'LabelGenerator',
    'generate_labels_from_klines',
    'Backtester',
    'load_inference_model',
    'tune_hyperparameters',
]
