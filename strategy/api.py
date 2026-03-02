"""
策略服务 API 模块
"""

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import config
from .state_machine import TradingStateMachine
from .position_manager import calculate_position_size

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BTC Quant Strategy Service",
    description="比特币量化交易系统 - 策略与执行服务",
    version="1.0.0"
)

state_machine = TradingStateMachine()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/status")
async def get_status():
    """获取系统状态"""
    return {"code": 0, "data": state_machine.get_status()}


@app.get("/api/v1/position")
async def get_position():
    """获取持仓信息"""
    pos = state_machine.current_position
    return {
        "code": 0,
        "data": {
            "has_position": pos is not None,
            "position": pos.to_dict() if pos else None
        }
    }


@app.post("/api/v1/close")
async def close_position():
    """手动平仓"""
    try:
        if state_machine.current_position is None:
            return JSONResponse(
                status_code=400,
                content={"code": 3001, "message": "No position to close", "data": None}
            )
        
        return {
            "code": 0,
            "data": {
                "message": "Manual close endpoint - implement with executor"
            }
        }
    except Exception as e:
        logger.error(f"Close failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": 1003, "message": str(e), "data": None}
        )


@app.get("/api/v1/config")
async def get_config():
    """获取策略配置"""
    return {
        "code": 0,
        "data": {
            "mode": config.strategy.mode,
            "risk_amount": config.strategy.risk_amount,
            "min_rr_threshold": config.strategy.min_rr_threshold,
            "leverage": config.strategy.leverage,
            "max_sl_pct": config.strategy.max_sl_pct
        }
    }


def create_app() -> FastAPI:
    return app
