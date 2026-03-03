"""
预测服务包初始化
"""

from .label_generator import LabelGenerator, generate_labels_from_klines
from .tcn_model import TCNModel, TCNLoss, create_tcn_model
from .data_loader import (
    TimeSeriesDataset,
    split_data,
    create_dataloaders,
    normalize_inference_data
)
from .model_trainer import ModelTrainer, EarlyStopping
from .backtest import BacktestEngine
from .inference import ModelInference, load_inference_model

# 可选依赖
try:
    from .hyperparameter_tuner import HyperparameterTuner, tune_hyperparameters
    _has_optuna = True
except ImportError:
    HyperparameterTuner = None
    tune_hyperparameters = None
    _has_optuna = False

__all__ = [
    'LabelGenerator',
    'generate_labels_from_klines',
    'TCNModel',
    'TCNLoss',
    'create_tcn_model',
    'TimeSeriesDataset',
    'split_data',
    'create_dataloaders',
    'normalize_inference_data',
    'ModelTrainer',
    'EarlyStopping',
    'BacktestEngine',
    'ModelInference',
    'load_inference_model',
]

if _has_optuna:
    __all__.extend(['HyperparameterTuner', 'tune_hyperparameters'])
