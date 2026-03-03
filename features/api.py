"""
特征工程服务 API 模块
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd

from .config import config
from .registry import registry
from .pipeline import compute_features, get_feature_columns

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Quant Features Service",
    description="比特币量化交易系统 - 特征工程服务",
    version="1.0.0"
)


class KlineData(BaseModel):
    """K 线数据"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class ComputeRequest(BaseModel):
    """特征计算请求"""
    klines: List[KlineData]
    feature_names: Optional[List[str]] = None


class ApiResponse(BaseModel):
    """API 响应"""
    code: int
    data: Optional[dict] = None
    message: Optional[str] = None


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/v1/features/compute")
async def compute_features_api(request: ComputeRequest):
    """
    计算特征
    
    接收 K 线数据，返回计算后的特征
    """
    try:
        data = [k.model_dump() for k in request.klines]
        df = pd.DataFrame(data)
        
        result_df = compute_features(df, request.feature_names, drop_na=False)
        
        feature_cols = get_feature_columns(request.feature_names)
        
        output_cols = ["timestamp"] + feature_cols
        available_cols = [c for c in output_cols if c in result_df.columns]
        
        import numpy as np
        result_df = result_df[available_cols].replace([np.inf, -np.inf], np.nan)
        
        # 保留 NaN（序列化为 JSON null），让 LightGBM 原生处理缺失值
        features = result_df.to_dict(orient="records")
        for record in features:
            for key, val in record.items():
                if isinstance(val, float) and val != val:
                    record[key] = None
        
        return {
            "code": 0,
            "data": {
                "features": features,
                "feature_columns": feature_cols
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to compute features: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.get("/api/v1/features/list")
async def list_features():
    """
    获取可用特征列表
    """
    try:
        features = registry.list_features()
        return {
            "code": 0,
            "data": features
        }
    except Exception as e:
        logger.error(f"Failed to list features: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.get("/api/v1/features/columns")
async def get_columns(feature_names: Optional[str] = None):
    """
    获取特征列名
    
    Args:
        feature_names: 逗号分隔的特征名称
    """
    try:
        names = feature_names.split(",") if feature_names else None
        columns = get_feature_columns(names)
        return {
            "code": 0,
            "data": {
                "columns": columns,
                "count": len(columns)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get columns: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    return app
