#!/usr/bin/env python3
"""
统一训练脚本

支持多种训练模式：
- 完整训练：使用所有历史数据
- 缓存训练：使用预先准备的数据缓存
- 增量训练：在已有模型基础上继续训练
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_loader import load_klines_from_service, split_data
from src.label_generator import LabelGenerator
from src.model_trainer import ModelTrainer
from src.tcn_model import TCNModel
from src.backtest import Backtester
from config import Config

# 配置日志
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_data_from_cache(cache_file: Path):
    """从缓存加载数据"""
    import pickle
    
    logger.info(f"从缓存加载数据: {cache_file}")
    with open(cache_file, 'rb') as f:
        data = pickle.load(f)
    
    logger.info(f"数据加载完成: {len(data['df'])} 条记录")
    return data['df'], data.get('train_df'), data.get('val_df'), data.get('test_df')


def load_data_from_service(config: Config):
    """从数据服务加载数据"""
    logger.info("从数据服务加载K线数据...")
    
    df = load_klines_from_service(
        symbol=config.symbol,
        interval=config.data_interval,
        start_date=config.data_start_date,
        end_date=config.data_end_date,
        service_url=config.data_service_url
    )
    
    logger.info(f"数据加载完成: {len(df)} 条记录")
    logger.info(f"时间范围: {df.index[0]} 至 {df.index[-1]}")
    
    return df, None, None, None


def generate_labels(df, config: Config):
    """生成训练标签"""
    logger.info("生成训练标签...")
    
    generator = LabelGenerator(
        alpha=config.label_alpha,
        gamma=config.label_gamma,
        beta=config.label_beta,
        theta_min=config.label_theta_min,
        K=config.label_K,
        n_jobs=-1  # 使用所有CPU核心
    )
    
    df_labeled = generator.generate_labels(df)
    logger.info("标签生成完成")
    
    return df_labeled


def train_model(train_df, val_df, test_df, config: Config, model_dir: Path, base_model_path=None):
    """训练模型"""
    logger.info("开始训练模型...")
    
    # 创建模型
    model = TCNModel(
        input_dim=config.model_input_dim,
        num_channels=config.model_channels,
        num_layers=config.model_num_layers,
        kernel_size=config.model_kernel_size,
        dropout=config.model_dropout
    )
    
    # 加载基础模型（增量训练）
    if base_model_path:
        logger.info(f"加载基础模型: {base_model_path}")
        import torch
        model.load_state_dict(torch.load(base_model_path))
    
    # 创建训练器
    trainer = ModelTrainer(
        model=model,
        window_size=config.data_window_size,
        batch_size=config.train_batch_size,
        learning_rate=config.train_learning_rate,
        device=config.train_device,
        lambda_cls=config.train_lambda_cls,
        lambda_reg=config.train_lambda_reg
    )
    
    # 训练
    history = trainer.train(
        train_df=train_df,
        val_df=val_df,
        epochs=config.train_epochs,
        early_stopping_patience=config.train_early_stopping_patience,
        save_dir=model_dir
    )
    
    logger.info("模型训练完成")
    
    # 回测
    if test_df is not None and len(test_df) > 0:
        logger.info("开始回测...")
        backtester = Backtester(
            model=model,
            window_size=config.data_window_size,
            device=config.train_device,
            min_confidence=config.inference_min_confidence,
            min_space=config.inference_min_space
        )
        
        metrics = backtester.backtest(test_df)
        
        # 保存回测结果
        import json
        with open(model_dir / 'backtest_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info("回测完成")
        logger.info(f"回测指标: {metrics}")
    
    return history


def main():
    parser = argparse.ArgumentParser(description='TCN模型训练')
    parser.add_argument('--mode', type=str, default='cache',
                        choices=['full', 'cache', 'incremental'],
                        help='训练模式: full=完整训练, cache=使用缓存, incremental=增量训练')
    parser.add_argument('--cache-file', type=str, default='data_cache.pkl',
                        help='数据缓存文件路径')
    parser.add_argument('--base-model', type=str,
                        help='基础模型路径（增量训练）')
    parser.add_argument('--config', type=str,
                        help='配置文件路径')
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config()
    if args.config:
        config.load_from_file(args.config)
    
    logger.info("="*60)
    logger.info("BTC Quant - TCN模型训练")
    logger.info("="*60)
    logger.info(f"训练模式: {args.mode}")
    logger.info(f"设备: {config.train_device}")
    logger.info(f"批次大小: {config.train_batch_size}")
    logger.info(f"学习率: {config.train_learning_rate}")
    logger.info(f"训练轮数: {config.train_epochs}")
    
    # 创建模型保存目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = Path(__file__).parent / 'models' / f'tcn_{timestamp}'
    model_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"模型保存目录: {model_dir}")
    
    # 加载数据
    if args.mode == 'cache':
        cache_file = Path(args.cache_file)
        if not cache_file.exists():
            logger.error(f"缓存文件不存在: {cache_file}")
            logger.info("请先运行: btcquant data prepare")
            return 1
        
        df, train_df, val_df, test_df = load_data_from_cache(cache_file)
        
        # 如果缓存中没有划分好的数据集，则重新划分
        if train_df is None:
            logger.info("缓存中没有划分好的数据集，重新划分...")
            train_df, val_df, test_df = split_data(
                df,
                train_ratio=config.data_train_ratio,
                val_ratio=config.data_val_ratio,
                test_ratio=config.data_test_ratio
            )
    else:
        df, _, _, _ = load_data_from_service(config)
        
        # 生成标签
        df = generate_labels(df, config)
        
        # 划分数据集
        logger.info("划分数据集...")
        train_df, val_df, test_df = split_data(
            df,
            train_ratio=config.data_train_ratio,
            val_ratio=config.data_val_ratio,
            test_ratio=config.data_test_ratio
        )
    
    logger.info(f"训练集: {len(train_df)} 条")
    logger.info(f"验证集: {len(val_df)} 条")
    logger.info(f"测试集: {len(test_df)} 条")
    
    # 训练模型
    base_model_path = args.base_model if args.mode == 'incremental' else None
    history = train_model(train_df, val_df, test_df, config, model_dir, base_model_path)
    
    logger.info("="*60)
    logger.info("训练完成！")
    logger.info(f"模型保存在: {model_dir}")
    logger.info("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
