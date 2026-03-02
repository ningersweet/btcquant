"""
特征工程服务配置模块

从 YAML 配置文件加载配置
"""

import os
import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config_loader import get_config


class FeatureConfig:
    """特征工程配置"""
    
    @property
    def ema_periods(self) -> tuple:
        periods = get_config("features.technical.ema_periods", [9, 21, 50])
        return tuple(periods) if isinstance(periods, list) else periods
    
    @property
    def rsi_period(self) -> int:
        return get_config("features.technical.rsi_period", 14)
    
    @property
    def macd_fast(self) -> int:
        return get_config("features.technical.macd_fast", 12)
    
    @property
    def macd_slow(self) -> int:
        return get_config("features.technical.macd_slow", 26)
    
    @property
    def macd_signal(self) -> int:
        return get_config("features.technical.macd_signal", 9)
    
    @property
    def atr_period(self) -> int:
        return get_config("features.technical.atr_period", 14)
    
    @property
    def bb_period(self) -> int:
        return get_config("features.technical.bb_period", 20)
    
    @property
    def bb_std(self) -> float:
        return get_config("features.technical.bb_std", 2.0)
    
    @property
    def obv_ema_period(self) -> int:
        return get_config("features.technical.obv_ema_period", 20)
    
    @property
    def lookback_periods(self) -> tuple:
        periods = get_config("features.structural.lookback_periods", [5, 10, 20])
        return tuple(periods) if isinstance(periods, list) else periods
    
    @property
    def return_periods(self) -> tuple:
        periods = get_config("features.structural.return_periods", [1, 5, 10])
        return tuple(periods) if isinstance(periods, list) else periods
    
    @property
    def round_number_base(self) -> int:
        return get_config("features.structural.round_number_base", 1000)


class ServiceConfig:
    """服务配置"""
    
    @property
    def host(self) -> str:
        return get_config("features.host", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return get_config("features.port", 8002)
    
    @property
    def data_service_url(self) -> str:
        return get_config("features.data_service_url", "http://data-service:8001")


class FeaturesServiceConfig:
    """特征服务主配置"""
    
    def __init__(self):
        self.feature = FeatureConfig()
        self.service = ServiceConfig()


config = FeaturesServiceConfig()
