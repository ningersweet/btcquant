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
        from .src.label_generator import generate_labels
        from datetime import datetime
        
        logger.info(f"Starting training: {request.train_start} to {request.train_end}")
        
        # 1. 获取训练数据
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 转换日期为时间戳
            train_start_ts = int(pd.Timestamp(request.train_start).timestamp() * 1000)
            train_end_ts = int(pd.Timestamp(request.train_end).timestamp() * 1000)
            
            logger.info(f"Fetching klines from {train_start_ts} to {train_end_ts}")
            
            # 获取 K 线数据
            klines_url = f"{config.service.data_service_url}/api/v1/klines"
            klines_params = {
                "symbol": "BTCUSDT",
                "interval": "1h",
                "start_time": train_start_ts,
                "end_time": train_end_ts,
                "limit": 50000
            }
            
            logger.info(f"Requesting: {klines_url} with params: {klines_params}")
            
            klines_resp = await client.get(klines_url, params=klines_params)
            klines_json = klines_resp.json()
            
            logger.info(f"Klines response keys: {klines_json.keys()}")
            
            if "code" in klines_json and klines_json["code"] != 0:
                return JSONResponse(
                    status_code=400,
                    content={"code": klines_json["code"], "message": "Data service error", "data": None}
                )
            
            klines_data = klines_json.get("data", [])
            
            if not klines_data:
                return JSONResponse(
                    status_code=400,
                    content={"code": 1001, "message": "No training data available", "data": None}
                )
            
            logger.info(f"Fetched {len(klines_data)} klines")
            
            # 2. 计算特征
            logger.info("Computing features...")
            features_resp = await client.post(
                f"{config.service.features_service_url}/api/v1/features/compute",
                json={"klines": klines_data}
            )
            features_json = features_resp.json()
            
            if "code" in features_json and features_json["code"] != 0:
                return JSONResponse(
                    status_code=400,
                    content={"code": features_json["code"], "message": "Features service error", "data": None}
                )
            
            features_data = features_json.get("data", {})
        
        # 3. 构建 DataFrame
        df = pd.DataFrame(features_data["features"])
        feature_columns = features_data["feature_columns"]
        
        logger.info(f"Features computed: {len(feature_columns)} columns, {len(df)} rows")
        
        # 4. 生成标签
        logger.info("Generating labels...")
        df = generate_labels(df, window=config.label.window_size)
        
        # 5. 准备训练数据
        X, y, weights = trainer.prepare_data(df, feature_columns)
        
        logger.info(f"Training data prepared: X={X.shape}, y={y.shape}")
        
        # 6. 训练模型
        logger.info("Training model...")
        metrics = trainer.train(X, y, weights, val_size=0.1)
        
        # 7. 保存模型
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = trainer.save(model_id)
        
        logger.info(f"Model saved: {model_id}")
        
        return {
            "code": 0,
            "data": {
                "model_id": model_id,
                "model_path": model_path,
                "metrics": metrics,
                "train_samples": len(X),
                "feature_count": len(feature_columns)
            }
        }
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
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
