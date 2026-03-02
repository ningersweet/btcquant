"""
超参数优化模块

使用 Optuna 进行自动超参数搜索
"""

import logging
from typing import Dict, Tuple
import numpy as np
import optuna
from optuna.trial import Trial
from sklearn.multioutput import MultiOutputRegressor
from lightgbm import LGBMRegressor

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """超参数优化器"""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.best_params = None
        self.best_score = None
        self.study = None
    
    def optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        weights_train: np.ndarray = None,
        n_trials: int = 50,
        timeout: int = 3600
    ) -> Dict:
        """
        执行超参数优化
        
        Args:
            X_train: 训练特征
            y_train: 训练标签
            X_val: 验证特征
            y_val: 验证标签
            weights_train: 训练样本权重
            n_trials: 优化次数
            timeout: 超时时间（秒）
            
        Returns:
            最佳参数和评估指标
        """
        logger.info(f"Starting hyperparameter optimization: {n_trials} trials, timeout={timeout}s")
        
        def objective(trial: Trial) -> float:
            """优化目标函数"""
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=50),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'min_child_samples': trial.suggest_int('min_child_samples', 20, 100, step=10),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
                'random_state': self.random_state,
                'verbose': -1,
                'n_jobs': 1
            }
            
            # 创建模型
            base_model = LGBMRegressor(**params)
            model = MultiOutputRegressor(base_model)
            
            # 训练
            if weights_train is not None:
                model.fit(X_train, y_train, sample_weight=weights_train)
            else:
                model.fit(X_train, y_train)
            
            # 预测
            y_pred = model.predict(X_val)
            
            # 计算评估指标
            metrics = self._compute_metrics(y_val, y_pred)
            
            # 优化目标：最大化方向准确率，同时最小化 MAE
            # 使用加权组合
            direction_acc = metrics['direction_accuracy']
            mae_rr = metrics['mae_rr']
            
            # 归一化 MAE（假设合理范围是 0-100）
            normalized_mae = min(mae_rr / 100.0, 1.0)
            
            # 综合得分：70% 方向准确率 + 30% (1 - normalized_mae)
            score = 0.7 * direction_acc + 0.3 * (1 - normalized_mae)
            
            # 记录中间结果
            trial.set_user_attr('direction_accuracy', direction_acc)
            trial.set_user_attr('mae_rr', mae_rr)
            trial.set_user_attr('mae_sl', metrics['mae_sl'])
            trial.set_user_attr('mae_tp', metrics['mae_tp'])
            
            return score
        
        # 创建 Optuna study
        self.study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=self.random_state)
        )
        
        # 执行优化
        self.study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True
        )
        
        # 获取最佳参数
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value
        
        # 获取最佳 trial 的详细指标
        best_trial = self.study.best_trial
        best_metrics = {
            'direction_accuracy': best_trial.user_attrs['direction_accuracy'],
            'mae_rr': best_trial.user_attrs['mae_rr'],
            'mae_sl': best_trial.user_attrs['mae_sl'],
            'mae_tp': best_trial.user_attrs['mae_tp']
        }
        
        logger.info(f"Optimization completed. Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        logger.info(f"Best metrics: {best_metrics}")
        
        return {
            'best_params': self.best_params,
            'best_score': round(self.best_score, 4),
            'best_metrics': best_metrics,
            'n_trials': len(self.study.trials),
            'best_trial_number': best_trial.number
        }
    
    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """计算评估指标"""
        direction_true = np.sign(y_true[:, 0])
        direction_pred = np.sign(y_pred[:, 0])
        direction_acc = np.mean(direction_true == direction_pred)
        
        mae_rr = np.mean(np.abs(y_true[:, 0] - y_pred[:, 0]))
        mae_sl = np.mean(np.abs(y_true[:, 1] - y_pred[:, 1]))
        mae_tp = np.mean(np.abs(y_true[:, 2] - y_pred[:, 2]))
        
        return {
            "direction_accuracy": direction_acc,
            "mae_rr": mae_rr,
            "mae_sl": mae_sl,
            "mae_tp": mae_tp
        }
    
    def get_optimization_history(self) -> Dict:
        """获取优化历史"""
        if self.study is None:
            return {}
        
        trials_data = []
        for trial in self.study.trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                trials_data.append({
                    'number': trial.number,
                    'score': trial.value,
                    'params': trial.params,
                    'direction_accuracy': trial.user_attrs.get('direction_accuracy', 0),
                    'mae_rr': trial.user_attrs.get('mae_rr', 0)
                })
        
        return {
            'trials': trials_data,
            'best_trial': self.study.best_trial.number,
            'best_score': self.best_score
        }
