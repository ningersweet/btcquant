"""
预测服务配置模块

统一使用YAML配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """统一配置类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，默认为根目录的 config.yaml
        """
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        
        # 默认使用根目录的config.yaml
        if config_file:
            self.config_file = Path(config_file)
        else:
            # 优先使用根目录的config.yaml
            root_config = self.project_root / 'config.yaml'
            if root_config.exists():
                self.config_file = root_config
            else:
                # 尝试使用示例配置
                example_config = self.project_root / 'config.yaml.example'
                if example_config.exists():
                    self.config_file = example_config
                else:
                    # 最后尝试predict目录
                    self.config_file = self.config_dir / 'config.yaml'
        
        # 统一存储目录
        self.storage_dir = self.project_root / 'storage'
        self.logs_dir = self.storage_dir / 'logs'
        self.cache_dir = self.storage_dir / 'cache'
        self.models_dir = self.storage_dir / 'models'
        
        # 创建目录
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self._config = self._get_default_config()
        
        # 加载配置文件
        if self.config_file.exists():
            self.load_from_file(self.config_file)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        import torch
        
        return {
            'predict': {
                'label': {
                    'alpha': 0.0015,
                    'gamma': 0.0040,
                    'beta': 0.0025,
                    'theta_min': 0.0100,
                    'K': 12
                },
                'data': {
                    'window_size': 288,
                    'interval': '5m',
                    'start_date': '2019-01-01',
                    'end_date': '',
                    'train_ratio': 0.7,
                    'val_ratio': 0.15,
                    'test_ratio': 0.15
                },
                'model': {
                    'input_dim': 5,
                    'channels': 64,
                    'num_layers': 8,
                    'kernel_size': 3,
                    'dropout': 0.2
                },
                'training': {
                    'batch_size': 128,
                    'learning_rate': 0.001,
                    'epochs': 100,
                    'early_stopping_patience': 15,
                    'lambda_cls': 1.0,
                    'lambda_reg': 0.5,
                    'device': 'cuda' if torch.cuda.is_available() else 'cpu'
                },
                'inference': {
                    'min_confidence': 0.65,
                    'min_space': 0.01
                },
                'data_service_url': 'http://localhost:8001',
                'features_service_url': 'http://localhost:8002'
            },
            'data': {
                'symbol': 'BTCUSDT',
                'interval': '5m'
            }
        }
    
    def load_from_file(self, config_file: str):
        """
        从YAML文件加载配置
        
        Args:
            config_file: 配置文件路径
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            loaded_config = yaml.safe_load(f)
        
        # 深度合并配置
        self._config = self._deep_merge(self._config, loaded_config)
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_to_file(self, config_file: Optional[str] = None):
        """
        保存配置到YAML文件
        
        Args:
            config_file: 配置文件路径，默认使用初始化时的路径
        """
        save_path = Path(config_file) if config_file else self.config_file
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
    
    # 标签生成配置
    @property
    def label_alpha(self) -> float:
        return self._config['predict']['label']['alpha']
    
    @property
    def label_gamma(self) -> float:
        return self._config['predict']['label']['gamma']
    
    @property
    def label_beta(self) -> float:
        return self._config['predict']['label']['beta']
    
    @property
    def label_theta_min(self) -> float:
        return self._config['predict']['label']['theta_min']
    
    @property
    def label_K(self) -> int:
        return self._config['predict']['label']['K']
    
    # 数据配置
    @property
    def data_window_size(self) -> int:
        return self._config['predict']['data']['window_size']
    
    @property
    def data_interval(self) -> str:
        return self._config['predict']['data']['interval']
    
    @property
    def data_start_date(self) -> str:
        return self._config['predict']['data']['start_date']
    
    @property
    def data_end_date(self) -> str:
        return self._config['predict']['data']['end_date']
    
    @property
    def data_train_ratio(self) -> float:
        return self._config['predict']['data']['train_ratio']
    
    @property
    def data_val_ratio(self) -> float:
        return self._config['predict']['data']['val_ratio']
    
    @property
    def data_test_ratio(self) -> float:
        return self._config['predict']['data']['test_ratio']
    
    # 模型配置
    @property
    def model_input_dim(self) -> int:
        return self._config['predict']['model']['input_dim']
    
    @property
    def model_channels(self) -> int:
        return self._config['predict']['model']['channels']
    
    @property
    def model_num_layers(self) -> int:
        return self._config['predict']['model']['num_layers']
    
    @property
    def model_kernel_size(self) -> int:
        return self._config['predict']['model']['kernel_size']
    
    @property
    def model_dropout(self) -> float:
        return self._config['predict']['model']['dropout']
    
    # 训练配置
    @property
    def train_batch_size(self) -> int:
        return self._config['predict']['training']['batch_size']
    
    @property
    def train_learning_rate(self) -> float:
        return self._config['predict']['training']['learning_rate']
    
    @property
    def train_epochs(self) -> int:
        return self._config['predict']['training']['epochs']
    
    @property
    def train_early_stopping_patience(self) -> int:
        return self._config['predict']['training']['early_stopping_patience']
    
    @property
    def train_lambda_cls(self) -> float:
        return self._config['predict']['training']['lambda_cls']
    
    @property
    def train_lambda_reg(self) -> float:
        return self._config['predict']['training']['lambda_reg']
    
    @property
    def train_device(self) -> str:
        return self._config['predict']['training']['device']
    
    # 推理配置
    @property
    def inference_min_confidence(self) -> float:
        return self._config['predict']['inference']['min_confidence']
    
    @property
    def inference_min_space(self) -> float:
        return self._config['predict']['inference']['min_space']
    
    # 服务配置
    @property
    def data_service_url(self) -> str:
        return self._config['predict']['data_service_url']
    
    @property
    def features_service_url(self) -> str:
        return self._config['predict']['features_service_url']
    
    @property
    def symbol(self) -> str:
        return self._config['data']['symbol']
    
    # 邮件配置（从环境变量读取）
    @property
    def smtp_server(self) -> str:
        return os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        return int(os.getenv('SMTP_PORT', '587'))
    
    @property
    def smtp_user(self) -> str:
        return os.getenv('SMTP_USER', '')
    
    @property
    def smtp_password(self) -> str:
        return os.getenv('SMTP_PASSWORD', '')
    
    @property
    def from_email(self) -> str:
        return os.getenv('FROM_EMAIL', self.smtp_user)
    
    @property
    def to_email(self) -> str:
        return os.getenv('TO_EMAIL', self.smtp_user)
    
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
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值（支持点号分隔的路径）
        
        Args:
            key: 配置键，支持 'predict.label.alpha' 格式
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def __repr__(self) -> str:
        return f"Config(file={self.config_file})"


# 全局配置实例（向后兼容）
_global_config = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


# 向后兼容的配置类
class LabelConfig:
    """标签生成配置（向后兼容）"""
    def __init__(self):
        self._config = get_config()
    
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
        self._config = get_config()
    
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
        self._config = get_config()
    
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
        self._config = get_config()
    
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
        self._config = get_config()
    
    @property
    def MIN_CONFIDENCE(self): return self._config.inference_min_confidence
    
    @property
    def MIN_SPACE(self): return self._config.inference_min_space


class ServiceConfig:
    """服务配置（向后兼容）"""
    def __init__(self):
        self._config = get_config()
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
