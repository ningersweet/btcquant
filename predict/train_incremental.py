"""
增量训练脚本

用于定期更新模型（建议在GPU上运行）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import logging
from pathlib import Path
from datetime import datetime, timedelta

from src.model_trainer import ModelTrainer
from src.data_loader import create_dataloaders, split_data
from train_cached import fetch_historical_data_cached
from src.label_generator import LabelGenerator
from config import label_config, data_config, model_config, train_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def incremental_train(
    base_model_path: str,
    days_back: int = 30,
    epochs: int = 10,
    device: str = 'cuda'
):
    """
    增量训练
    
    Args:
        base_model_path: 基础模型路径
        days_back: 使用最近N天的数据
        epochs: 训练轮数
        device: 训练设备
    """
    logger.info("="*60)
    logger.info("Incremental Training")
    logger.info("="*60)
    
    # 1. 加载基础模型
    logger.info(f"\n[1/5] Loading base model from {base_model_path}")
    checkpoint = torch.load(base_model_path, map_location=device)
    
    from src.tcn_model import TCNModel
    model = TCNModel(
        input_dim=model_config.INPUT_DIM,
        channels=model_config.CHANNELS,
        num_layers=model_config.NUM_LAYERS,
        kernel_size=model_config.KERNEL_SIZE,
        dropout=model_config.DROPOUT
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    logger.info(f"Base model loaded (epoch {checkpoint['epoch']})")
    
    # 2. 获取最近的数据
    logger.info(f"\n[2/5] Fetching recent {days_back} days data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    df = fetch_historical_data_cached(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        cache_file=f"incremental_cache_{start_date.strftime('%Y%m%d')}.pkl"
    )
    
    # 3. 生成标签
    logger.info("\n[3/5] Generating labels...")
    label_generator = LabelGenerator(
        alpha=label_config.ALPHA,
        gamma=label_config.GAMMA,
        beta=label_config.BETA,
        theta_min=label_config.THETA_MIN,
        K=label_config.K
    )
    df_with_labels = label_generator.generate_labels(df)
    
    # 4. 创建数据加载器
    logger.info("\n[4/5] Creating data loaders...")
    train_df, val_df, test_df = split_data(df_with_labels, 0.8, 0.1, 0.1)
    train_loader, val_loader, test_loader = create_dataloaders(
        train_df, val_df, test_df,
        window_size=data_config.WINDOW_SIZE,
        batch_size=train_config.BATCH_SIZE,
        num_workers=0
    )
    
    # 5. 增量训练
    logger.info(f"\n[5/5] Incremental training for {epochs} epochs...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = Path("models") / f"tcn_incremental_{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用较小的学习率进行微调
    trainer = ModelTrainer(
        model=model,
        device=device,
        learning_rate=train_config.LEARNING_RATE * 0.1,  # 降低学习率
        lambda_cls=train_config.LAMBDA_CLS,
        lambda_reg=train_config.LAMBDA_REG,
        theta_min=label_config.THETA_MIN
    )
    
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=epochs,
        early_stopping_patience=5,
        save_dir=save_dir
    )
    
    logger.info("\n" + "="*60)
    logger.info(f"Incremental training completed!")
    logger.info(f"New model saved to {save_dir}")
    logger.info("="*60)
    
    return save_dir


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-model', required=True, help='Base model path')
    parser.add_argument('--days', type=int, default=30, help='Days of data to use')
    parser.add_argument('--epochs', type=int, default=10, help='Training epochs')
    parser.add_argument('--device', default='cuda', help='Training device')
    
    args = parser.parse_args()
    
    incremental_train(
        base_model_path=args.base_model,
        days_back=args.days,
        epochs=args.epochs,
        device=args.device
    )
