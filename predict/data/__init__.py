"""
数据模块

包含数据加载和标签生成
"""

from .label_generator import LabelGenerator, generate_labels_from_klines

__all__ = [
    'LabelGenerator',
    'generate_labels_from_klines'
]
