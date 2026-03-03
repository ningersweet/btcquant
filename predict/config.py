"""
预测服务配置模块

从 YAML 配置文件加载配置
"""

import os
import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config_loader import get_config


class ModelConfig:
    """模型配置"""
    
    @property
    def n_estimators(self) -> int:
        return get_config("predict.model.n_estimators", 500)
    
    @property
    def max_depth(self) -> int:
        return get_config("predict.model.max_depth", 6)
    
    @property
    def min_child_samples(self) -> int:
        return get_config("predict.model.min_child_samples", 50)
    
    @property
    def subsample(self) -> float:
        return get_config("predict.model.subsample", 0.8)
    
    @property
    def colsample_bytree(self) -> float:
        return get_config("predict.model.colsample_bytree", 0.8)
    
    @property
    def learning_rate(self) -> float:
        return get_config("predict.model.learning_rate", 0.05)
    
    @property
    def random_state(self) -> int:
        return get_config("predict.model.random_state", 42)


class LabelConfig:
    """标签配置"""
    
    @property
    def window_size(self) -> int:
        return get_config("predict.label.window_size", 1)
    
    @property
    def decay_lambda(self) -> float:
        return get_config("predict.label.decay_lambda", 0.00095)
    
    @property
    def min_trend_strength(self) -> float:
        """趋势强度最低阈值，低于此值视为噪声不生成标签"""
        return get_config("predict.label.min_trend_strength", 0.005)
    
    @property
    def rr_clip_range(self) -> float:
        """盈亏比截断范围 [-rr_clip_range, rr_clip_range]"""
        return get_config("predict.label.rr_clip_range", 10.0)
    
    @property
    def min_sl_pct_floor(self) -> float:
        """止损百分比最小值，防止除零产生极端 RR"""
        return get_config("predict.label.min_sl_pct_floor", 0.001)


class ValidationConfig:
    """校验配置"""
    
    @property
    def min_rr(self) -> float:
        return get_config("predict.validation.min_rr", 1.5)
    
    @property
    def max_sl_pct(self) -> float:
        return get_config("predict.validation.max_sl_pct", 0.05)
    
    @property
    def min_sl_pct(self) -> float:
        return get_config("predict.validation.min_sl_pct", 0.001)


class ServiceConfig:
    """服务配置"""
    
    @property
    def host(self) -> str:
        return get_config("predict.host", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return get_config("predict.port", 8003)
    
    @property
    def model_path(self) -> str:
        return get_config("predict.model_path", "/app/models")
    
    @property
    def data_service_url(self) -> str:
        return get_config("predict.data_service_url", "http://data-service:8001")
    
    @property
    def features_service_url(self) -> str:
        return get_config("predict.features_service_url", "http://features-service:8002")


class PredictServiceConfig:
    """预测服务主配置"""
    
    def __init__(self):
        self.model = ModelConfig()
        self.label = LabelConfig()
        self.validation = ValidationConfig()
        self.service = ServiceConfig()


config = PredictServiceConfig()
