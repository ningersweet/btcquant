# 策略与执行服务 (Strategy Service) 详细设计

## 1. 模块概述

策略服务负责根据预测信号执行交易，管理仓位和状态，支持回测、模拟和实盘三种模式。

### 1.1 核心职责

- 交易状态机管理
- 仓位计算与管理
- 回测撮合引擎
- 交易执行接口

### 1.2 服务端口

- **端口**: 8004
- **健康检查**: `GET /health`

---

## 2. 文件结构

```
strategy/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── models.py            # 数据模型定义
├── position_manager.py  # 仓位管理
├── state_machine.py     # 交易状态机
├── executor/
│   ├── __init__.py
│   ├── interface.py     # 统一交易接口
│   └── backtest_engine.py  # 回测撮合引擎
├── api.py               # FastAPI 接口
├── requirements.txt     # 依赖列表
└── Dockerfile           # Docker 镜像
```

---

## 3. 数据模型

### 3.1 持仓信息

```python
@dataclass
class Position:
    symbol: str           # 交易对
    side: Side            # 方向 (LONG/SHORT)
    entry_price: float    # 入场价格
    quantity: float       # 数量
    sl_price: float       # 止损价格
    tp_price: float       # 止盈价格
    entry_time: int       # 入场时间
    deadline: int         # 最大持仓时间
    rr_predicted: float   # 预测的盈亏比
```

### 3.2 交易记录

```python
@dataclass
class Trade:
    trade_id: str         # 交易 ID
    symbol: str           # 交易对
    side: Side            # 方向
    entry_price: float    # 入场价格
    exit_price: float     # 出场价格
    sl_price: float       # 止损价格
    tp_price: float       # 止盈价格
    quantity: float       # 数量
    entry_time: int       # 入场时间
    exit_time: int        # 出场时间
    exit_reason: ExitReason  # 出场原因 (SL/TP/TIME/MANUAL)
    pnl: float            # 盈亏金额
    pnl_pct: float        # 盈亏百分比
    rr_predicted: float   # 预测的盈亏比
    rr_actual: float      # 实际的盈亏比
    mode: str             # 模式 (backtest/paper/live)
```

### 3.3 枚举类型

```python
class Side(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class ExitReason(Enum):
    SL = "SL"       # 止损
    TP = "TP"       # 止盈
    TIME = "TIME"   # 超时
    MANUAL = "MANUAL"  # 手动
```

---

## 4. 交易状态机

### 4.1 状态定义

```python
class SystemState(Enum):
    IDLE = "idle"           # 空闲，等待信号
    WAITING_SIGNAL = "waiting"  # 等待信号确认
    POSITION_OPEN = "open"  # 持仓中
    CLOSING = "closing"     # 平仓中
```

### 4.2 状态转换图

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│    ┌────────┐                         ┌────────┐        │
│    │  IDLE  │◄────────────────────────│CLOSING │        │
│    └───┬────┘                         └────▲───┘        │
│        │                                   │            │
│        │ 收到有效信号                       │            │
│        ▼                                   │            │
│    ┌────────┐                              │            │
│    │WAITING │                              │            │
│    └───┬────┘                              │            │
│        │                                   │            │
│        │ 开仓成功                           │            │
│        ▼                                   │            │
│    ┌────────┐     触发 SL/TP/TIME          │            │
│    │  OPEN  │──────────────────────────────┘            │
│    └────────┘                                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.3 状态机接口

```python
class TradingStateMachine:
    def can_open_position(self) -> bool
    def open_position(self, position: Position) -> bool
    def close_position(self, exit_price, exit_time, pnl) -> bool
    def check_exit_conditions(self, current_price, current_time) -> Optional[str]
    def get_status(self) -> dict
```

---

## 5. 仓位管理

### 5.1 仓位计算

```python
def calculate_position_size(
    risk_amount: float,    # 单笔风险金额 (USDT)
    entry_price: float,    # 入场价格
    sl_price: float,       # 止损价格
    leverage: int = 20     # 杠杆倍数
) -> Dict:
    sl_distance = abs(entry_price - sl_price)
    sl_pct = sl_distance / entry_price
    
    quantity = risk_amount / sl_distance
    notional = quantity * entry_price
    margin = notional / leverage
    
    return {
        "quantity": quantity,
        "margin": margin,
        "notional": notional,
        "sl_distance": sl_distance,
        "sl_pct": sl_pct
    }
```

### 5.2 盈亏计算

```python
def calculate_pnl(
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float
) -> Dict:
    if side == "LONG":
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = (exit_price - entry_price) / entry_price
    else:  # SHORT
        pnl = (entry_price - exit_price) * quantity
        pnl_pct = (entry_price - exit_price) / entry_price
    
    return {"pnl": pnl, "pnl_pct": pnl_pct}
```

### 5.3 实际盈亏比计算

```python
def calculate_actual_rr(
    side: str,
    entry_price: float,
    exit_price: float,
    sl_price: float
) -> float:
    sl_distance = abs(entry_price - sl_price)
    
    if side == "LONG":
        profit_distance = exit_price - entry_price
    else:
        profit_distance = entry_price - exit_price
    
    return profit_distance / sl_distance if sl_distance > 0 else 0
```

---

## 6. 执行器接口

### 6.1 统一接口定义

```python
class ExecutorInterface(ABC):
    @abstractmethod
    def open_position(self, symbol, side, quantity, sl_price, tp_price) -> OrderResult
    
    @abstractmethod
    def close_position(self, symbol, reason) -> OrderResult
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo
    
    @abstractmethod
    def get_current_price(self, symbol) -> float
```

### 6.2 回测撮合引擎

```python
class BacktestEngine(ExecutorInterface):
    def __init__(self, initial_balance: float, klines: pd.DataFrame):
        self.balance = initial_balance
        self.klines = klines
        self.current_idx = 0
        self.trades: List[Trade] = []
    
    def step(self) -> bool:
        """前进一步"""
        self.current_idx += 1
        return self.current_idx < len(self.klines)
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录"""
        return pd.DataFrame([t.to_dict() for t in self.trades])
```

---

## 7. API 接口

### 7.1 获取系统状态

```
GET /api/v1/status
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "state": "idle",
    "mode": "backtest",
    "current_position": null,
    "total_trades": 42,
    "total_pnl": 1234.56,
    "last_trade_time": 1709251200000
  }
}
```

### 7.2 获取持仓信息

```
GET /api/v1/position
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "has_position": true,
    "position": {
      "symbol": "BTCUSDT",
      "side": "LONG",
      "entry_price": 62500.0,
      "quantity": 0.016,
      "sl_price": 62000.0,
      "tp_price": 63675.0,
      "entry_time": 1709251200000,
      "deadline": 1709254800000,
      "rr_predicted": 2.35
    }
  }
}
```

### 7.3 手动平仓

```
POST /api/v1/close
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "success": true,
    "exit_price": 62800.0,
    "pnl": 4.8,
    "exit_reason": "MANUAL"
  }
}
```

### 7.4 获取策略配置

```
GET /api/v1/config
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "mode": "backtest",
    "risk_amount": 100,
    "min_rr_threshold": 1.5,
    "leverage": 20,
    "max_sl_pct": 0.05
  }
}
```

---

## 8. 配置项

```yaml
strategy:
  host: "0.0.0.0"
  port: 8004
  predict_service_url: "http://predict-service:8003"
  data_service_url: "http://data-service:8001"
  
  trading:
    mode: "backtest"      # backtest / paper / live
    risk_amount: 100      # 单笔风险金额 (USDT)
    min_rr_threshold: 1.5 # 最小盈亏比阈值
    max_sl_pct: 0.05      # 最大止损百分比
    min_sl_pct: 0.001     # 最小止损百分比
    leverage: 20          # 杠杆倍数
```

---

## 9. 出场条件

| 条件 | 说明 | 触发逻辑 |
|------|------|----------|
| SL | 止损 | LONG: price <= sl_price; SHORT: price >= sl_price |
| TP | 止盈 | LONG: price >= tp_price; SHORT: price <= tp_price |
| TIME | 超时 | current_time >= deadline |
| MANUAL | 手动 | 用户主动平仓 |
