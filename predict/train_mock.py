"""
使用模拟数据的训练脚本 - 验证训练流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import torch
import logging
from pathlib import Path
from datetime import datetime, timedelta

from src.label_generator import LabelGenerator
from src.tcn_model import create_tcn_model
from src.data_loader import split_data, create_dataloaders
from src.model_trainer import ModelTrainer
from src.backtest import BacktestEngine
from config import (
    label_config, data_config, model_config, 
    train_config, service_config
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_data(n_samples=2000):
    """生成模拟的K线数据"""
    logger.info(f"Generating {n_samples} mock K-line data...")
    
    # 生成时间序列
    start_time = datetime.now() - timedelta(minutes=5*n_samples)
    timestamps = [start_time + timedelta(minutes=5*i) for i in range(n_samples)]
    
    # 生成价格数据（随机游走 + 趋势）
    np.random.seed(42)
    base_price = 50000
    returns = np.random.randn(n_samples) * 0.002  # 0.2% 波动
    trend = np.linspace(0, 0.1, n_samples)  # 10% 上涨趋势
    
    close_prices = base_price * np.exp(np.cumsum(returns) + trend)
    
    # 生成OHLCV
    data = []
    for i, (ts, close) in enumerate(zip(timestamps, close_prices)):
        high = close * (1 + abs(np.random.randn() * 0.001))
        low = close * (1 - abs(np.random.randn() * 0.001))
        open_price = close_prices[i-1] if i > 0 else close
        volume = abs(np.random.randn() * 1000 + 5000)
        
        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df = df.set_index('timestamp')
    
    logger.info(f"Generated data from {df.index[0]} to {df.index[-1]}")
    logger.info(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


def main():
    logger.info("="*60)
    logger.info("BTC Quant - TCN Model Training (Mock Data)")
    logger.info("="*60)
    
    # 1. 生成模拟数据
    logger.info("\n[Step 1/6] Generating mock data...")
    df = generate_mock_data(n_samples=2000)
    
    # 2. 生成标签
    logger.info("\n[Step 2/6] Generating labels...")
    label_generator = LabelGenerator(
        alpha=label_config.ALPHA,
        gamma=label_config.GAMMA,
        beta=label_config.BETA,
        theta_min=label_config.THETA_MIN,
        K=label_config.K
    )
    
    df_with_labels = label_generator.generate_labels(df)
    
    # 移除没有标签的样本
    valid_mask = df_with_labels.index < (df_with_labels.index[-1] - pd.Timedelta(minutes=5*label_config.K))
    df_with_labels = df_with_labels[valid_mask]
    
    logger.info(f"Valid samples: {len(df_with_labels)}")
    
    # 3. 划分数据集
    logger.info("\n[Step 3/6] Splitting dataset...")
    train_df, val_df, test_df = split_data(
        df_with_labels,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    # 创建数据加载器
    train_loader, val_loader, test_loader = create_dataloaders(
        train_df, val_df, test_df,
        window_size=data_config.WINDOW_SIZE,
        batch_size=32,
        num_workers=0
    )
    
    # 4. 创建模型
    logger.info("\n[Step 4/6] Creating TCN model...")
    model = create_tcn_model(
        input_dim=model_config.INPUT_DIM,
        channels=model_config.CHANNELS,
        num_layers=model_config.NUM_LAYERS,
        kernel_size=model_config.KERNEL_SIZE,
        dropout=model_config.DROPOUT
    )
    
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Total parameters: {total_params:,}")
    
    # 5. 训练模型
    logger.info("\n[Step 5/6] Training model...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = service_config.MODEL_DIR / f"tcn_mock_{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    trainer = ModelTrainer(
        model=model,
        device=train_config.DEVICE,
        learning_rate=train_config.LEARNING_RATE,
        lambda_cls=train_config.LAMBDA_CLS,
        lambda_reg=train_config.LAMBDA_REG,
        theta_min=label_config.THETA_MIN
    )
    
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=10,  # 训练10个epoch
        early_stopping_patience=5,
        save_dir=save_dir
    )
    
    # 6. 回测评估
    logger.info("\n[Step 6/6] Running backtest...")
    
    best_model_path = save_dir / 'best_model.pt'
    if best_model_path.exists():
        trainer.load_model(best_model_path)
    
    backtest_engine = BacktestEngine(
        initial_capital=10000.0,
        leverage=20
    )
    
    metrics = backtest_engine.run_backtest(
        model=model,
        test_data=test_df,
        window_size=data_config.WINDOW_SIZE,
        min_confidence=0.65,
        device=train_config.DEVICE
    )
    
    backtest_engine.print_metrics(metrics)
    
    # 保存回测结果
    import json
    with open(save_dir / 'backtest_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("\n" + "="*60)
    logger.info(f"Training completed! Models saved to {save_dir}")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Check the training history in training_history.json")
    logger.info("2. Review backtest metrics in backtest_metrics.json")
    logger.info("3. If results are good, train on real data using train.py")


if __name__ == "__main__":
    main()
