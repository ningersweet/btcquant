"""
预测服务 API 模块
"""

import logging
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import pandas as pd

from .config import config
from .src.model_trainer import ModelTrainer
from .src.inference import InferenceService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Quant Predict Service",
    description="比特币量化交易系统 - 预测服务",
    version="1.0.0"
)

trainer = ModelTrainer()
inference_service = InferenceService(trainer)


class TrainRequest(BaseModel):
    """训练请求"""
    train_start: str
    train_end: str
    val_start: Optional[str] = None
    val_end: Optional[str] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/predict")
async def get_prediction(symbol: str = Query(default="BTCUSDT")):
    """
    获取预测信号
    """
    try:
        async with httpx.AsyncClient() as client:
            ticker_resp = await client.get(
                f"{config.service.data_service_url}/api/v1/ticker",
                params={"symbol": symbol}
            )
            ticker_data = ticker_resp.json()
            current_price = ticker_data["data"]["price"]
            timestamp = ticker_data["data"]["timestamp"]
            
            klines_resp = await client.get(
                f"{config.service.data_service_url}/api/v1/klines",
                params={"symbol": symbol, "interval": "1h", "limit": 100}
            )
            klines_data = klines_resp.json()["data"]
            
            features_resp = await client.post(
                f"{config.service.features_service_url}/api/v1/features/compute",
                json={"klines": klines_data}
            )
            features_data = features_resp.json()["data"]
        
        if not features_data["features"]:
            return {"code": 2002, "message": "No features computed", "data": None}
        
        latest_features = features_data["features"][-1]
        feature_cols = features_data["feature_columns"]
        
        import numpy as np
        feature_values = np.array([latest_features.get(c, 0) for c in feature_cols])
        
        result = inference_service.predict(feature_values, current_price, timestamp)
        
        return {"code": 0, "data": result.to_dict()}
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.post("/api/v1/train")
async def train_model(request: TrainRequest):
    """
    触发模型训练
    """
    try:
        return {
            "code": 0,
            "data": {
                "message": "Training endpoint placeholder",
                "train_start": request.train_start,
                "train_end": request.train_end
            }
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.get("/api/v1/model/status")
async def get_model_status():
    """
    获取模型状态
    """
    return {
        "code": 0,
        "data": {
            "loaded": trainer.model is not None,
            "feature_count": len(trainer.feature_columns),
            "model_path": str(trainer.model_path)
        }
    }


@app.post("/api/v1/model/load")
async def load_model(model_id: str):
    """
    加载模型
    """
    success = trainer.load(model_id)
    if success:
        return {"code": 0, "data": {"loaded": True, "model_id": model_id}}
    return JSONResponse(
        status_code=404,
        content={"code": 2001, "message": "Model not found", "data": None}
    )


def create_app() -> FastAPI:
    return app
