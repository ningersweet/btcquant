"""
技术指标特征模块

包含 EMA, RSI, MACD, ATR, BB, OBV 等技术指标
"""

import pandas as pd
import numpy as np
from typing import List

from .base import BaseFeature
from .config import config


class EMAFeature(BaseFeature):
    """指数移动平均特征"""
    
    def __init__(self, periods: tuple = None):
        self.periods = periods or config.feature.ema_periods
    
    @property
    def name(self) -> str:
        return "ema"
    
    @property
    def output_columns(self) -> List[str]:
        return [f"ema_{p}" for p in self.periods]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        for period in self.periods:
            ema = df["close"].ewm(span=period, adjust=False).mean()
            result[f"ema_{period}"] = (ema - df["close"]) / df["close"]
        
        return result


class RSIFeature(BaseFeature):
    """相对强弱指数特征"""
    
    def __init__(self, period: int = None):
        self.period = period or config.feature.rsi_period
    
    @property
    def name(self) -> str:
        return "rsi"
    
    @property
    def output_columns(self) -> List[str]:
        return [f"rsi_{self.period}"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        result[f"rsi_{self.period}"] = rsi / 100
        
        return result


class MACDFeature(BaseFeature):
    """MACD 指标特征"""
    
    def __init__(self, fast: int = None, slow: int = None, signal: int = None):
        self.fast = fast or config.feature.macd_fast
        self.slow = slow or config.feature.macd_slow
        self.signal = signal or config.feature.macd_signal
    
    @property
    def name(self) -> str:
        return "macd"
    
    @property
    def output_columns(self) -> List[str]:
        return ["macd", "macd_signal", "macd_hist"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        ema_fast = df["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        result["macd"] = macd_line / df["close"]
        result["macd_signal"] = signal_line / df["close"]
        result["macd_hist"] = histogram / df["close"]
        
        return result


class ATRFeature(BaseFeature):
    """平均真实波幅特征"""
    
    def __init__(self, period: int = None):
        self.period = period or config.feature.atr_period
    
    @property
    def name(self) -> str:
        return "atr"
    
    @property
    def output_columns(self) -> List[str]:
        return [f"atr_{self.period}"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.ewm(span=self.period, adjust=False).mean()
        
        result[f"atr_{self.period}"] = atr / df["close"]
        
        return result


class BollingerBandsFeature(BaseFeature):
    """布林带特征"""
    
    def __init__(self, period: int = None, std: float = None):
        self.period = period or config.feature.bb_period
        self.std = std or config.feature.bb_std
    
    @property
    def name(self) -> str:
        return "bb"
    
    @property
    def output_columns(self) -> List[str]:
        return ["bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_pct"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        middle = df["close"].rolling(window=self.period).mean()
        std = df["close"].rolling(window=self.period).std()
        
        upper = middle + (std * self.std)
        lower = middle - (std * self.std)
        
        result["bb_upper"] = (upper - df["close"]) / df["close"]
        result["bb_middle"] = (middle - df["close"]) / df["close"]
        result["bb_lower"] = (lower - df["close"]) / df["close"]
        result["bb_width"] = (upper - lower) / df["close"]
        result["bb_pct"] = (df["close"] - lower) / (upper - lower)
        
        return result


class OBVFeature(BaseFeature):
    """能量潮特征"""
    
    def __init__(self, ema_period: int = None):
        self.ema_period = ema_period or config.feature.obv_ema_period
    
    @property
    def name(self) -> str:
        return "obv"
    
    @property
    def output_columns(self) -> List[str]:
        return ["obv_norm", "obv_ema_norm"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        direction = np.sign(df["close"].diff())
        obv = (direction * df["volume"]).cumsum()
        obv_ema = obv.ewm(span=self.ema_period, adjust=False).mean()
        
        obv_max = obv.rolling(window=100, min_periods=1).max()
        obv_min = obv.rolling(window=100, min_periods=1).min()
        obv_range = obv_max - obv_min
        
        result["obv_norm"] = (obv - obv_min) / obv_range.replace(0, 1)
        result["obv_ema_norm"] = (obv_ema - obv_min) / obv_range.replace(0, 1)
        
        return result


TECHNICAL_FEATURES = {
    "ema": EMAFeature,
    "rsi": RSIFeature,
    "macd": MACDFeature,
    "atr": ATRFeature,
    "bb": BollingerBandsFeature,
    "obv": OBVFeature,
}
