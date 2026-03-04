"""
标签生成器

严格按照模型设计.md中的数学公式生成训练标签
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging
from multiprocessing import Pool, cpu_count
from functools import partial

logger = logging.getLogger(__name__)


class LabelGenerator:
    """
    标签生成器
    
    基于未来K线的极值时序，计算有效净利润空间
    """
    
    def __init__(
        self,
        alpha: float = 0.0015,  # 入场缓冲系数
        gamma: float = 0.0040,  # 止盈缓冲系数
        beta: float = 0.0025,   # 止损缓冲系数
        theta_min: float = 0.0100,  # 最小净利阈值
        K: int = 12,  # 预测窗口长度
        n_jobs: int = -1  # 并行核心数，-1表示使用所有核心
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta
        self.theta_min = theta_min
        self.K = K
        self.n_jobs = cpu_count() if n_jobs == -1 else n_jobs
        
        logger.info(f"LabelGenerator initialized with α={alpha}, γ={gamma}, β={beta}, θ_min={theta_min}, K={K}, n_jobs={self.n_jobs}")
    
    def generate_labels(self, df: pd.DataFrame, use_parallel: bool = True) -> pd.DataFrame:
        """
        生成标签
        
        Args:
            df: 包含 ['open', 'high', 'low', 'close', 'volume'] 的DataFrame
            use_parallel: 是否使用多核并行处理
            
        Returns:
            包含标签的DataFrame，新增列：
            - y_dir: 方向 (0=Hold, 1=Long, 2=Short)
            - y_offset: 入场偏移率
            - y_tp_dist: 止盈距离率
            - y_sl_dist: 止损距离率
            - y_space: 空间权重因子
        """
        df = df.copy()
        n = len(df)
        
        # 初始化标签列
        df['y_dir'] = 0
        df['y_offset'] = 0.0
        df['y_tp_dist'] = 0.0
        df['y_sl_dist'] = 0.0
        df['y_space'] = 0.0
        
        total_samples = n - self.K
        logger.info(f"开始处理 {total_samples} 个样本...")
        
        if use_parallel and self.n_jobs > 1 and total_samples > 1000:
            # 使用多核并行处理
            logger.info(f"使用 {self.n_jobs} 个核心并行处理...")
            df = self._generate_labels_parallel(df, n, total_samples)
        else:
            # 单核处理
            if not use_parallel:
                logger.info("使用单核处理...")
            df = self._generate_labels_sequential(df, n, total_samples)
        
        # 统计结果
        long_count = (df['y_dir'] == 1).sum()
        short_count = (df['y_dir'] == 2).sum()
        hold_count = (df['y_dir'] == 0).sum()
        valid_count = long_count + short_count
        
        logger.info(f"Label generation complete: Total={n}, Valid={valid_count}, "
                   f"Long={long_count}, Short={short_count}, Hold={hold_count}")
        logger.info(f"Label distribution: Long={long_count/n*100:.2f}%, "
                   f"Short={short_count/n*100:.2f}%, Hold={hold_count/n*100:.2f}%")
        
        return df
    
    def _generate_labels_sequential(self, df: pd.DataFrame, n: int, total_samples: int) -> pd.DataFrame:
        """单核顺序处理"""
        for i in range(n - self.K):
            # 每处理10%打印进度
            if i > 0 and i % max(1, total_samples // 10) == 0:
                progress = i / total_samples * 100
                logger.info(f"标签生成进度: {progress:.1f}% ({i}/{total_samples})")
            
            result = self._process_single_sample(df, i)
            if result is not None:
                idx, y_dir, y_offset, y_tp_dist, y_sl_dist, y_space = result
                df.loc[df.index[idx], 'y_dir'] = y_dir
                df.loc[df.index[idx], 'y_offset'] = y_offset
                df.loc[df.index[idx], 'y_tp_dist'] = y_tp_dist
                df.loc[df.index[idx], 'y_sl_dist'] = y_sl_dist
                df.loc[df.index[idx], 'y_space'] = y_space
        
        return df
    
    def _generate_labels_parallel(self, df: pd.DataFrame, n: int, total_samples: int) -> pd.DataFrame:
        """多核并行处理"""
        # 准备数据：转换为numpy数组以提高效率
        data_array = df[['open', 'high', 'low', 'close']].values
        
        # 分批处理
        chunk_size = max(100, total_samples // (self.n_jobs * 4))
        indices = list(range(n - self.K))
        
        # 创建处理函数
        process_func = partial(
            _process_batch,
            data_array=data_array,
            K=self.K,
            alpha=self.alpha,
            gamma=self.gamma,
            beta=self.beta,
            theta_min=self.theta_min
        )
        
        # 分批
        batches = [indices[i:i+chunk_size] for i in range(0, len(indices), chunk_size)]
        
        # 并行处理
        results = []
        with Pool(processes=self.n_jobs) as pool:
            for batch_idx, batch_results in enumerate(pool.imap(process_func, batches)):
                results.extend(batch_results)
                progress = (batch_idx + 1) / len(batches) * 100
                if batch_idx % max(1, len(batches) // 10) == 0:
                    logger.info(f"标签生成进度: {progress:.1f}% ({len(results)}/{total_samples})")
        
        # 应用结果
        for result in results:
            if result is not None:
                idx, y_dir, y_offset, y_tp_dist, y_sl_dist, y_space = result
                df.loc[df.index[idx], 'y_dir'] = y_dir
                df.loc[df.index[idx], 'y_offset'] = y_offset
                df.loc[df.index[idx], 'y_tp_dist'] = y_tp_dist
                df.loc[df.index[idx], 'y_sl_dist'] = y_sl_dist
                df.loc[df.index[idx], 'y_space'] = y_space
        
        return df
    
    def _process_single_sample(self, df: pd.DataFrame, i: int) -> Optional[Tuple]:
        """处理单个样本"""
        # 未来窗口
        future_window = df.iloc[i+1:i+1+self.K]
        
        if len(future_window) < self.K:
            return None
        
        # 提取极值
        H_max = future_window['high'].max()
        L_min = future_window['low'].min()
        
        # 获取极值索引（相对于窗口起始）
        idx_high = future_window['high'].idxmax() - future_window.index[0]
        idx_low = future_window['low'].idxmin() - future_window.index[0]
        
        # 基准价格（下一根K线的开盘价）
        P_open = future_window.iloc[0]['open']
        
        # 计算做多和做空场景
        space_long = self._calculate_long_space(L_min, H_max, idx_low, idx_high)
        space_short = self._calculate_short_space(H_max, L_min, idx_high, idx_low)
        
        # 决策逻辑
        if space_long >= self.theta_min and space_long >= space_short:
            # 做多
            P_entry = L_min * (1 + self.alpha)
            P_tp = H_max * (1 - self.gamma)
            P_sl = L_min * (1 - self.beta)
            
            return (
                i, 1,
                (P_entry - P_open) / P_open,
                (P_tp - P_entry) / P_entry,
                (P_entry - P_sl) / P_entry,
                space_long
            )
            
        elif space_short >= self.theta_min and space_short > space_long:
            # 做空
            P_entry = H_max * (1 - self.alpha)
            P_tp = L_min * (1 + self.gamma)
            P_sl = H_max * (1 + self.beta)
            
            return (
                i, 2,
                (P_entry - P_open) / P_open,
                (P_entry - P_tp) / P_entry,
                (P_sl - P_entry) / P_entry,
                space_short
            )
        
        return None
    
    def _calculate_long_space(
        self, 
        L_min: float, 
        H_max: float, 
        idx_low: int, 
        idx_high: int
    ) -> float:
        """
        计算做多场景的有效空间
        
        前提条件：先底后顶 (idx_low < idx_high)
        """
        # 时序检查
        if idx_low >= idx_high:
            return 0.0
        
        # 理论价格
        P_entry = L_min * (1 + self.alpha)
        P_tp = H_max * (1 - self.gamma)
        P_sl = L_min * (1 - self.beta)
        
        # 有效性检查
        if P_tp <= P_entry:
            return 0.0
        
        # 有效空间
        space = (P_tp - P_entry) / P_entry
        return space
    
    def _calculate_short_space(
        self, 
        H_max: float, 
        L_min: float, 
        idx_high: int, 
        idx_low: int
    ) -> float:
        """
        计算做空场景的有效空间
        
        前提条件：先顶后底 (idx_high < idx_low)
        """
        # 时序检查
        if idx_high >= idx_low:
            return 0.0
        
        # 理论价格
        P_entry = H_max * (1 - self.alpha)
        P_tp = L_min * (1 + self.gamma)
        P_sl = H_max * (1 + self.beta)
        
        # 有效性检查
        if P_tp >= P_entry:
            return 0.0
        
        # 有效空间
        space = (P_entry - P_tp) / P_entry
        return space


def generate_labels_from_klines(
    klines: pd.DataFrame,
    alpha: float = 0.0015,
    gamma: float = 0.0040,
    beta: float = 0.0025,
    theta_min: float = 0.0100,
    K: int = 12,
    n_jobs: int = -1
) -> pd.DataFrame:
    """
    便捷函数：从K线数据生成标签
    
    Args:
        klines: K线数据
        alpha: 入场缓冲系数
        gamma: 止盈缓冲系数
        beta: 止损缓冲系数
        theta_min: 最小净利阈值
        K: 预测窗口长度
        n_jobs: 并行核心数，-1表示使用所有核心
        
    Returns:
        带标签的DataFrame
    """
    generator = LabelGenerator(alpha, gamma, beta, theta_min, K, n_jobs)
    return generator.generate_labels(klines)


def _process_batch(indices, data_array, K, alpha, gamma, beta, theta_min):
    """
    批量处理函数（用于多进程）
    
    Args:
        indices: 要处理的索引列表
        data_array: numpy数组 [open, high, low, close]
        K: 预测窗口长度
        alpha, gamma, beta, theta_min: 标签生成参数
    
    Returns:
        结果列表
    """
    results = []
    
    for i in indices:
        # 未来窗口
        future_window = data_array[i+1:i+1+K]
        
        if len(future_window) < K:
            continue
        
        # 提取极值
        H_max = future_window[:, 1].max()  # high
        L_min = future_window[:, 2].min()   # low
        
        # 获取极值索引
        idx_high = future_window[:, 1].argmax()
        idx_low = future_window[:, 2].argmin()
        
        # 基准价格
        P_open = future_window[0, 0]  # open
        
        # 计算做多和做空场景
        space_long = _calculate_long_space(L_min, H_max, idx_low, idx_high, alpha, gamma, beta)
        space_short = _calculate_short_space(H_max, L_min, idx_high, idx_low, alpha, gamma, beta)
        
        # 决策逻辑
        if space_long >= theta_min and space_long >= space_short:
            # 做多
            P_entry = L_min * (1 + alpha)
            P_tp = H_max * (1 - gamma)
            P_sl = L_min * (1 - beta)
            
            results.append((
                i, 1,
                (P_entry - P_open) / P_open,
                (P_tp - P_entry) / P_entry,
                (P_entry - P_sl) / P_entry,
                space_long
            ))
            
        elif space_short >= theta_min and space_short > space_long:
            # 做空
            P_entry = H_max * (1 - alpha)
            P_tp = L_min * (1 + gamma)
            P_sl = H_max * (1 + beta)
            
            results.append((
                i, 2,
                (P_entry - P_open) / P_open,
                (P_entry - P_tp) / P_entry,
                (P_sl - P_entry) / P_entry,
                space_short
            ))
    
    return results


def _calculate_long_space(L_min, H_max, idx_low, idx_high, alpha, gamma, beta):
    """计算做多场景的有效空间"""
    if idx_low >= idx_high:
        return 0.0
    
    P_entry = L_min * (1 + alpha)
    P_tp = H_max * (1 - gamma)
    
    if P_tp <= P_entry:
        return 0.0
    
    return (P_tp - P_entry) / P_entry


def _calculate_short_space(H_max, L_min, idx_high, idx_low, alpha, gamma, beta):
    """计算做空场景的有效空间"""
    if idx_high >= idx_low:
        return 0.0
    
    P_entry = H_max * (1 - alpha)
    P_tp = L_min * (1 + gamma)
    
    if P_tp >= P_entry:
        return 0.0
    
    return (P_entry - P_tp) / P_entry
