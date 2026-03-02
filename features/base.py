"""
特征基类模块

定义特征计算的统一接口
"""

from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class BaseFeature(ABC):
    """特征基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """特征名称"""
        pass
    
    @property
    @abstractmethod
    def output_columns(self) -> List[str]:
        """输出列名列表"""
        pass
    
    @property
    def required_columns(self) -> List[str]:
        """所需的输入列"""
        return ["open", "high", "low", "close", "volume"]
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算特征
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            包含计算结果的 DataFrame（添加新列）
        """
        pass
    
    def validate_input(self, df: pd.DataFrame) -> bool:
        """验证输入数据"""
        for col in self.required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        return True
