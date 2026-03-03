"""
TCN (时间卷积网络) 模型架构

基于残差空洞卷积的时序预测模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List


class CausalConv1d(nn.Module):
    """
    因果卷积层
    
    确保时间步 t 的输出只依赖于 t 及之前的输入
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int = 1,
        **kwargs
    ):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            padding=self.padding,
            dilation=dilation,
            **kwargs
        )
    
    def forward(self, x):
        # x shape: (batch, channels, seq_len)
        out = self.conv(x)
        # 移除右侧填充，保持因果性
        if self.padding > 0:
            out = out[:, :, :-self.padding]
        return out


class ResidualBlock(nn.Module):
    """
    残差空洞卷积块
    
    包含两层卷积 + 残差连接
    """
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int,
        dropout: float = 0.2
    ):
        super().__init__()
        
        # 第一层卷积
        self.conv1 = CausalConv1d(
            in_channels,
            out_channels,
            kernel_size,
            dilation=dilation
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.dropout1 = nn.Dropout(dropout)
        
        # 第二层卷积
        self.conv2 = CausalConv1d(
            out_channels,
            out_channels,
            kernel_size,
            dilation=dilation
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.dropout2 = nn.Dropout(dropout)
        
        # 残差连接（如果输入输出通道数不同，需要1x1卷积调整）
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None
        
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # x shape: (batch, in_channels, seq_len)
        residual = x
        
        # 第一层
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.dropout1(out)
        
        # 第二层
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.dropout2(out)
        
        # 残差连接
        if self.downsample is not None:
            residual = self.downsample(residual)
        
        out = out + residual
        out = self.relu(out)
        
        return out


class TCNModel(nn.Module):
    """
    TCN模型
    
    输入: (batch, seq_len, features)
    输出: 
        - cls_out: (batch, 3) - 分类概率 [Hold, Long, Short]
        - reg_out: (batch, 3) - 回归输出 [offset, tp_dist, sl_dist]
    """
    
    def __init__(
        self,
        input_dim: int = 5,
        channels: int = 64,
        num_layers: int = 8,
        kernel_size: int = 3,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.channels = channels
        self.num_layers = num_layers
        
        # 输入升维：5 -> 64
        self.input_conv = nn.Conv1d(input_dim, channels, kernel_size=1)
        
        # 堆叠残差块
        layers = []
        for i in range(num_layers):
            dilation = 2 ** i  # 膨胀率: 1, 2, 4, 8, 16, 32, 64, 128
            layers.append(
                ResidualBlock(
                    in_channels=channels,
                    out_channels=channels,
                    kernel_size=kernel_size,
                    dilation=dilation,
                    dropout=dropout
                )
            )
        self.tcn_layers = nn.ModuleList(layers)
        
        # 全局平均池化
        self.gap = nn.AdaptiveAvgPool1d(1)
        
        # 分类头
        self.cls_fc1 = nn.Linear(channels, channels)
        self.cls_fc2 = nn.Linear(channels, 3)
        
        # 回归头
        self.reg_fc1 = nn.Linear(channels, channels)
        self.reg_fc2 = nn.Linear(channels, 3)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        
        # 计算感受野
        receptive_field = 1 + sum((kernel_size - 1) * (2 ** i) for i in range(num_layers))
        print(f"TCN Model initialized: {num_layers} layers, receptive field = {receptive_field}")
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: (batch, seq_len, features)
            
        Returns:
            cls_out: (batch, 3) - 分类logits
            reg_out: (batch, 3) - 回归输出
        """
        # 转换维度: (batch, seq_len, features) -> (batch, features, seq_len)
        x = x.transpose(1, 2)
        
        # 输入升维
        x = self.input_conv(x)
        
        # TCN层
        for layer in self.tcn_layers:
            x = layer(x)
        
        # 全局平均池化: (batch, channels, seq_len) -> (batch, channels, 1)
        x = self.gap(x)
        # (batch, channels, 1) -> (batch, channels)
        x = x.squeeze(-1)
        
        # 分类头
        cls = self.relu(self.cls_fc1(x))
        cls = self.dropout(cls)
        cls_out = self.cls_fc2(cls)  # (batch, 3)
        
        # 回归头
        reg = self.relu(self.reg_fc1(x))
        reg = self.dropout(reg)
        reg_out = self.reg_fc2(reg)  # (batch, 3)
        
        return cls_out, reg_out


class TCNLoss(nn.Module):
    """
    TCN模型的组合损失函数
    
    L_total = λ_cls * L_cls + λ_reg * L_reg
    """
    
    def __init__(
        self,
        lambda_cls: float = 1.0,
        lambda_reg: float = 0.5,
        theta_min: float = 0.01
    ):
        super().__init__()
        self.lambda_cls = lambda_cls
        self.lambda_reg = lambda_reg
        self.theta_min = theta_min
        
        self.ce_loss = nn.CrossEntropyLoss()
        self.huber_loss = nn.SmoothL1Loss(reduction='none')  # Huber loss
    
    def forward(
        self,
        cls_out: torch.Tensor,
        reg_out: torch.Tensor,
        y_dir: torch.Tensor,
        y_reg: torch.Tensor,
        y_space: torch.Tensor
    ):
        """
        计算损失
        
        Args:
            cls_out: (batch, 3) - 分类logits
            reg_out: (batch, 3) - 回归输出
            y_dir: (batch,) - 方向标签 [0, 1, 2]
            y_reg: (batch, 3) - 回归标签 [offset, tp_dist, sl_dist]
            y_space: (batch,) - 空间权重
            
        Returns:
            total_loss, cls_loss, reg_loss
        """
        # 分类损失
        cls_loss = self.ce_loss(cls_out, y_dir)
        
        # 回归损失（仅对非Hold样本计算）
        mask = (y_dir != 0).float()  # (batch,)
        
        if mask.sum() > 0:
            # 计算Huber损失
            huber = self.huber_loss(reg_out, y_reg)  # (batch, 3)
            huber = huber.mean(dim=1)  # (batch,)
            
            # 动态权重
            w_space = 1.0 + y_space / self.theta_min  # (batch,)
            
            # 加权回归损失
            weighted_huber = huber * w_space * mask
            reg_loss = weighted_huber.sum() / mask.sum()
        else:
            reg_loss = torch.tensor(0.0, device=cls_out.device)
        
        # 总损失
        total_loss = self.lambda_cls * cls_loss + self.lambda_reg * reg_loss
        
        return total_loss, cls_loss, reg_loss


def create_tcn_model(
    input_dim: int = 5,
    channels: int = 64,
    num_layers: int = 8,
    kernel_size: int = 3,
    dropout: float = 0.2
) -> TCNModel:
    """创建TCN模型"""
    return TCNModel(input_dim, channels, num_layers, kernel_size, dropout)
