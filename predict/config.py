"""
预测服务配置模块

基于 common/config_loader 的配置访问接口
"""

import os
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.config_loader import get_config, get_section


class Config:
    """预测服务配置类（基于 common/config_loader）"""
    
    def __init__(self):
        """初始化配置"""
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        
        # 统一存储目录
        self.storage_dir = self.project_root / 'storage'
        self.logs_dir = self.storage_dir / 'logs'
        self.cache_dir = self.storage_dir / 'cache'
        self.models_dir = self.storage_dir / 'models'
        
        # 创建目录
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    # 标签生成配置
    @property
    def label_alpha(self) -> float:
        return get_config('predict.label.alpha', 0.0015)
    
    @property
    def label_gamma(self) -> float:
        return get_config('predict.label.gamma', 0.0040)
    
    @property
    def label_beta(self) -> float:
        return get_config('predict.label.beta', 0.0025)
    
    @property
    def label_theta_min(self) -> float:
        return get_config('predict.label.theta_min', 0.0100)
    
    @property
    def label_K(self) -> int:
        return get_config('predict.label.K', 12)
    
    # 数据配置
    @property
    def data_window_size(self) -> int:
        return get_config('predict.data.window_size', 288)
    
    @property
    def data_interval(self) -> str:
        return get_config('predict.data.interval', '5m')
    
    @property
    def data_start_date(self) -> str:
        return get_config('predict.data.start_date', '2019-01-01')
    
    @property
    def data_end_date(self) -> str:
        return get_config('predict.data.end_date', '')
    
    @property
    def data_train_ratio(self) -> float:
        return get_config('predict.data.train_ratio', 0.7)
    
    @property
    def data_val_ratio(self) -> float:
        return get_config('predict.data.val_ratio', 0.15)
    
    @property
    def data_test_ratio(self) -> float:
        return get_config('predict.data.test_ratio', 0.15)
    
    # 模型配置
    @property
    def model_input_dim(self) -> int:
        return get_config('predict.model.input_dim', 5)
    
    @property
    def model_channels(self) -> int:
        return get_config('predict.model.channels', 64)
    
    @property
    def model_num_layers(self) -> int:
        return get_config('predict.model.num_layers', 8)
    
    @property
    def model_kernel_size(self) -> int:
        return get_config('predict.model.kernel_size', 3)
    
    @property
    def model_dropout(self) -> float:
        return get_config('predict.model.dropout', 0.2)
    
    # 训练配置
    @property
    def train_batch_size(self) -> int:
        return get_config('predict.training.batch_size', 128)
    
    @property
    def train_learning_rate(self) -> float:
        return get_config('predict.training.learning_rate', 0.001)
    
    @property
    def train_epochs(self) -> int:
        return get_config('predict.training.epochs', 100)
    
    @property
    def train_early_stopping_patience(self) -> int:
        return get_config('predict.training.early_stopping_patience', 15)
    
    @property
    def train_lambda_cls(self) -> float:
        return get_config('predict.training.lambda_cls', 1.0)
    
    @property
    def train_lambda_reg(self) -> float:
        return get_config('predict.training.lambda_reg', 0.5)
    
    @property
    def train_device(self) -> str:
        import torch
        default_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return get_config('predict.training.device', default_device)
    
    # 推理配置
    @property
    def inference_min_confidence(self) -> float:
        return get_config('predict.inference.min_confidence', 0.65)
    
    @property
    def inference_min_space(self) -> float:
        return get_config('predict.inference.min_space', 0.01)
    
    # 服务配置
    @property
    def data_service_url(self) -> str:
        return get_config('predict.data_service_url', 'http://localhost:8001')
    
    @property
    def features_service_url(self) -> str:
        return get_config('predict.features_service_url', 'http://localhost:8002')
    
    @property
    def symbol(self) -> str:
        return get_config('data.symbol', 'BTCUSDT')
    
    # 邮件配置（优先环境变量）
    @property
    def notification_enabled(self) -> bool:
        return get_config('notification.email.enabled', False)
    
    @property
    def smtp_server(self) -> str:
        return get_config('notification.email.smtp_server', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        return get_config('notification.email.smtp_port', 587)
    
    @property
    def smtp_use_tls(self) -> bool:
        return get_config('notification.email.smtp_use_tls', True)
    
    @property
    def smtp_user(self) -> str:
        return get_config('notification.email.smtp_user', '')
    
    @property
    def smtp_password(self) -> str:
        return get_config('notification.email.smtp_password', '')
    
    @property
    def from_email(self) -> str:
        return get_config('notification.email.from_email', self.smtp_user)
    
    @property
    def to_email(self) -> str:
        return get_config('notification.email.to_email', self.smtp_user)
    
    # 交易配置
    @property
    def trading_mode(self) -> str:
        return get_config('trading.mode', 'backtest')
    
    @property
    def binance_api_key(self) -> str:
        return get_config('trading.binance.api_key', '')
    
    @property
    def binance_api_secret(self) -> str:
        return get_config('trading.binance.api_secret', '')
    
    @property
    def use_testnet(self) -> bool:
        return get_config('trading.binance.use_testnet', False)
    
    @property
    def risk_amount(self) -> float:
        return get_config('trading.risk.risk_amount', 100.0)
    
    @property
    def min_rr_threshold(self) -> float:
        return get_config('trading.risk.min_rr_threshold', 1.5)
    
    @property
    def leverage(self) -> int:
        return get_config('trading.risk.leverage', 20)
    
    @property
    def log_level(self) -> str:
        return get_config('trading.log_level', 'INFO')
    
    # 路径配置
    @property
    def logs_directory(self) -> Path:
        """日志目录"""
        return self.logs_dir
    
    @property
    def cache_directory(self) -> Path:
        """缓存目录"""
        return self.cache_dir
    
    @property
    def models_directory(self) -> Path:
        """模型目录"""
        return self.models_dir
    
    def get_log_path(self, log_name: str) -> Path:
        """获取日志文件路径"""
        return self.logs_dir / log_name
    
    def get_cache_path(self, cache_name: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / cache_name
    
    def get_model_path(self, model_name: str) -> Path:
        """获取模型目录路径"""
        return self.models_dir / model_name
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）
        
        Args:
            key: 配置键，支持 'predict.label.alpha' 格式
            default: 默认值
            
        Returns:
            配置值
        """
        return get_config(key, default)
    
    def __repr__(self) -> str:
        return f"Config(loader=common.config_loader)"


# 全局配置实例（向后兼容）
_global_config = None

def get_config_instance() -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


# 向后兼容的配置类
class LabelConfig:
    """标签生成配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
    
    @property
    def ALPHA(self): return self._config.label_alpha
    
    @property
    def GAMMA(self): return self._config.label_gamma
    
    @property
    def BETA(self): return self._config.label_beta
    
    @property
    def THETA_MIN(self): return self._config.label_theta_min
    
    @property
    def K(self): return self._config.label_K


class DataConfig:
    """数据配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
    
    @property
    def WINDOW_SIZE(self): return self._config.data_window_size
    
    @property
    def INTERVAL(self): return self._config.data_interval
    
    @property
    def START_DATE(self): return self._config.data_start_date
    
    @property
    def END_DATE(self): return self._config.data_end_date
    
    @property
    def TRAIN_RATIO(self): return self._config.data_train_ratio
    
    @property
    def VAL_RATIO(self): return self._config.data_val_ratio
    
    @property
    def TEST_RATIO(self): return self._config.data_test_ratio


class ModelConfig:
    """模型配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
    
    @property
    def INPUT_DIM(self): return self._config.model_input_dim
    
    @property
    def CHANNELS(self): return self._config.model_channels
    
    @property
    def NUM_LAYERS(self): return self._config.model_num_layers
    
    @property
    def KERNEL_SIZE(self): return self._config.model_kernel_size
    
    @property
    def DROPOUT(self): return self._config.model_dropout


class TrainConfig:
    """训练配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
    
    @property
    def BATCH_SIZE(self): return self._config.train_batch_size
    
    @property
    def LEARNING_RATE(self): return self._config.train_learning_rate
    
    @property
    def EPOCHS(self): return self._config.train_epochs
    
    @property
    def EARLY_STOPPING_PATIENCE(self): return self._config.train_early_stopping_patience
    
    @property
    def LAMBDA_CLS(self): return self._config.train_lambda_cls
    
    @property
    def LAMBDA_REG(self): return self._config.train_lambda_reg
    
    @property
    def DEVICE(self): return self._config.train_device


class InferenceConfig:
    """推理配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
    
    @property
    def MIN_CONFIDENCE(self): return self._config.inference_min_confidence
    
    @property
    def MIN_SPACE(self): return self._config.inference_min_space


class ServiceConfig:
    """服务配置（向后兼容）"""
    def __init__(self):
        self._config = get_config_instance()
        self.MODEL_DIR = Path(__file__).parent / 'models'
        self.MODEL_DIR.mkdir(exist_ok=True)
    
    @property
    def DATA_SERVICE_URL(self): return self._config.data_service_url
    
    @property
    def FEATURES_SERVICE_URL(self): return self._config.features_service_url


# 全局配置实例（向后兼容）
label_config = LabelConfig()
data_config = DataConfig()
model_config = ModelConfig()
train_config = TrainConfig()
inference_config = InferenceConfig()
service_config = ServiceConfig()
