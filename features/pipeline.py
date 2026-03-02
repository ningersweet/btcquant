"""
特征流水线模块

批量计算特征，支持缓存
"""

import logging
from typing import List, Optional
import pandas as pd

from .base import BaseFeature
from .registry import registry

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """特征计算流水线"""
    
    def __init__(self, feature_names: Optional[List[str]] = None):
        """
        初始化流水线
        
        Args:
            feature_names: 要计算的特征名称列表，None 表示全部
        """
        self.feature_names = feature_names or registry.get_all_names()
        self.features: List[BaseFeature] = []
        self._init_features()
    
    def _init_features(self) -> None:
        """初始化特征实例"""
        for name in self.feature_names:
            feature = registry.create(name)
            if feature:
                self.features.append(feature)
            else:
                logger.warning(f"Unknown feature: {name}")
    
    def compute(self, df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
        """
        计算所有特征
        
        Args:
            df: 输入数据 (OHLCV)
            drop_na: 是否删除包含 NaN 的行
            
        Returns:
            包含所有特征的 DataFrame
        """
        result = df.copy()
        
        for feature in self.features:
            try:
                result = feature.compute(result)
                logger.debug(f"Computed feature: {feature.name}")
            except Exception as e:
                logger.error(f"Failed to compute feature {feature.name}: {e}")
        
        if drop_na:
            result = result.dropna()
        
        return result
    
    def get_feature_columns(self) -> List[str]:
        """获取所有特征列名"""
        columns = []
        for feature in self.features:
            columns.extend(feature.output_columns)
        return columns
    
    def compute_single(self, df: pd.DataFrame, feature_name: str) -> pd.DataFrame:
        """
        计算单个特征
        
        Args:
            df: 输入数据
            feature_name: 特征名称
            
        Returns:
            包含该特征的 DataFrame
        """
        feature = registry.create(feature_name)
        if feature:
            return feature.compute(df)
        raise ValueError(f"Unknown feature: {feature_name}")


def compute_features(
    df: pd.DataFrame,
    feature_names: Optional[List[str]] = None,
    drop_na: bool = True
) -> pd.DataFrame:
    """
    便捷函数：计算特征
    
    Args:
        df: 输入数据
        feature_names: 特征名称列表
        drop_na: 是否删除 NaN
        
    Returns:
        包含特征的 DataFrame
    """
    pipeline = FeaturePipeline(feature_names)
    return pipeline.compute(df, drop_na)


def get_feature_columns(feature_names: Optional[List[str]] = None) -> List[str]:
    """
    获取特征列名
    
    Args:
        feature_names: 特征名称列表
        
    Returns:
        特征列名列表
    """
    pipeline = FeaturePipeline(feature_names)
    return pipeline.get_feature_columns()
