"""
模型训练器

包含训练循环、早停、模型保存等功能
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime
import json

from .tcn_model import TCNModel, TCNLoss

logger = logging.getLogger(__name__)


class EarlyStopping:
    """早停机制"""
    
    def __init__(self, patience: int = 15, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
    
    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.early_stop


class ModelTrainer:
    """模型训练器"""
    
    def __init__(
        self,
        model: TCNModel,
        device: str = 'cpu',
        learning_rate: float = 0.001,
        lambda_cls: float = 1.0,
        lambda_reg: float = 0.5,
        theta_min: float = 0.01
    ):
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        
        # 损失函数
        self.criterion = TCNLoss(lambda_cls, lambda_reg, theta_min)
        
        # 优化器
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # 学习率调度器
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        # 训练历史
        self.history = {
            'train_loss': [],
            'train_cls_loss': [],
            'train_reg_loss': [],
            'val_loss': [],
            'val_cls_loss': [],
            'val_reg_loss': [],
            'val_accuracy': []
        }
    
    def train_epoch(self, train_loader: DataLoader) -> Tuple[float, float, float]:
        """训练一个epoch"""
        self.model.train()
        
        total_loss = 0.0
        total_cls_loss = 0.0
        total_reg_loss = 0.0
        num_batches = 0
        
        for batch_idx, (x, y_dir, y_reg, y_space) in enumerate(train_loader):
            # 移动到设备
            x = x.to(self.device)
            y_dir = y_dir.to(self.device)
            y_reg = y_reg.to(self.device)
            y_space = y_space.to(self.device)
            
            # 前向传播
            cls_out, reg_out = self.model(x)
            
            # 计算损失
            loss, cls_loss, reg_loss = self.criterion(cls_out, reg_out, y_dir, y_reg, y_space)
            
            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # 累计损失
            total_loss += loss.item()
            total_cls_loss += cls_loss.item()
            total_reg_loss += reg_loss.item()
            num_batches += 1
            
            if (batch_idx + 1) % 50 == 0:
                logger.info(f"Batch {batch_idx+1}/{len(train_loader)}, "
                           f"Loss: {loss.item():.4f}, "
                           f"Cls: {cls_loss.item():.4f}, "
                           f"Reg: {reg_loss.item():.4f}")
        
        avg_loss = total_loss / num_batches
        avg_cls_loss = total_cls_loss / num_batches
        avg_reg_loss = total_reg_loss / num_batches
        
        return avg_loss, avg_cls_loss, avg_reg_loss
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float, float, float]:
        """验证"""
        self.model.eval()
        
        total_loss = 0.0
        total_cls_loss = 0.0
        total_reg_loss = 0.0
        num_batches = 0
        
        correct = 0
        total = 0
        
        with torch.no_grad():
            for x, y_dir, y_reg, y_space in val_loader:
                # 移动到设备
                x = x.to(self.device)
                y_dir = y_dir.to(self.device)
                y_reg = y_reg.to(self.device)
                y_space = y_space.to(self.device)
                
                # 前向传播
                cls_out, reg_out = self.model(x)
                
                # 计算损失
                loss, cls_loss, reg_loss = self.criterion(cls_out, reg_out, y_dir, y_reg, y_space)
                
                # 累计损失
                total_loss += loss.item()
                total_cls_loss += cls_loss.item()
                total_reg_loss += reg_loss.item()
                num_batches += 1
                
                # 计算准确率
                _, predicted = torch.max(cls_out, 1)
                total += y_dir.size(0)
                correct += (predicted == y_dir).sum().item()
        
        avg_loss = total_loss / num_batches
        avg_cls_loss = total_cls_loss / num_batches
        avg_reg_loss = total_reg_loss / num_batches
        accuracy = correct / total
        
        return avg_loss, avg_cls_loss, avg_reg_loss, accuracy
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100,
        early_stopping_patience: int = 15,
        save_dir: Optional[Path] = None
    ) -> Dict:
        """
        完整训练流程
        
        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            epochs: 训练轮数
            early_stopping_patience: 早停耐心值
            save_dir: 模型保存目录
            
        Returns:
            训练历史
        """
        early_stopping = EarlyStopping(patience=early_stopping_patience)
        best_val_loss = float('inf')
        best_epoch = 0
        
        logger.info(f"Starting training for {epochs} epochs...")
        logger.info(f"Device: {self.device}")
        logger.info(f"Learning rate: {self.learning_rate}")
        
        for epoch in range(epochs):
            logger.info(f"\n{'='*60}")
            logger.info(f"Epoch {epoch+1}/{epochs}")
            logger.info(f"{'='*60}")
            
            # 训练
            train_loss, train_cls_loss, train_reg_loss = self.train_epoch(train_loader)
            
            # 验证
            val_loss, val_cls_loss, val_reg_loss, val_accuracy = self.validate(val_loader)
            
            # 更新学习率
            self.scheduler.step(val_loss)
            
            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['train_cls_loss'].append(train_cls_loss)
            self.history['train_reg_loss'].append(train_reg_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_cls_loss'].append(val_cls_loss)
            self.history['val_reg_loss'].append(val_reg_loss)
            self.history['val_accuracy'].append(val_accuracy)
            
            # 打印结果
            logger.info(f"\nTrain Loss: {train_loss:.4f} (Cls: {train_cls_loss:.4f}, Reg: {train_reg_loss:.4f})")
            logger.info(f"Val Loss: {val_loss:.4f} (Cls: {val_cls_loss:.4f}, Reg: {val_reg_loss:.4f})")
            logger.info(f"Val Accuracy: {val_accuracy:.4f}")
            logger.info(f"Learning Rate: {self.optimizer.param_groups[0]['lr']:.6f}")
            
            # 保存最佳模型
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch + 1
                
                if save_dir:
                    self.save_model(save_dir / 'best_model.pt', epoch, val_loss, val_accuracy)
                    logger.info(f"✓ Best model saved (Val Loss: {val_loss:.4f})")
            
            # 早停检查
            if early_stopping(val_loss):
                logger.info(f"\nEarly stopping triggered at epoch {epoch+1}")
                logger.info(f"Best epoch: {best_epoch}, Best val loss: {best_val_loss:.4f}")
                break
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Training completed!")
        logger.info(f"Best epoch: {best_epoch}, Best val loss: {best_val_loss:.4f}")
        logger.info(f"{'='*60}")
        
        # 保存最终模型
        if save_dir:
            self.save_model(save_dir / 'final_model.pt', epochs, val_loss, val_accuracy)
            self.save_history(save_dir / 'training_history.json')
        
        return self.history
    
    def save_model(self, path: Path, epoch: int, val_loss: float, val_accuracy: float):
        """保存模型"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'val_accuracy': val_accuracy,
            'history': self.history
        }, path)
        
        logger.info(f"Model saved to {path}")
    
    def save_history(self, path: Path):
        """保存训练历史"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.history, f, indent=2)
        
        logger.info(f"Training history saved to {path}")
    
    def load_model(self, path: Path):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint.get('history', self.history)
        
        logger.info(f"Model loaded from {path}")
        logger.info(f"Epoch: {checkpoint['epoch']}, Val Loss: {checkpoint['val_loss']:.4f}")
