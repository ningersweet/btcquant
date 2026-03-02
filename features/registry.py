"""
特征注册中心

管理所有可用特征，支持按名称动态获取
"""

from typing import Dict, List, Type, Optional

from .base import BaseFeature
from .technical import TECHNICAL_FEATURES
from .structural import STRUCTURAL_FEATURES


class FeatureRegistry:
    """特征注册中心"""
    
    def __init__(self):
        self._features: Dict[str, Type[BaseFeature]] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """注册默认特征"""
        for name, feature_class in TECHNICAL_FEATURES.items():
            self.register(name, feature_class)
        
        for name, feature_class in STRUCTURAL_FEATURES.items():
            self.register(name, feature_class)
    
    def register(self, name: str, feature_class: Type[BaseFeature]) -> None:
        """
        注册特征
        
        Args:
            name: 特征名称
            feature_class: 特征类
        """
        self._features[name] = feature_class
    
    def get(self, name: str) -> Optional[Type[BaseFeature]]:
        """
        获取特征类
        
        Args:
            name: 特征名称
            
        Returns:
            特征类或 None
        """
        return self._features.get(name)
    
    def create(self, name: str, **kwargs) -> Optional[BaseFeature]:
        """
        创建特征实例
        
        Args:
            name: 特征名称
            **kwargs: 特征参数
            
        Returns:
            特征实例或 None
        """
        feature_class = self.get(name)
        if feature_class:
            return feature_class(**kwargs)
        return None
    
    def list_features(self) -> Dict[str, List[str]]:
        """
        列出所有可用特征
        
        Returns:
            按类别分组的特征列表
        """
        technical = list(TECHNICAL_FEATURES.keys())
        structural = list(STRUCTURAL_FEATURES.keys())
        
        return {
            "technical": technical,
            "structural": structural
        }
    
    def get_all_names(self) -> List[str]:
        """获取所有特征名称"""
        return list(self._features.keys())


registry = FeatureRegistry()
