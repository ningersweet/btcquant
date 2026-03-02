"""
结构特征模块

包含高低点、整数关口、时间特征、收益率、K线形态等
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from .base import BaseFeature
from .config import config


class HighLowFeature(BaseFeature):
    """N 周期高低点特征"""
    
    def __init__(self, periods: tuple = None):
        self.periods = periods or config.feature.lookback_periods
    
    @property
    def name(self) -> str:
        return "highlow"
    
    @property
    def output_columns(self) -> List[str]:
        cols = []
        for p in self.periods:
            cols.extend([f"highest_high_{p}", f"lowest_low_{p}"])
        return cols
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        for period in self.periods:
            highest = df["high"].rolling(window=period).max()
            lowest = df["low"].rolling(window=period).min()
            
            result[f"highest_high_{period}"] = (highest - df["close"]) / df["close"]
            result[f"lowest_low_{period}"] = (df["close"] - lowest) / df["close"]
        
        return result


class RoundNumberFeature(BaseFeature):
    """整数关口距离特征"""
    
    def __init__(self, base: int = None):
        self.base = base or config.feature.round_number_base
    
    @property
    def name(self) -> str:
        return "round_number"
    
    @property
    def output_columns(self) -> List[str]:
        return ["round_dist_pct", "round_above_pct", "round_below_pct"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        round_above = np.ceil(df["close"] / self.base) * self.base
        round_below = np.floor(df["close"] / self.base) * self.base
        
        dist_above = round_above - df["close"]
        dist_below = df["close"] - round_below
        
        nearest_dist = np.minimum(dist_above, dist_below)
        
        result["round_dist_pct"] = nearest_dist / df["close"]
        result["round_above_pct"] = dist_above / df["close"]
        result["round_below_pct"] = dist_below / df["close"]
        
        return result


class TimeFeature(BaseFeature):
    """时间特征"""
    
    @property
    def name(self) -> str:
        return "time"
    
    @property
    def output_columns(self) -> List[str]:
        return ["hour", "day_of_week", "is_weekend", "hour_sin", "hour_cos"]
    
    @property
    def required_columns(self) -> List[str]:
        return ["timestamp"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        if "timestamp" in df.columns:
            dt = pd.to_datetime(df["timestamp"], unit="ms")
        else:
            dt = df.index
        
        result["hour"] = dt.dt.hour / 24
        result["day_of_week"] = dt.dt.dayofweek / 7
        result["is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
        
        result["hour_sin"] = np.sin(2 * np.pi * dt.dt.hour / 24)
        result["hour_cos"] = np.cos(2 * np.pi * dt.dt.hour / 24)
        
        return result


class ReturnFeature(BaseFeature):
    """收益率特征"""
    
    def __init__(self, periods: tuple = None):
        self.periods = periods or config.feature.return_periods
    
    @property
    def name(self) -> str:
        return "return"
    
    @property
    def output_columns(self) -> List[str]:
        return [f"return_{p}" for p in self.periods]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        for period in self.periods:
            result[f"return_{period}"] = df["close"].pct_change(periods=period)
        
        return result


class CandleFeature(BaseFeature):
    """K 线形态特征"""
    
    @property
    def name(self) -> str:
        return "candle"
    
    @property
    def output_columns(self) -> List[str]:
        return ["body_ratio", "upper_shadow", "lower_shadow", "is_bullish"]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        body = (df["close"] - df["open"]).abs()
        full_range = df["high"] - df["low"]
        
        result["body_ratio"] = body / full_range.replace(0, np.nan)
        
        upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
        lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]
        
        result["upper_shadow"] = upper_shadow / full_range.replace(0, np.nan)
        result["lower_shadow"] = lower_shadow / full_range.replace(0, np.nan)
        
        result["is_bullish"] = (df["close"] > df["open"]).astype(int)
        
        return result


class VolatilityFeature(BaseFeature):
    """波动率特征"""
    
    def __init__(self, periods: tuple = None):
        self.periods = periods or config.feature.lookback_periods
    
    @property
    def name(self) -> str:
        return "volatility"
    
    @property
    def output_columns(self) -> List[str]:
        return [f"volatility_{p}" for p in self.periods]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_input(df)
        result = df.copy()
        
        returns = df["close"].pct_change()
        
        for period in self.periods:
            result[f"volatility_{period}"] = returns.rolling(window=period).std()
        
        return result


STRUCTURAL_FEATURES = {
    "highlow": HighLowFeature,
    "round_number": RoundNumberFeature,
    "time": TimeFeature,
    "return": ReturnFeature,
    "candle": CandleFeature,
    "volatility": VolatilityFeature,
}
