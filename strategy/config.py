"""
策略服务配置模块

从 YAML 配置文件加载配置
"""

import os
import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config_loader import get_config


class StrategyConfig:
    """策略配置"""
    
    @property
    def mode(self) -> str:
        return get_config("strategy.trading.mode", "backtest")
    
    @property
    def risk_amount(self) -> float:
        return get_config("strategy.trading.risk_amount", 100.0)
    
    @property
    def min_rr_threshold(self) -> float:
        return get_config("strategy.trading.min_rr_threshold", 1.5)
    
    @property
    def max_sl_pct(self) -> float:
        return get_config("strategy.trading.max_sl_pct", 0.05)
    
    @property
    def min_sl_pct(self) -> float:
        return get_config("strategy.trading.min_sl_pct", 0.001)
    
    @property
    def leverage(self) -> int:
        return get_config("strategy.trading.leverage", 20)


class ServiceConfig:
    """服务配置"""
    
    @property
    def host(self) -> str:
        return get_config("strategy.host", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return get_config("strategy.port", 8004)
    
    @property
    def predict_service_url(self) -> str:
        return get_config("strategy.predict_service_url", "http://predict-service:8003")
    
    @property
    def data_service_url(self) -> str:
        return get_config("strategy.data_service_url", "http://data-service:8001")


class StrategyServiceConfig:
    """策略服务主配置"""
    
    def __init__(self):
        self.strategy = StrategyConfig()
        self.service = ServiceConfig()


config = StrategyServiceConfig()
