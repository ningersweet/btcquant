"""
预测服务包初始化
"""

from .config import config
from .src.label_generator import generate_labels, compute_sample_weights
from .src.model_trainer import ModelTrainer, create_model
from .src.inference import InferenceService, PredictionResult
from .api import app, create_app

__all__ = [
    "config",
    "generate_labels", "compute_sample_weights",
    "ModelTrainer", "create_model",
    "InferenceService", "PredictionResult",
    "app", "create_app",
]
