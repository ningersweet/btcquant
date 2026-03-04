"""
预测服务配置模块

从环境变量加载TCN模型配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class LabelConfig:
    """标签生成配置"""
    
    # 缓冲系数
    ALPHA = float(os.getenv('LABEL_ALPHA', '0.0015'))  # 入场缓冲
    GAMMA = float(os.getenv('LABEL_GAMMA', '0.0040'))  # 止盈缓冲
    BETA = float(os.getenv('LABEL_BETA', '0.0025'))    # 止损缓冲
    
    # 阈值
    THETA_MIN = float(os.getenv('LABEL_THETA_MIN', '0.0100'))  # 最小净利阈值
    
    # 预测窗口
    K = int(os.getenv('LABEL_K', '12'))  # 未来K线数量


class DataConfig:
    """数据配置"""
    
    WINDOW_SIZE = int(os.getenv('DATA_WINDOW_SIZE', '288'))  # 输入窗口
    INTERVAL = os.getenv('DATA_INTERVAL', '5m')  # K线间隔
    START_DATE = os.getenv('DATA_START_DATE', '2019-01-01')
    END_DATE = os.getenv('DATA_END_DATE', '')  # 空则使用当前日期
    
    # 数据集划分
    TRAIN_RATIO = float(os.getenv('DATA_TRAIN_RATIO', '0.7'))
    VAL_RATIO = float(os.getenv('DATA_VAL_RATIO', '0.15'))
    TEST_RATIO = float(os.getenv('DATA_TEST_RATIO', '0.15'))


class ModelConfig:
    """TCN模型配置"""
    
    INPUT_DIM = int(os.getenv('MODEL_INPUT_DIM', '5'))  # OHLCV
    CHANNELS = int(os.getenv('MODEL_CHANNELS', '64'))
    NUM_LAYERS = int(os.getenv('MODEL_NUM_LAYERS', '8'))
    KERNEL_SIZE = int(os.getenv('MODEL_KERNEL_SIZE', '3'))
    DROPOUT = float(os.getenv('MODEL_DROPOUT', '0.2'))


class TrainConfig:
    """训练配置"""
    
    BATCH_SIZE = int(os.getenv('TRAIN_BATCH_SIZE', '128'))
    LEARNING_RATE = float(os.getenv('TRAIN_LEARNING_RATE', '0.001'))
    EPOCHS = int(os.getenv('TRAIN_EPOCHS', '100'))
    EARLY_STOPPING_PATIENCE = int(os.getenv('TRAIN_EARLY_STOPPING_PATIENCE', '15'))
    
    # 损失权重
    LAMBDA_CLS = float(os.getenv('TRAIN_LAMBDA_CLS', '1.0'))
    LAMBDA_REG = float(os.getenv('TRAIN_LAMBDA_REG', '0.5'))
    
    # 自动检测设备：优先使用GPU
    import torch
    DEVICE = os.getenv('TRAIN_DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')


class InferenceConfig:
    """推理配置"""
    
    MIN_CONFIDENCE = float(os.getenv('INFERENCE_MIN_CONFIDENCE', '0.65'))
    MIN_SPACE = float(os.getenv('INFERENCE_MIN_SPACE', '0.01'))


class ServiceConfig:
    """服务配置"""
    
    DATA_SERVICE_URL = os.getenv('DATA_SERVICE_URL', 'http://localhost:8001')
    FEATURES_SERVICE_URL = os.getenv('FEATURES_SERVICE_URL', 'http://localhost:8002')
    
    # 模型保存路径
    MODEL_DIR = Path(__file__).parent / 'models'
    MODEL_DIR.mkdir(exist_ok=True)


# 全局配置实例
label_config = LabelConfig()
data_config = DataConfig()
model_config = ModelConfig()
train_config = TrainConfig()
inference_config = InferenceConfig()
service_config = ServiceConfig()
