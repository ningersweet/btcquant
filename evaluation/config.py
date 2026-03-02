"""
评估模块配置

从 YAML 配置文件加载配置
"""

import os
import sys
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config_loader import get_config


class EvaluationConfig:
    """评估配置"""
    
    @property
    def risk_free_rate(self) -> float:
        return get_config("evaluation.risk_free_rate", 0.02)
    
    @property
    def trading_days_per_year(self) -> int:
        return get_config("evaluation.trading_days_per_year", 365)
    
    @property
    def hours_per_day(self) -> int:
        return get_config("evaluation.hours_per_day", 24)


config = EvaluationConfig()
