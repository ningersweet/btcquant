"""
直接从数据库读取数据的训练脚本

避免API超时问题
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
import sqlite3

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


def fetch_from_database(
    db_path: str = "/Users/lemonshwang/project/btc_quant/data_storage/btc_quant.db",
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    start_date: str = "2019-09-01"
):
    """
    直接从SQLite数据库读取数据
    """
    logger.info(f"Reading data from database: {db_path}")
    logger.info(f"Symbol: {symbol}, Interval: {interval}, Start: {start_date}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    
    # 转换日期为时间戳
    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    
    # 查询数据
    query = f"""
    SELECT timestamp, open, high, low, close, volume
    FROM klines
    WHERE symbol = ? AND interval = ? AND timestamp >= ?
    ORDER BY timestamp ASC
    """
    
    logger.info("Executing database query...")
    df = pd.read_sql_query(query, conn, params=(symbol, interval, start_ts))
    conn.close()
    
    if len(df) == 0:
        raise Exception("No data found in database")
    
    # 转换数据类型
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    logger.info(f"Loaded {len(df)} K-lines from {df.index[0]} to {df.index[-1]}")
    
    return df


def main():
    logger.info("="*60)
    logger.info("BTC Quant - TCN Model Training (Database Direct)")
    logger.info("="*60)
    
    # 1. 从数据库读取数据
    logger.info("\n[Step 1/6] Loading data from database...")
    try:
        df = fetch_from_database(
            symbol="BTCUSDT",
            interval=data_config.INTERVAL,
            start_date=data_config.START_DATE
        )
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return
    
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
    
    logger.info(f"Valid samples after label generation: {len(df_with_labels)}")
    
    # 3. 划分数据集
    logger.info("\n[Step 3/6] Splitting dataset...")
    train_df, val_df, test_df = split_data(
        df_with_labels,
        train_ratio=data_config.TRAIN_RATIO,
        val_ratio=data_config.VAL_RATIO,
        test_ratio=data_config.TEST_RATIO
    )
    
    # 创建数据加载器
    train_loader, val_loader, test_loader = create_dataloaders(
        train_df, val_df, test_df,
        window_size=data_config.WINDOW_SIZE,
        batch_size=train_config.BATCH_SIZE,
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
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # 5. 训练模型
    logger.info("\n[Step 5/6] Training model...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = service_config.MODEL_DIR / f"tcn_{timestamp}"
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
        epochs=train_config.EPOCHS,
        early_stopping_patience=train_config.EARLY_STOPPING_PATIENCE,
        save_dir=save_dir
    )
    
    # 6. 回测评估
    logger.info("\n[Step 6/6] Running backtest on test set...")
    
    best_model_path = save_dir / 'best_model.pt'
    trainer.load_model(best_model_path)
    
    backtest_engine = BacktestEngine(
        initial_capital=10000.0,
        leverage=20,
        maker_fee=0.0002,
        taker_fee=0.0004,
        slippage=0.0001
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
    
    # 导出ONNX模型
    logger.info("\n[Bonus] Exporting to ONNX format...")
    try:
        dummy_input = torch.randn(1, data_config.WINDOW_SIZE, model_config.INPUT_DIM)
        onnx_path = save_dir / 'model.onnx'
        
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['cls_output', 'reg_output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'cls_output': {0: 'batch_size'},
                'reg_output': {0: 'batch_size'}
            }
        )
        logger.info(f"ONNX model saved to {onnx_path}")
    except Exception as e:
        logger.warning(f"Failed to export ONNX: {e}")
    
    logger.info("\n" + "="*60)
    logger.info(f"Training completed! Models saved to {save_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
