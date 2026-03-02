"""
预测服务 API 模块
"""

import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import pandas as pd
import numpy as np

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


async def fetch_all_klines(
    client: httpx.AsyncClient,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    batch_size: int = 1500
) -> List[dict]:
    """
    分批获取完整的历史 K 线数据
    
    Args:
        client: HTTP 客户端
        symbol: 交易对
        interval: 时间间隔
        start_time: 开始时间戳（毫秒）
        end_time: 结束时间戳（毫秒）
        batch_size: 每批数据量
        
    Returns:
        完整的 K 线数据列表
    """
    all_data = []
    current_time = start_time
    batch_count = 0
    
    # 计算预期批次数
    time_diff_hours = (end_time - start_time) / (1000 * 3600)
    expected_batches = int(time_diff_hours / batch_size) + 1
    
    logger.info(f"Fetching data from {pd.Timestamp(start_time, unit='ms')} to {pd.Timestamp(end_time, unit='ms')}")
    logger.info(f"Expected batches: ~{expected_batches}, batch_size: {batch_size}")
    
    while current_time < end_time:
        batch_count += 1
        
        try:
            response = await client.get(
                f"{config.service.data_service_url}/api/v1/klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "start_time": current_time,
                    "end_time": end_time,
                    "limit": batch_size
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"Batch {batch_count} failed: HTTP {response.status_code}")
                break
            
            batch_data = response.json().get("data", [])
            
            if not batch_data:
                logger.info(f"No more data at batch {batch_count}")
                break
            
            all_data.extend(batch_data)
            
            # 更新时间戳到下一批
            last_timestamp = batch_data[-1]["timestamp"]
            current_time = last_timestamp + 3600000  # +1 小时（毫秒）
            
            # 避免请求过快
            if batch_count % 10 == 0:
                logger.info(f"Fetched {len(all_data)} records in {batch_count} batches...")
                await asyncio.sleep(0.1)
            
            # 如果这批数据少于 batch_size，说明已经到达终点
            if len(batch_data) < batch_size:
                break
                
        except Exception as e:
            logger.error(f"Error fetching batch {batch_count}: {e}")
            break
    
    logger.info(f"Total fetched: {len(all_data)} records in {batch_count} batches")
    return all_data


class TrainRequest(BaseModel):
    """训练请求"""
    train_start: str
    train_end: str
    val_start: Optional[str] = None
    val_end: Optional[str] = None


class OptimizeRequest(BaseModel):
    """超参数优化请求"""
    train_start: str = "2019-01-01"
    train_end: str = "2024-06-30"
    val_start: str = "2024-07-01"
    val_end: str = "2025-06-30"
    test_start: str = "2025-07-01"
    test_end: str = "2026-02-28"
    n_trials: int = 50
    timeout: int = 3600


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
        
        # 使用模型训练时的特征列
        if not trainer.feature_columns:
            return {"code": 2003, "message": "Model not loaded", "data": None}
        
        import numpy as np
        # 只使用模型训练时的特征
        feature_values = np.array([latest_features.get(c, 0) for c in trainer.feature_columns])
        
        result = inference_service.predict(feature_values, current_price, timestamp)
        
        return {"code": 0, "data": result.to_dict()}
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.post("/api/v1/train/optimize")
async def optimize_hyperparameters(request: OptimizeRequest):
    """
    超参数优化
    
    使用 Optuna 自动搜索最佳超参数
    """
    try:
        import numpy as np
        from .src.hyperparameter_tuner import HyperparameterTuner
        from .src.label_generator import generate_labels
        from datetime import datetime
        
        logger.info(f"Starting hyperparameter optimization")
        logger.info(f"Train: {request.train_start} to {request.train_end}")
        logger.info(f"Val: {request.val_start} to {request.val_end}")
        logger.info(f"Test: {request.test_start} to {request.test_end}")
        logger.info(f"Trials: {request.n_trials}, Timeout: {request.timeout}s")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # 1. 获取训练数据（分批获取）
            train_start_ts = int(pd.Timestamp(request.train_start).timestamp() * 1000)
            train_end_ts = int(pd.Timestamp(request.train_end).timestamp() * 1000)
            
            logger.info(f"Fetching training data...")
            train_klines_data = await fetch_all_klines(
                client=client,
                symbol="BTCUSDT",
                interval="1h",
                start_time=train_start_ts,
                end_time=train_end_ts,
                batch_size=1500
            )
            
            # 2. 获取验证数据（分批获取）
            val_start_ts = int(pd.Timestamp(request.val_start).timestamp() * 1000)
            val_end_ts = int(pd.Timestamp(request.val_end).timestamp() * 1000)
            
            logger.info(f"Fetching validation data...")
            val_klines_data = await fetch_all_klines(
                client=client,
                symbol="BTCUSDT",
                interval="1h",
                start_time=val_start_ts,
                end_time=val_end_ts,
                batch_size=1500
            )
            
            if not train_klines_data or not val_klines_data:
                return JSONResponse(
                    status_code=400,
                    content={"code": 1001, "message": "Insufficient data", "data": None}
                )
            
            logger.info(f"Train klines: {len(train_klines_data)}, Val klines: {len(val_klines_data)}")
            
            # 3. 计算训练集特征
            logger.info("Computing training features...")
            train_features_resp = await client.post(
                f"{config.service.features_service_url}/api/v1/features/compute",
                json={"klines": train_klines_data},
                timeout=120.0
            )
            
            if train_features_resp.status_code != 200:
                return JSONResponse(
                    status_code=400,
                    content={"code": 1002, "message": "Features computation failed", "data": None}
                )
            
            train_features_data = train_features_resp.json().get("data", {})
            
            # 4. 计算验证集特征
            logger.info("Computing validation features...")
            val_features_resp = await client.post(
                f"{config.service.features_service_url}/api/v1/features/compute",
                json={"klines": val_klines_data},
                timeout=120.0
            )
            
            if val_features_resp.status_code != 200:
                return JSONResponse(
                    status_code=400,
                    content={"code": 1002, "message": "Features computation failed", "data": None}
                )
            
            val_features_data = val_features_resp.json().get("data", {})
        
        # 5. 构建训练集 DataFrame
        train_klines_df = pd.DataFrame(train_klines_data)
        train_features_df = pd.DataFrame(train_features_data["features"])
        train_df = pd.merge(train_klines_df, train_features_df, on='timestamp', how='inner')
        train_df = generate_labels(train_df, window=config.label.window_size)
        
        # 6. 构建验证集 DataFrame
        val_klines_df = pd.DataFrame(val_klines_data)
        val_features_df = pd.DataFrame(val_features_data["features"])
        val_df = pd.merge(val_klines_df, val_features_df, on='timestamp', how='inner')
        val_df = generate_labels(val_df, window=config.label.window_size)
        
        feature_columns = train_features_data["feature_columns"]
        available_features = [col for col in feature_columns if col in train_df.columns and col in val_df.columns]
        
        logger.info(f"Using {len(available_features)} features")
        
        # 7. 准备数据
        target_columns = ["y_rr", "y_sl_pct", "y_tp_pct"]
        
        train_clean = train_df.dropna(subset=available_features + target_columns)
        val_clean = val_df.dropna(subset=available_features + target_columns)
        
        X_train = train_clean[available_features].values
        y_train = train_clean[target_columns].values
        X_val = val_clean[available_features].values
        y_val = val_clean[target_columns].values
        
        from .src.label_generator import compute_sample_weights
        weights_train = compute_sample_weights(train_clean["timestamp"])
        
        logger.info(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")
        
        # 8. 执行超参数优化
        tuner = HyperparameterTuner(random_state=config.model.random_state)
        optimization_result = tuner.optimize(
            X_train, y_train, X_val, y_val,
            weights_train=weights_train,
            n_trials=request.n_trials,
            timeout=request.timeout
        )
        
        # 9. 使用最佳参数训练最终模型
        logger.info("Training final model with best parameters...")
        trainer.feature_columns = available_features
        
        # 合并训练集和验证集进行最终训练
        X_full = np.vstack([X_train, X_val])
        y_full = np.vstack([y_train, y_val])
        weights_val = compute_sample_weights(val_clean["timestamp"])
        weights_full = np.concatenate([weights_train, weights_val])
        
        final_metrics = trainer.train(
            X_full, y_full,
            weights=weights_full,
            val_size=0.1,
            custom_params=optimization_result['best_params']
        )
        
        # 10. 保存模型
        model_id = f"model_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = trainer.save(model_id)
        
        logger.info(f"Optimized model saved: {model_id}")
        
        return {
            "code": 0,
            "data": {
                "model_id": model_id,
                "model_path": model_path,
                "optimization": optimization_result,
                "final_metrics": final_metrics,
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "feature_count": len(available_features)
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
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
            
            # 使用分批获取
            klines_data = await fetch_all_klines(
                client=client,
                symbol="BTCUSDT",
                interval="1h",
                start_time=train_start_ts,
                end_time=train_end_ts,
                batch_size=1500
            )
            
            if not klines_data:
                logger.error("No klines data returned")
                return JSONResponse(
                    status_code=400,
                    content={"code": 1001, "message": "No training data available", "data": None}
                )
            
            logger.info(f"Fetched {len(klines_data)} klines")
            
            # 2. 计算特征
            logger.info("Computing features...")
            
            # 构造正确的请求体
            features_request = {"klines": klines_data}
            logger.info(f"Features request has {len(klines_data)} klines")
            
            features_resp = await client.post(
                f"{config.service.features_service_url}/api/v1/features/compute",
                json=features_request,
                timeout=120.0
            )
            
            logger.info(f"Features response status: {features_resp.status_code}")
            
            if features_resp.status_code != 200:
                logger.error(f"Features service error: status={features_resp.status_code}, body={features_resp.text[:500]}")
                return JSONResponse(
                    status_code=400,
                    content={"code": 1002, "message": f"Features service error: {features_resp.status_code}", "data": None}
                )
            
            features_json = features_resp.json()
            
            if "code" in features_json and features_json["code"] != 0:
                return JSONResponse(
                    status_code=400,
                    content={"code": features_json["code"], "message": "Features service error", "data": None}
                )
            
            features_data = features_json.get("data", {})
        
        # 3. 构建 DataFrame
        features_list = features_data["features"]
        feature_columns = features_data["feature_columns"]
        
        logger.info(f"Features computed: {len(feature_columns)} columns, {len(features_list)} rows")
        
        # 合并原始 K 线数据和特征数据
        klines_df = pd.DataFrame(klines_data)
        features_df = pd.DataFrame(features_list)
        
        # 按 timestamp 合并
        df = pd.merge(klines_df, features_df, on='timestamp', how='inner')
        
        logger.info(f"Merged dataframe columns: {df.columns.tolist()}")
        logger.info(f"Merged dataframe shape: {df.shape}")
        
        # 4. 生成标签
        logger.info("Generating labels...")
        df = generate_labels(df, window=config.label.window_size)
        
        # 5. 准备训练数据
        # 只使用实际存在的特征列
        available_features = [col for col in feature_columns if col in df.columns]
        missing_features = [col for col in feature_columns if col not in df.columns]
        
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
        
        logger.info(f"Using {len(available_features)} features out of {len(feature_columns)}")
        
        X, y, weights = trainer.prepare_data(df, available_features)
        
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
