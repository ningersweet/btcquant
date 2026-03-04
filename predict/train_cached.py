"""
优化的训练脚本 - 支持数据缓存

第一次运行时从API获取并缓存，后续直接读取缓存
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
import pickle

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


def fetch_historical_data_cached(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    start_date: str = "2019-01-01",
    end_date: str = None,
    cache_file: str = "data_cache.pkl"
) -> pd.DataFrame:
    """
    获取历史数据（支持缓存）
    """
    cache_path = Path(__file__).parent / cache_file
    
    # 检查缓存
    if cache_path.exists():
        logger.info(f"Loading data from cache: {cache_path}")
        try:
            with open(cache_path, 'rb') as f:
                df = pickle.load(f)
            logger.info(f"Loaded {len(df)} K-lines from cache")
            logger.info(f"Date range: {df.index[0]} to {df.index[-1]}")
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}, fetching from API...")
    
    # 从API获取数据
    logger.info(f"Fetching data from API (this may take a while)...")
    logger.info(f"From {start_date} to {end_date or 'now'}")
    
    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    if end_date:
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
    else:
        end_ts = int(pd.Timestamp.now().timestamp() * 1000)
    
    url = f"{service_config.DATA_SERVICE_URL}/api/v1/klines"
    
    session = requests.Session()
    session.trust_env = False
    
    all_data = []
    batch_size = 1500
    current_start = start_ts
    batch_count = 0
    
    try:
        while current_start < end_ts:
            params = {
                'symbol': symbol,
                'interval': interval,
                'start_time': current_start,
                'end_time': end_ts,
                'limit': batch_size
            }
            
            batch_count += 1
            if batch_count % 10 == 0:
                logger.info(f"Fetching batch {batch_count}, total records: {len(all_data)}")
            
            response = session.get(url, params=params, timeout=180)
            response.raise_for_status()
            
            result = response.json()
            if result['code'] != 0:
                raise Exception(f"API error: {result.get('message', 'Unknown error')}")
            
            batch_data = result['data']
            if not batch_data:
                break
            
            all_data.extend(batch_data)
            
            last_timestamp = batch_data[-1]['timestamp']
            current_start = last_timestamp + 1
            
            if len(batch_data) < batch_size:
                break
        
        if not all_data:
            raise Exception("No data fetched")
        
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df = df[~df.index.duplicated(keep='first')].sort_index()
        
        logger.info(f"Fetched {len(df)} K-lines from {df.index[0]} to {df.index[-1]}")
        
        # 保存缓存
        logger.info(f"Saving data to cache: {cache_path}")
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)
        logger.info("Cache saved successfully")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise


def main():
    logger.info("="*60)
    logger.info("BTC Quant - TCN Model Training (Cached)")
    logger.info("="*60)
    
    # 打印设备信息
    logger.info(f"\n[Device Info]")
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"GPU count: {torch.cuda.device_count()}")
        logger.info(f"GPU name: {torch.cuda.get_device_name(0)}")
    logger.info(f"Training device: {train_config.DEVICE}")
    
    # 1. 获取历史数据（使用缓存）
    logger.info("\n[Step 1/6] Loading historical data...")
    try:
        df = fetch_historical_data_cached(
            symbol="BTCUSDT",
            interval=data_config.INTERVAL,
            start_date=data_config.START_DATE,
            end_date=data_config.END_DATE
        )
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
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
    logger.info(f"Total parameters: {total_params:,}")
    
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
    logger.info("\n[Step 6/6] Running backtest...")
    
    best_model_path = save_dir / 'best_model.pt'
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
    logger.info(f"Training completed! Models saved to {save_dir}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
