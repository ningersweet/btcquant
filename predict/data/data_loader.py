"""
数据加载器

支持滚动窗口和Z-Score标准化
"""

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """
    时间序列数据集
    
    支持滑动窗口和标签对齐
    """
    
    def __init__(
        self,
        data: np.ndarray,
        labels: pd.DataFrame,
        window_size: int = 288,
        normalize: bool = True
    ):
        """
        Args:
            data: (N, features) - 原始OHLCV数据
            labels: DataFrame包含 ['y_dir', 'y_offset', 'y_tp_dist', 'y_sl_dist', 'y_space']
            window_size: 输入窗口大小
            normalize: 是否进行滚动Z-Score标准化
        """
        self.data = data
        self.labels = labels
        self.window_size = window_size
        self.normalize = normalize
        
        # 计算有效样本数（需要足够的历史数据）
        self.valid_indices = []
        for i in range(window_size, len(data)):
            # 检查标签是否有效（至少不是最后K个样本）
            if i < len(labels):
                self.valid_indices.append(i)
        
        logger.info(f"Dataset created: {len(self.valid_indices)} valid samples from {len(data)} total")
    
    def __len__(self):
        return len(self.valid_indices)
    
    def __getitem__(self, idx) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        获取一个样本
        
        Returns:
            x: (window_size, features) - 输入序列
            y_dir: (,) - 方向标签
            y_reg: (3,) - 回归标签
            y_space: (,) - 空间权重
        """
        actual_idx = self.valid_indices[idx]
        
        # 提取窗口数据
        start_idx = actual_idx - self.window_size
        end_idx = actual_idx
        x = self.data[start_idx:end_idx].copy()
        
        # 滚动Z-Score标准化
        if self.normalize:
            x = self._rolling_zscore(x)
        
        # 提取标签
        label_row = self.labels.iloc[actual_idx]
        y_dir = int(label_row['y_dir'])
        y_offset = float(label_row['y_offset'])
        y_tp_dist = float(label_row['y_tp_dist'])
        y_sl_dist = float(label_row['y_sl_dist'])
        y_space = float(label_row['y_space'])
        
        # 转换为tensor
        x_tensor = torch.FloatTensor(x)
        y_dir_tensor = torch.LongTensor([y_dir])[0]
        y_reg_tensor = torch.FloatTensor([y_offset, y_tp_dist, y_sl_dist])
        y_space_tensor = torch.FloatTensor([y_space])[0]
        
        return x_tensor, y_dir_tensor, y_reg_tensor, y_space_tensor
    
    def _rolling_zscore(self, x: np.ndarray) -> np.ndarray:
        """
        滚动Z-Score标准化
        
        Args:
            x: (window_size, features)
            
        Returns:
            标准化后的数据
        """
        mean = x.mean(axis=0, keepdims=True)
        std = x.std(axis=0, keepdims=True) + 1e-8
        return (x - mean) / std


def split_data(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    按时间顺序划分数据集
    
    Args:
        df: 完整数据
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        test_ratio: 测试集比例
        
    Returns:
        train_df, val_df, test_df
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例之和必须为1"
    
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()
    
    logger.info(f"Data split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    return train_df, val_df, test_df


def create_dataloaders(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    window_size: int = 288,
    batch_size: int = 128,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    创建数据加载器
    
    Args:
        train_df: 训练数据（包含OHLCV和标签）
        val_df: 验证数据
        test_df: 测试数据
        window_size: 窗口大小
        batch_size: 批次大小
        num_workers: 工作进程数
        
    Returns:
        train_loader, val_loader, test_loader
    """
    # 提取特征列
    feature_cols = ['open', 'high', 'low', 'close', 'volume']
    label_cols = ['y_dir', 'y_offset', 'y_tp_dist', 'y_sl_dist', 'y_space']
    
    # 创建数据集
    train_data = train_df[feature_cols].values
    train_labels = train_df[label_cols]
    train_dataset = TimeSeriesDataset(train_data, train_labels, window_size, normalize=True)
    
    val_data = val_df[feature_cols].values
    val_labels = val_df[label_cols]
    val_dataset = TimeSeriesDataset(val_data, val_labels, window_size, normalize=True)
    
    test_data = test_df[feature_cols].values
    test_labels = test_df[label_cols]
    test_dataset = TimeSeriesDataset(test_data, test_labels, window_size, normalize=True)
    
    # 创建数据加载器
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,  # 使用4个工作进程
        pin_memory=True  # 启用pin_memory加速GPU传输
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    logger.info(f"DataLoaders created: Train batches={len(train_loader)}, "
               f"Val batches={len(val_loader)}, Test batches={len(test_loader)}")
    
    return train_loader, val_loader, test_loader


def normalize_inference_data(data: np.ndarray) -> np.ndarray:
    """
    推理时的数据标准化
    
    Args:
        data: (window_size, features) - 最近的window_size根K线
        
    Returns:
        标准化后的数据
    """
    mean = data.mean(axis=0, keepdims=True)
    std = data.std(axis=0, keepdims=True) + 1e-8
    return (data - mean) / std
