"""
推理服务模块
"""

import logging
from dataclasses import dataclass
from typing import Optional
import numpy as np

from ..config import config
from .model_trainer import ModelTrainer

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """预测结果"""
    valid: bool
    signal: str
    rr_score: float
    entry_price: float
    sl_price: float
    tp_price: float
    sl_pct: float
    tp_pct: float
    timestamp: int
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "signal": self.signal,
            "rr_score": round(self.rr_score, 4),
            "entry_price": round(self.entry_price, 2),
            "sl_price": round(self.sl_price, 2),
            "tp_price": round(self.tp_price, 2),
            "sl_pct": round(self.sl_pct, 6),
            "tp_pct": round(self.tp_pct, 6),
            "timestamp": self.timestamp
        }


class InferenceService:
    """推理服务"""
    
    def __init__(self, trainer: ModelTrainer = None):
        self.trainer = trainer or ModelTrainer()
        self.min_rr = config.validation.min_rr
        self.max_sl_pct = config.validation.max_sl_pct
        self.min_sl_pct = config.validation.min_sl_pct
    
    def predict(
        self,
        features: np.ndarray,
        current_price: float,
        timestamp: int
    ) -> PredictionResult:
        """
        执行预测
        
        Args:
            features: 特征向量
            current_price: 当前价格
            timestamp: 时间戳
            
        Returns:
            预测结果
        """
        if self.trainer.model is None:
            return self._invalid_result(current_price, timestamp, "Model not loaded")
        
        raw_output = self.trainer.model.predict(features.reshape(1, -1))[0]
        
        return self.post_process(raw_output, current_price, timestamp)
    
    def post_process(
        self,
        raw_output: np.ndarray,
        current_price: float,
        timestamp: int
    ) -> PredictionResult:
        """
        后处理校验
        
        Args:
            raw_output: 模型原始输出 [rr, sl_pct, tp_pct]
            current_price: 当前价格
            timestamp: 时间戳
            
        Returns:
            校验后的预测结果
        """
        rr_score = raw_output[0]
        sl_pct = abs(raw_output[1])
        tp_pct = abs(raw_output[2])
        
        if rr_score > 0:
            signal = "LONG"
            sl_price = current_price * (1 - sl_pct)
            tp_price = current_price * (1 + tp_pct)
        else:
            signal = "SHORT"
            sl_price = current_price * (1 + sl_pct)
            tp_price = current_price * (1 - tp_pct)
        
        valid = self._validate(
            rr_score, sl_pct, tp_pct,
            current_price, sl_price, tp_price, signal
        )
        
        if not valid:
            signal = "NONE"
        
        return PredictionResult(
            valid=valid,
            signal=signal,
            rr_score=abs(rr_score),
            entry_price=current_price,
            sl_price=sl_price,
            tp_price=tp_price,
            sl_pct=sl_pct,
            tp_pct=tp_pct,
            timestamp=timestamp
        )
    
    def _validate(
        self,
        rr_score: float,
        sl_pct: float,
        tp_pct: float,
        current_price: float,
        sl_price: float,
        tp_price: float,
        signal: str
    ) -> bool:
        """校验预测结果"""
        if abs(rr_score) < self.min_rr:
            logger.debug(f"RR {rr_score} below threshold {self.min_rr}")
            return False
        
        if sl_pct < self.min_sl_pct or sl_pct > self.max_sl_pct:
            logger.debug(f"SL pct {sl_pct} out of range [{self.min_sl_pct}, {self.max_sl_pct}]")
            return False
        
        if signal == "LONG":
            if not (sl_price < current_price < tp_price):
                logger.debug(f"Invalid LONG prices: SL={sl_price}, Entry={current_price}, TP={tp_price}")
                return False
        else:
            if not (tp_price < current_price < sl_price):
                logger.debug(f"Invalid SHORT prices: TP={tp_price}, Entry={current_price}, SL={sl_price}")
                return False
        
        return True
    
    def _invalid_result(
        self,
        current_price: float,
        timestamp: int,
        reason: str
    ) -> PredictionResult:
        """返回无效结果"""
        logger.warning(f"Invalid prediction: {reason}")
        return PredictionResult(
            valid=False,
            signal="NONE",
            rr_score=0.0,
            entry_price=current_price,
            sl_price=current_price,
            tp_price=current_price,
            sl_pct=0.0,
            tp_pct=0.0,
            timestamp=timestamp
        )
