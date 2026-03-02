"""
数据服务 API 模块

提供 RESTful API 接口
"""

import logging
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import config
from .models import ApiResponse, ErrorCode
from .service import data_service

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Quant Data Service",
    description="比特币量化交易系统 - 数据服务",
    version="1.0.0"
)


class SyncRequest(BaseModel):
    """数据同步请求"""
    symbol: str = "BTCUSDT"
    start_date: str
    end_date: Optional[str] = None


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/v1/klines")
async def get_klines(
    symbol: str = Query(default="BTCUSDT", description="交易对"),
    interval: str = Query(default="1h", description="K线周期"),
    start_time: Optional[int] = Query(default=None, description="开始时间戳(ms)"),
    end_time: Optional[int] = Query(default=None, description="结束时间戳(ms)"),
    limit: int = Query(default=500, ge=1, le=1500, description="返回数量")
):
    """
    获取 K 线数据
    
    优先从数据库查询，缺失数据从 Binance API 获取
    """
    try:
        if start_time is None or end_time is None:
            klines = data_service.get_latest_klines(symbol, interval, limit)
        else:
            klines = data_service.get_klines(symbol, interval, start_time, end_time)
            if len(klines) > limit:
                klines = klines[-limit:]
        
        data = [k.to_dict() for k in klines]
        
        for item in data:
            item.pop("symbol", None)
            item.pop("interval", None)
        
        return ApiResponse.success(data).to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get klines: {e}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(ErrorCode.INTERNAL_ERROR, str(e)).to_dict()
        )


@app.get("/api/v1/ticker")
async def get_ticker(
    symbol: str = Query(default="BTCUSDT", description="交易对")
):
    """
    获取最新价格
    """
    try:
        ticker = data_service.get_ticker(symbol)
        return ApiResponse.success(ticker.to_dict()).to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get ticker: {e}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(ErrorCode.BINANCE_API_ERROR, str(e)).to_dict()
        )


@app.post("/api/v1/sync")
async def sync_data(request: SyncRequest):
    """
    同步历史数据
    """
    try:
        result = data_service.sync_historical_data(
            symbol=request.symbol,
            interval=config.interval,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return ApiResponse.success(result.to_dict()).to_dict()
        
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        return JSONResponse(
            status_code=400,
            content=ApiResponse.error(ErrorCode.PARAM_ERROR, str(e)).to_dict()
        )
    except Exception as e:
        logger.error(f"Failed to sync data: {e}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(ErrorCode.INTERNAL_ERROR, str(e)).to_dict()
        )


@app.get("/api/v1/status")
async def get_data_status(
    symbol: str = Query(default="BTCUSDT", description="交易对"),
    interval: str = Query(default="1h", description="K线周期")
):
    """
    获取数据状态
    """
    try:
        status = data_service.get_data_status(symbol, interval)
        return ApiResponse.success(status).to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get data status: {e}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(ErrorCode.INTERNAL_ERROR, str(e)).to_dict()
        )


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    return app
