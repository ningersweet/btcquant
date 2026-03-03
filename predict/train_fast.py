"""
快速训练版本 - 使用更少的数据和更少的epoch
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import torch
import logging
from pathlib import Path
from datetime import datetime
import requests

from src.label_generator import LabelGenerator
from src.tcn_model import create_tcn_model
from src.data_loader import split_data, create_dataloaders
from src.model_trainer import ModelTrainer
from src.backtest import BacktestEngine
from config import (
    label_config, data_config, model_config, 
    train_config, service_config
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_recent_data(months=3):
    """获取最近几个月的数据"""
    logger.info(f"Fetching recent {months} months data...")
    
    url = f"{service_config.DATA_SERVICE_URL}/api/v1/klines"
    
    # 计算时间范围（最近N个月）
    from datetime import timedelta
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=30*months)).timestamp() * 1000)
    
    session = requests.Session()
    session.trust_env = False
    
    all_data = []
    batch_size = 1500
    current_start = start_time
    
    while current_start < end_time:
        params = {
            'symbol': 'BTCUSDT',
            'interval': '5m',
            'start_time': current_start,
            'end_time': end_time,
            'limit': batch_size
        }
        
        response = session.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        batch_data = result['data']
        
        if not batch_data:
            break
        
        all_data.extend(batch_data)
        current_start = batch_data[-1]['timestamp'] + 1
        
        if len(batch_data) < batch_size:
            break
    
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df[~df.index.duplicated(keep='first')].sort_index()
    
    logger.info(f"Fetched {len(df)} K-lines from {df.index[0]} to {df.index[-1]}")
    return df


def main():
    logger.info("="*60)
    logger.info("BTC Quant - TCN Model Fast Training")
    logger.info("="*60)
    
    # 1. 获取最近3个月的数据
    logger.info("\n[Step 1/6] Fetching recent data...")
    df = fetch_recent_data(months=3)
    
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
    
    # 4. 创建数据加载器（增大batch size）
    train_loader, val_loader, test_loader = create_dataloaders(
        train_df, val_df, test_df,
        window_size=data_config.WINDOW_SIZE,
        batch_size=256,  # 增大到256
        num_workers=0
    )
    
    # 5. 创建更小的模型
    logger.info("\n[Step 4/6] Creating TCN model...")
    model = create_tcn_model(
        input_dim=model_config.INPUT_DIM,
        channels=32,  # 减少通道数：64->32
        num_layers=6,  # 减少层数：8->6
        kernel_size=model_config.KERNEL_SIZE,
        dropout=model_config.DROPOUT
    )
    
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Total parameters: {total_params:,}")
    
    # 6. 训练模型（减少epoch）
    logger.info("\n[Step 5/6] Training model...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = service_config.MODEL_DIR / f"tcn_fast_{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    trainer = ModelTrainer(
        model=model,
        device=train_config.DEVICE,
        learning_rate=0.002,  # 增大学习率
        lambda_cls=train_config.LAMBDA_CLS,
        lambda_reg=train_config.LAMBDA_REG,
        theta_min=label_config.THETA_MIN
    )
    
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=20,  # 只训练20个epoch
        early_stopping_patience=5,
        save_dir=save_dir
    )
    
    # 7. 回测评估
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
    
    import json
    with open(save_dir / 'backtest_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("\n" + "="*60)
    logger.info(f"Fast training completed! Models saved to {save_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
