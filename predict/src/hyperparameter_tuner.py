"""
超参数优化器

使用Optuna进行超参数搜索
"""

import optuna
import torch
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict

from .tcn_model import create_tcn_model
from .model_trainer import ModelTrainer
from .data_loader import create_dataloaders

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """超参数优化器"""
    
    def __init__(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        window_size: int = 288,
        n_trials: int = 50,
        device: str = 'cpu'
    ):
        self.train_df = train_df
        self.val_df = val_df
        self.window_size = window_size
        self.n_trials = n_trials
        self.device = device
        
        logger.info(f"HyperparameterTuner initialized with {n_trials} trials")
    
    def objective(self, trial: optuna.Trial) -> float:
        """
        优化目标函数
        
        Args:
            trial: Optuna trial对象
            
        Returns:
            验证集损失
        """
        # 搜索空间
        channels = trial.suggest_categorical('channels', [32, 64, 128])
        num_layers = trial.suggest_int('num_layers', 6, 10)
        dropout = trial.suggest_float('dropout', 0.1, 0.4)
        learning_rate = trial.suggest_loguniform('learning_rate', 1e-4, 1e-2)
        batch_size = trial.suggest_categorical('batch_size', [64, 128, 256])
        lambda_reg = trial.suggest_float('lambda_reg', 0.3, 0.7)
        
        # 创建数据加载器
        train_loader, val_loader, _ = create_dataloaders(
            self.train_df, self.val_df, self.val_df,  # 测试集用验证集代替
            window_size=self.window_size,
            batch_size=batch_size,
            num_workers=0
        )
        
        # 创建模型
        model = create_tcn_model(
            input_dim=5,
            channels=channels,
            num_layers=num_layers,
            kernel_size=3,
            dropout=dropout
        )
        
        # 训练器
        trainer = ModelTrainer(
            model=model,
            device=self.device,
            learning_rate=learning_rate,
            lambda_cls=1.0,
            lambda_reg=lambda_reg,
            theta_min=0.01
        )
        
        # 训练（少量epoch用于快速评估）
        max_epochs = 20
        best_val_loss = float('inf')
        
        for epoch in range(max_epochs):
            train_loss, _, _ = trainer.train_epoch(train_loader)
            val_loss, _, _, val_acc = trainer.validate(val_loader)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
            
            # 报告中间结果
            trial.report(val_loss, epoch)
            
            # 早停检查
            if trial.should_prune():
                raise optuna.TrialPruned()
        
        return best_val_loss
    
    def optimize(self, save_path: Optional[Path] = None) -> Dict:
        """
        运行超参数优化
        
        Args:
            save_path: 保存最佳参数的路径
            
        Returns:
            最佳参数字典
        """
        study = optuna.create_study(
            direction='minimize',
            pruner=optuna.pruners.MedianPruner()
        )
        
        study.optimize(self.objective, n_trials=self.n_trials)
        
        logger.info(f"Best trial: {study.best_trial.number}")
        logger.info(f"Best value: {study.best_value:.4f}")
        logger.info(f"Best params: {study.best_params}")
        
        # 保存结果
        if save_path:
            import json
            with open(save_path, 'w') as f:
                json.dump({
                    'best_value': study.best_value,
                    'best_params': study.best_params,
                    'n_trials': len(study.trials)
                }, f, indent=2)
            logger.info(f"Best params saved to {save_path}")
        
        return study.best_params


def tune_hyperparameters(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    window_size: int = 288,
    n_trials: int = 50,
    device: str = 'cpu',
    save_path: Optional[Path] = None
) -> Dict:
    """
    便捷函数：超参数优化
    
    Args:
        train_df: 训练数据
        val_df: 验证数据
        window_size: 窗口大小
        n_trials: 试验次数
        device: 设备
        save_path: 保存路径
        
    Returns:
        最佳参数字典
    """
    tuner = HyperparameterTuner(train_df, val_df, window_size, n_trials, device)
    return tuner.optimize(save_path)
