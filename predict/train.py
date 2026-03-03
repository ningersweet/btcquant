"""
主训练脚本

完整的训练流程：数据获取 -> 标签生成 -> 模型训练 -> 回测评估
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
import argparse

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


def fetch_historical_data(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    start_date: str = "2019-01-01",
    end_date: str = None
) -> pd.DataFrame:
    """
    从数据服务获取历史数据
    
    Args:
        symbol: 交易对
        interval: K线间隔
        start_date: 开始日期
        end_date: 结束日期（None则使用当前日期）
        
    Returns:
        K线数据DataFrame
    """
    logger.info(f"Fetching historical data from {start_date} to {end_date or 'now'}...")
    
    # 转换日期为时间戳
    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    if end_date:
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
    else:
        end_ts = int(pd.Timestamp.now().timestamp() * 1000)
    
    # 调用数据服务API（分批获取）
    url = f"{service_config.DATA_SERVICE_URL}/api/v1/klines"
    
    # 禁用代理，直接连接localhost
    session = requests.Session()
    session.trust_env = False  # 忽略环境变量中的代理设置
    
    all_data = []
    batch_size = 1500  # 每批最多1500条
    current_start = start_ts
    
    try:
        while current_start < end_ts:
            params = {
                'symbol': symbol,
                'interval': interval,
                'start_time': current_start,
                'end_time': end_ts,
                'limit': batch_size
            }
            
            logger.info(f"Fetching batch starting from {pd.Timestamp(current_start, unit='ms')}")
            response = session.get(url, params=params, timeout=120)  # 增加超时到120秒
            response.raise_for_status()
            
            result = response.json()
            if result['code'] != 0:
                raise Exception(f"API error: {result.get('message', 'Unknown error')}")
            
            batch_data = result['data']
            if not batch_data:
                break
            
            all_data.extend(batch_data)
            
            # 更新下一批的起始时间
            last_timestamp = batch_data[-1]['timestamp']
            current_start = last_timestamp + 1
            
            # 如果返回的数据少于batch_size，说明已经获取完了
            if len(batch_data) < batch_size:
                break
        
        if not all_data:
            raise Exception("No data fetched")
        
        df = pd.DataFrame(all_data)
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        
        # 选择需要的列
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        # 去重并排序
        df = df[~df.index.duplicated(keep='first')].sort_index()
        
        logger.info(f"Fetched {len(df)} K-lines from {df.index[0]} to {df.index[-1]}")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise


def main(args):
    """主训练流程"""
    
    logger.info("="*60)
    logger.info("BTC Quant - TCN Model Training")
    logger.info("="*60)
    
    # 1. 获取历史数据
    logger.info("\n[Step 1/6] Fetching historical data...")
    try:
        df = fetch_historical_data(
            symbol="BTCUSDT",
            interval=data_config.INTERVAL,
            start_date=data_config.START_DATE,
            end_date=data_config.END_DATE
        )
    except Exception as e:
        logger.error(f"Failed to fetch data from service: {e}")
        logger.info("Please ensure data service is running: docker-compose up -d data-service")
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
    
    # 移除没有标签的样本（前面和后面的K根）
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
    
    # 创建保存目录
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
    
    # 加载最佳模型
    best_model_path = save_dir / 'best_model.pt'
    trainer.load_model(best_model_path)
    
    # 运行回测
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
    if not args.skip_onnx:
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
    parser = argparse.ArgumentParser(description='Train TCN model for BTC trading')
    parser.add_argument('--skip-onnx', action='store_true', help='Skip ONNX export')
    args = parser.parse_args()
    
    main(args)
