"""
标签生成器

严格按照模型设计.md中的数学公式生成训练标签
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

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
        K: int = 12  # 预测窗口长度
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta
        self.theta_min = theta_min
        self.K = K
        
        logger.info(f"LabelGenerator initialized with α={alpha}, γ={gamma}, β={beta}, θ_min={theta_min}, K={K}")
    
    def generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成标签（优化版：支持进度显示和多核处理）
        
        Args:
            df: 包含 ['open', 'high', 'low', 'close', 'volume'] 的DataFrame
            
        Returns:
            包含标签的DataFrame，新增列：
            - y_dir: 方向 (0=Hold, 1=Long, 2=Short)
            - y_offset: 入场偏移率
            - y_tp_dist: 止盈距离率
            - y_sl_dist: 止损距离率
            - y_space: 空间权重因子
        """
        from tqdm import tqdm
        import multiprocessing as mp
        from functools import partial
        
        df = df.copy()
        n = len(df)
        
        logger.info(f"开始生成标签，总样本数: {n}, 预测窗口: {self.K}")
        
        # 初始化标签列
        df['y_dir'] = 0
        df['y_offset'] = 0.0
        df['y_tp_dist'] = 0.0
        df['y_sl_dist'] = 0.0
        df['y_space'] = 0.0
        
        # 准备数据用于并行处理
        high_values = df['high'].values
        low_values = df['low'].values
        open_values = df['open'].values
        
        # 使用多进程处理
        num_workers = min(4, mp.cpu_count())
        logger.info(f"使用 {num_workers} 个进程并行处理")
        
        # 分块处理
        chunk_size = max(1000, (n - self.K) // (num_workers * 10))
        indices = list(range(n - self.K))
        
        # 创建处理函数
        def process_chunk(idx_list):
            results = []
            for i in idx_list:
                # 未来窗口
                future_high = high_values[i+1:i+1+self.K]
                future_low = low_values[i+1:i+1+self.K]
                future_open = open_values[i+1]
                
                if len(future_high) < self.K:
                    continue
                
                # 提取极值
                H_max = future_high.max()
                L_min = future_low.min()
                
                # 获取极值索引
                idx_high = np.argmax(future_high)
                idx_low = np.argmin(future_low)
                
                # 计算做多和做空场景
                space_long = self._calculate_long_space(L_min, H_max, idx_low, idx_high)
                space_short = self._calculate_short_space(H_max, L_min, idx_high, idx_low)
                
                # 决策逻辑
                if space_long >= self.theta_min and space_long >= space_short:
                    # 做多
                    P_entry = L_min * (1 + self.alpha)
                    P_tp = H_max * (1 - self.gamma)
                    P_sl = L_min * (1 - self.beta)
                    
                    results.append((i, 1, 
                                  (P_entry - future_open) / future_open,
                                  (P_tp - P_entry) / P_entry,
                                  (P_entry - P_sl) / P_entry,
                                  space_long))
                    
                elif space_short >= self.theta_min and space_short > space_long:
                    # 做空
                    P_entry = H_max * (1 - self.alpha)
                    P_tp = L_min * (1 + self.gamma)
                    P_sl = H_max * (1 + self.beta)
                    
                    results.append((i, 2,
                                  (P_entry - future_open) / future_open,
                                  (P_entry - P_tp) / P_entry,
                                  (P_sl - P_entry) / P_entry,
                                  space_short))
                else:
                    # 持有
                    results.append((i, 0, 0.0, 0.0, 0.0, 0.0))
            
            return results
        
        # 使用进度条的并行处理
        with mp.Pool(num_workers) as pool:
            chunks = [indices[i:i+chunk_size] for i in range(0, len(indices), chunk_size)]
            results = []
            
            with tqdm(total=len(chunks), desc="生成标签", unit="chunk") as pbar:
                for chunk_results in pool.imap(process_chunk, chunks):
                    results.extend(chunk_results)
                    pbar.update(1)
        
        # 应用结果
        valid_count = 0
        long_count = 0
        short_count = 0
        hold_count = 0
        
        for i, y_dir, y_offset, y_tp_dist, y_sl_dist, y_space in results:
            df.loc[df.index[i], 'y_dir'] = y_dir
            df.loc[df.index[i], 'y_offset'] = y_offset
            df.loc[df.index[i], 'y_tp_dist'] = y_tp_dist
            df.loc[df.index[i], 'y_sl_dist'] = y_sl_dist
            df.loc[df.index[i], 'y_space'] = y_space
            
            valid_count += 1
            if y_dir == 1:
                long_count += 1
            elif y_dir == 2:
                short_count += 1
            else:
                hold_count += 1
                df.loc[df.index[i], 'y_sl_dist'] = (P_entry - P_sl) / P_entry
                df.loc[df.index[i], 'y_space'] = space_long
                
                long_count += 1
                valid_count += 1
                
            elif space_short >= self.theta_min and space_short > space_long:
                # 做空
                df.loc[df.index[i], 'y_dir'] = 2
                P_entry = H_max * (1 - self.alpha)
                P_tp = L_min * (1 + self.gamma)
                P_sl = H_max * (1 + self.beta)
                
                df.loc[df.index[i], 'y_offset'] = (P_entry - P_open) / P_open
                df.loc[df.index[i], 'y_tp_dist'] = (P_entry - P_tp) / P_entry
                df.loc[df.index[i], 'y_sl_dist'] = (P_sl - P_entry) / P_entry
                df.loc[df.index[i], 'y_space'] = space_short
                
                short_count += 1
                valid_count += 1
                
            else:
                # 持有
                hold_count += 1
        
        logger.info(f"Label generation complete: Total={n}, Valid={valid_count}, "
                   f"Long={long_count}, Short={short_count}, Hold={hold_count}")
        logger.info(f"Label distribution: Long={long_count/n*100:.2f}%, "
                   f"Short={short_count/n*100:.2f}%, Hold={hold_count/n*100:.2f}%")
        
        return df
    
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
    K: int = 12
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
        
    Returns:
        带标签的DataFrame
    """
    generator = LabelGenerator(alpha, gamma, beta, theta_min, K)
    return generator.generate_labels(klines)
