# 数据服务 (Data Service) 详细设计

## 1. 模块概述

数据服务是 BTC Quant 系统的基础模块，负责从 Binance API 获取 K 线数据，并提供数据库优先的查询策略。

### 1.1 核心职责

- 从 Binance Futures API 获取 K 线数据
- 本地 SQLite 数据库存储和查询
- 数据预处理（时间对齐、缺失检测、填充）
- 提供 RESTful API 接口

### 1.2 服务端口

- **端口**: 8001
- **健康检查**: `GET /health`

---

## 2. 文件结构

```
data/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── models.py            # 数据模型定义
├── database.py          # 数据库操作
├── fetcher.py           # Binance API 调用
├── preprocessor.py      # 数据预处理
├── service.py           # 核心服务逻辑
├── api.py               # FastAPI 接口
├── main.py              # 服务入口
├── requirements.txt     # 依赖列表
└── Dockerfile           # Docker 镜像
```

---

## 3. 核心组件

### 3.1 数据模型 (models.py)

```python
@dataclass
class Kline:
    """K 线数据"""
    timestamp: int      # 开盘时间 (ms)
    open: float         # 开盘价
    high: float         # 最高价
    low: float          # 最低价
    close: float        # 收盘价
    volume: float       # 成交量
    symbol: str         # 交易对
    interval: str       # K 线周期

@dataclass
class Ticker:
    """最新价格"""
    symbol: str
    price: float
    timestamp: int
```

### 3.2 数据库操作 (database.py)

```python
class Database:
    def insert_klines(self, klines: List[Kline]) -> int
    def query_klines(self, symbol, interval, start_time, end_time) -> List[Kline]
    def get_latest_klines(self, symbol, interval, limit) -> List[Kline]
    def get_data_range(self, symbol, interval) -> Tuple[int, int]
```

**数据库表结构**:

```sql
CREATE TABLE klines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    UNIQUE(timestamp, symbol, interval)
);

CREATE INDEX idx_klines_lookup ON klines(symbol, interval, timestamp);
```

### 3.3 Binance API 调用 (fetcher.py)

```python
class BinanceFetcher:
    def fetch_klines(self, symbol, interval, start_time, end_time, limit) -> List[Kline]
    def get_ticker(self, symbol) -> Ticker
```

**API 端点**:
- K 线数据: `GET /fapi/v1/klines`
- 最新价格: `GET /fapi/v1/ticker/price`

### 3.4 数据预处理 (preprocessor.py)

```python
class DataPreprocessor:
    def align_timestamps(self, klines, interval) -> List[Kline]
    def find_missing_ranges(self, klines, start, end, interval) -> List[Tuple]
    def fill_missing_data(self, klines, missing_ranges) -> List[Kline]
```

### 3.5 核心服务 (service.py)

```python
class DataService:
    def get_klines(self, symbol, interval, start_time, end_time) -> List[Kline]
    def get_latest_klines(self, symbol, interval, limit) -> List[Kline]
    def get_ticker(self, symbol) -> Ticker
    def sync_historical_data(self, symbol, interval, start_date, end_date) -> SyncResult
```

---

## 4. 数据库优先查询策略

### 4.1 流程图

```
┌─────────────────┐
│   查询请求       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 查询本地数据库   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ 检查数据完整性   │────▶│  数据完整？      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
             ┌──────────┐              ┌──────────┐
             │   是     │              │   否     │
             └────┬─────┘              └────┬─────┘
                  │                         │
                  │                         ▼
                  │                  ┌─────────────────┐
                  │                  │ 找出缺失时间段   │
                  │                  └────────┬────────┘
                  │                           │
                  │                           ▼
                  │                  ┌─────────────────┐
                  │                  │ 从 API 获取数据  │
                  │                  └────────┬────────┘
                  │                           │
                  │                           ▼
                  │                  ┌─────────────────┐
                  │                  │ 保存到数据库     │
                  │                  └────────┬────────┘
                  │                           │
                  ▼                           ▼
             ┌─────────────────────────────────────┐
             │           返回完整数据               │
             └─────────────────────────────────────┘
```

### 4.2 实现代码

```python
def get_klines(self, symbol, interval, start_time, end_time):
    # 1. 查询数据库
    db_klines = self.db.query_klines(symbol, interval, start_time, end_time)
    
    # 2. 检查完整性
    missing_ranges = self.preprocessor.find_missing_ranges(
        db_klines, start_time, end_time, interval
    )
    
    # 3. 获取缺失数据
    if missing_ranges:
        for range_start, range_end in missing_ranges:
            api_klines = self.fetcher.fetch_klines(
                symbol, interval, range_start, range_end
            )
            self.db.insert_klines(api_klines)
        
        # 重新查询
        db_klines = self.db.query_klines(symbol, interval, start_time, end_time)
    
    return db_klines
```

---

## 5. API 接口

### 5.1 获取 K 线数据

```
GET /api/v1/klines
```

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | string | 否 | BTCUSDT | 交易对 |
| interval | string | 否 | 1h | K 线周期 |
| start_time | int | 否 | - | 开始时间戳 (ms) |
| end_time | int | 否 | - | 结束时间戳 (ms) |
| limit | int | 否 | 500 | 返回数量 (1-1500) |

**响应**:

```json
{
  "code": 0,
  "data": [
    {
      "timestamp": 1709251200000,
      "open": 62500.0,
      "high": 62800.0,
      "low": 62300.0,
      "close": 62600.0,
      "volume": 1234.56
    }
  ]
}
```

### 5.2 获取最新价格

```
GET /api/v1/ticker
```

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | string | 否 | BTCUSDT | 交易对 |

**响应**:

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "price": 62500.0,
    "timestamp": 1709251200000
  }
}
```

### 5.3 同步历史数据

```
POST /api/v1/sync
```

**请求体**:

```json
{
  "symbol": "BTCUSDT",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01"
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "total_records": 1440,
    "new_records": 720,
    "start_time": 1704067200000,
    "end_time": 1709251200000
  }
}
```

### 5.4 获取数据状态

```
GET /api/v1/status
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "total_records": 8760,
    "earliest_time": 1672531200000,
    "latest_time": 1709251200000,
    "coverage_days": 365
  }
}
```

---

## 6. 配置项

```yaml
data:
  symbol: "BTCUSDT"           # 默认交易对
  interval: "1h"              # 默认 K 线周期
  host: "0.0.0.0"             # 服务地址
  port: 8001                  # 服务端口
  
  binance:
    base_url: "https://fapi.binance.com"
    testnet_url: "https://testnet.binancefuture.com"
    use_testnet: false
    max_klines_per_request: 1500
    request_timeout: 30
    retry_count: 3
    retry_delay: 1.0
  
  database:
    db_path: "/app/data/btc_quant.db"
    echo: false
```

---

## 7. 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | Binance API 错误 |
| 1003 | 内部错误 |
| 1004 | 数据库错误 |
