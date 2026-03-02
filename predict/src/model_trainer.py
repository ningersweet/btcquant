"""
模型训练模块
"""

import logging
import joblib
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split

try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    from sklearn.ensemble import GradientBoostingRegressor

from ..config import config
from .label_generator import compute_sample_weights

logger = logging.getLogger(__name__)


def create_model(params: Dict = None) -> MultiOutputRegressor:
    """
    创建多输出回归模型
    
    Args:
        params: 模型参数
        
    Returns:
        MultiOutputRegressor 实例
    """
    default_params = {
        'n_estimators': config.model.n_estimators,
        'max_depth': config.model.max_depth,
        'learning_rate': config.model.learning_rate,
        'random_state': config.model.random_state,
    }
    
    if params:
        default_params.update(params)
    
    if HAS_LIGHTGBM:
        default_params.update({
            'min_child_samples': config.model.min_child_samples,
            'subsample': config.model.subsample,
            'colsample_bytree': config.model.colsample_bytree,
            'verbose': -1
        })
        base_model = LGBMRegressor(**default_params)
    else:
        base_model = GradientBoostingRegressor(**default_params)
    
    return MultiOutputRegressor(base_model)


class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path or config.service.model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.feature_columns: List[str] = []
        self.target_columns = ["y_rr", "y_sl_pct", "y_tp_pct"]
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_columns: List[str]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            df: 包含特征和标签的 DataFrame
            feature_columns: 特征列名
            
        Returns:
            (X, y, weights)
        """
        df_clean = df.dropna(subset=feature_columns + self.target_columns)
        
        X = df_clean[feature_columns].values
        y = df_clean[self.target_columns].values
        
        if "timestamp" in df_clean.columns:
            weights = compute_sample_weights(df_clean["timestamp"])
        else:
            weights = np.ones(len(df_clean))
        
        self.feature_columns = feature_columns
        return X, y, weights
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray = None,
        val_size: float = 0.1,
        custom_params: Dict = None
    ) -> Dict:
        """
        训练模型
        
        Args:
            X: 特征矩阵
            y: 标签矩阵
            weights: 样本权重
            val_size: 验证集比例
            custom_params: 自定义模型参数（用于超参数优化）
            
        Returns:
            训练指标
        """
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_size, shuffle=False
        )
        
        if weights is not None:
            w_train, _ = train_test_split(
                weights, test_size=val_size, shuffle=False
            )
        else:
            w_train = None
        
        self.model = create_model(custom_params)
        
        if w_train is not None and HAS_LIGHTGBM:
            self.model.fit(X_train, y_train, sample_weight=w_train)
        else:
            self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_val)
        
        metrics = self._compute_metrics(y_val, y_pred)
        
        logger.info(f"Training completed. Metrics: {metrics}")
        return metrics
    
    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """计算评估指标"""
        direction_true = np.sign(y_true[:, 0])
        direction_pred = np.sign(y_pred[:, 0])
        direction_acc = np.mean(direction_true == direction_pred)
        
        mae_rr = np.mean(np.abs(y_true[:, 0] - y_pred[:, 0]))
        mae_sl = np.mean(np.abs(y_true[:, 1] - y_pred[:, 1]))
        mae_tp = np.mean(np.abs(y_true[:, 2] - y_pred[:, 2]))
        
        return {
            "direction_accuracy": round(direction_acc, 4),
            "mae_rr": round(mae_rr, 4),
            "mae_sl": round(mae_sl, 6),
            "mae_tp": round(mae_tp, 6)
        }
    
    def save(self, model_id: str) -> str:
        """保存模型"""
        if self.model is None:
            raise ValueError("No model to save")
        
        model_file = self.model_path / f"{model_id}.joblib"
        
        model_data = {
            "model": self.model,
            "feature_columns": self.feature_columns,
            "target_columns": self.target_columns
        }
        
        joblib.dump(model_data, model_file)
        logger.info(f"Model saved to {model_file}")
        return str(model_file)
    
    def load(self, model_id: str) -> bool:
        """加载模型"""
        model_file = self.model_path / f"{model_id}.joblib"
        
        if not model_file.exists():
            logger.error(f"Model file not found: {model_file}")
            return False
        
        model_data = joblib.load(model_file)
        self.model = model_data["model"]
        self.feature_columns = model_data["feature_columns"]
        self.target_columns = model_data["target_columns"]
        
        logger.info(f"Model loaded from {model_file}")
        return True
