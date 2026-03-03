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
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, f1_score

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
        
        只 drop 目标列为 NaN 的行，保留特征中的 NaN 让 LightGBM 原生处理。
        
        Args:
            df: 包含特征和标签的 DataFrame
            feature_columns: 特征列名
            
        Returns:
            (X, y, weights)
        """
        df_clean = df.dropna(subset=self.target_columns)
        
        X = df_clean[feature_columns].values.astype(np.float64)
        y = df_clean[self.target_columns].values
        
        if "timestamp" in df_clean.columns:
            weights = compute_sample_weights(df_clean["timestamp"])
        else:
            weights = np.ones(len(df_clean))
        
        nan_feature_ratio = np.isnan(X).mean()
        if nan_feature_ratio > 0:
            logger.info(f"Feature NaN ratio: {nan_feature_ratio:.4f} (handled by LightGBM natively)")
        
        self.feature_columns = feature_columns
        return X, y, weights
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray = None,
        val_size: float = 0.1,
        custom_params: Dict = None,
        n_cv_splits: int = 5
    ) -> Dict:
        """
        训练模型（含时间序列交叉验证）
        
        流程：
        1. TimeSeriesSplit 交叉验证，获取鲁棒的性能估计
        2. 用最后一段做验证集训练最终模型
        
        Args:
            X: 特征矩阵
            y: 标签矩阵
            weights: 样本权重
            val_size: 验证集比例（用于最终模型训练）
            custom_params: 自定义模型参数（用于超参数优化）
            n_cv_splits: 交叉验证折数
            
        Returns:
            训练指标（含 CV 和最终评估）
        """
        cv_summary = None
        min_samples_for_cv = n_cv_splits * 200
        
        if len(X) >= min_samples_for_cv and n_cv_splits > 1:
            tscv = TimeSeriesSplit(n_splits=n_cv_splits)
            cv_metrics_list = []
            
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
                fold_model = create_model(custom_params)
                
                X_fold_train, y_fold_train = X[train_idx], y[train_idx]
                X_fold_val, y_fold_val = X[val_idx], y[val_idx]
                
                if weights is not None and HAS_LIGHTGBM:
                    fold_model.fit(X_fold_train, y_fold_train, sample_weight=weights[train_idx])
                else:
                    fold_model.fit(X_fold_train, y_fold_train)
                
                y_fold_pred = fold_model.predict(X_fold_val)
                fold_metrics = self._compute_metrics(y_fold_val, y_fold_pred)
                cv_metrics_list.append(fold_metrics)
                
                logger.info(
                    f"CV Fold {fold+1}/{n_cv_splits}: "
                    f"dir_acc={fold_metrics['direction_accuracy']:.4f}, "
                    f"dir_f1={fold_metrics['direction_f1']:.4f}, "
                    f"mae_rr={fold_metrics['mae_rr']:.4f}, "
                    f"train={len(train_idx)}, val={len(val_idx)}"
                )
            
            cv_summary = self._aggregate_cv_metrics(cv_metrics_list)
            logger.info(
                f"CV Summary: dir_acc={cv_summary['direction_accuracy']['mean']:.4f}"
                f"±{cv_summary['direction_accuracy']['std']:.4f}, "
                f"mae_rr={cv_summary['mae_rr']['mean']:.4f}"
                f"±{cv_summary['mae_rr']['std']:.4f}"
            )
        else:
            logger.info(f"Skipping CV: {len(X)} samples < {min_samples_for_cv} minimum")
        
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
        final_metrics = self._compute_metrics(y_val, y_pred)
        
        result = {**final_metrics}
        if cv_summary:
            result["cv"] = cv_summary
        
        logger.info(f"Training completed. Final eval: {final_metrics}")
        return result
    
    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """
        计算评估指标
        
        包含方向分类指标（accuracy/precision/recall/F1）和回归指标（MAE/RMSE）
        """
        direction_true = np.sign(y_true[:, 0])
        direction_pred = np.sign(y_pred[:, 0])
        
        direction_acc = np.mean(direction_true == direction_pred)
        
        valid_mask = (direction_true != 0) & (direction_pred != 0)
        if valid_mask.sum() > 0:
            dir_true_bin = (direction_true[valid_mask] > 0).astype(int)
            dir_pred_bin = (direction_pred[valid_mask] > 0).astype(int)
            dir_precision = precision_score(dir_true_bin, dir_pred_bin, zero_division=0)
            dir_recall = recall_score(dir_true_bin, dir_pred_bin, zero_division=0)
            dir_f1 = f1_score(dir_true_bin, dir_pred_bin, zero_division=0)
        else:
            dir_precision = dir_recall = dir_f1 = 0.0
        
        mae_rr = np.mean(np.abs(y_true[:, 0] - y_pred[:, 0]))
        rmse_rr = np.sqrt(np.mean((y_true[:, 0] - y_pred[:, 0]) ** 2))
        mae_sl = np.mean(np.abs(y_true[:, 1] - y_pred[:, 1]))
        mae_tp = np.mean(np.abs(y_true[:, 2] - y_pred[:, 2]))
        
        return {
            "direction_accuracy": round(direction_acc, 4),
            "direction_precision": round(dir_precision, 4),
            "direction_recall": round(dir_recall, 4),
            "direction_f1": round(dir_f1, 4),
            "mae_rr": round(mae_rr, 4),
            "rmse_rr": round(rmse_rr, 4),
            "mae_sl": round(mae_sl, 6),
            "mae_tp": round(mae_tp, 6)
        }
    
    def _aggregate_cv_metrics(self, cv_metrics_list: List[Dict]) -> Dict:
        """聚合交叉验证各折的指标，计算均值和标准差"""
        summary = {"n_splits": len(cv_metrics_list)}
        
        for key in cv_metrics_list[0]:
            values = [m[key] for m in cv_metrics_list]
            summary[key] = {
                "mean": round(float(np.mean(values)), 4),
                "std": round(float(np.std(values)), 4),
                "min": round(float(np.min(values)), 4),
                "max": round(float(np.max(values)), 4),
            }
        
        summary["fold_metrics"] = cv_metrics_list
        return summary
    
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
