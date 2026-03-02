# 比特币量化交易系统 - 实现计划

## Context
根据 `项目设计.md` 和 `predict/模型设计.md` 两份设计文档，需要从零开始实现一个完整的比特币日内合约量化交易系统。当前项目目录仅有设计文档，无任何代码实现。

系统核心：**时间对齐网格交易 + AI 模型预测 {RR, SL, TP} 三元组**

部署方式：**每个模块独立 Docker 容器部署，微服务架构**

部署环境：**云服务器**

实现范围：**全部实现**（回测 + 模拟盘 + 实盘）

配置参数：
- **单笔固定风险金额**：可配置（通过配置文件/环境变量）
- **最低盈亏比阈值**：可配置（通过配置文件/环境变量）

---

## 实现计划

### Phase 0: 系统详细设计文档 ⭐ 首先完成
> 在编码前完成完整的系统详细设计文档

| 步骤 | 文件 | 内容 |
|------|------|------|
| 0.1 | `docs/系统详细设计.md` | 完整的系统详细设计文档，包含以下章节： |

**文档大纲：**
1. **系统概述** - 目标、范围、约束
2. **架构设计** - 微服务架构图、模块划分、通信机制
3. **Docker 部署架构** - 容器编排、Docker Network 通信、数据卷挂载
4. **模块详细设计**
   - 4.1 特征工程服务 (features-service) - 常驻
   - 4.2 数据服务 (data-service) - 常驻，Binance API + SQLite
   - 4.3 预测服务 (predict-service) - 常驻
   - 4.4 策略与执行服务 (strategy-service) - 常驻，含执行层抽象
   - 4.5 评估模块 (evaluation) - 按需运行脚本
5. **接口设计** - REST API 接口定义（服务间通过 Docker Network 直连）
6. **数据流设计** - 各模块间数据流转
7. **配置管理** - 环境变量、配置文件
8. **日志设计** - 日志格式、日志级别、日志存储
9. **安全设计** - Binance API 密钥管理、网络隔离
10. **部署与运维** - docker-compose 启动、故障恢复

### Phase 1: 特征工程模块 (features/) ⭐ 优先
> 独立抽象，供 predict / strategy / evaluation 等多模块复用

| 步骤 | 文件 | 内容 |
|------|------|------|
| 1.1 | `base.py` | 特征基类 `BaseFeature`，定义统一接口 `compute(df) -> Series/DataFrame` |
| 1.2 | `technical.py` | 技术指标特征：EMA(9,21,50), RSI(14), MACD, ATR(14), BB, OBV |
| 1.3 | `structural.py` | 结构特征：N周期高低点、整数关口距离、小时/星期时间特征 |
| 1.4 | `registry.py` | 特征注册中心，支持按名称动态获取特征 |
| 1.5 | `pipeline.py` | 特征流水线，批量计算 + 归一化 + 缓存 |

### Phase 2: 预测模块 (predict/)
> 系统核心"大脑"

| 步骤 | 文件 | 内容 |
|------|------|------|
| 2.1 | `config.py` | 预测模块配置（窗口大小、衰减系数、阈值等） |
| 2.2 | `src/label_generator.py` | 标签构造（调用 features/），生成 y_rr, y_sl_pct, y_tp_pct |
| 2.3 | `src/model_trainer.py` | LightGBM + MultiOutputRegressor 训练、评估 |
| 2.4 | `src/inference.py` | 推理服务、后处理校验、输出标准化 JSON |
| 2.5 | `main.py` | 入口脚本 (--mode train / infer) |
| 2.6 | `requirements.txt` + `README.md` | 依赖与文档 |

### Phase 3: 数据服务层 (data/)
> 数据源：**Binance 交易所**（BTCUSDT 永续合约），存储：**SQLite**

| 步骤 | 内容 |
|------|------|
| 3.1 | Binance API 数据获取（使用 `python-binance` 或 `binance-connector`） |
| 3.2 | 历史 K 线数据下载（2019年至今，1H 周期） |
| 3.3 | 实时数据订阅（WebSocket 推送） |
| 3.4 | 数据清洗与时间对齐（整点对齐） |
| 3.5 | SQLite 数据存储（K线数据、交易记录） |

**数据集划分：**
| 数据集 | 时间范围 |
|--------|----------|
| 训练集 (Train) | 2019-01-01 ~ 2025-12-31 |
| 验证集 (Val) | 2026-01-01 ~ 2026-01-31 |
| 测试集 (Test) | 2026-02-01 ~ 2026-02-28 |

### Phase 4: 策略与执行服务 (strategy/)
> 合并策略决策与交易执行，执行层抽象为统一接口

| 步骤 | 内容 |
|------|------|
| 4.1 | 状态机与时钟同步 |
| 4.2 | 信号校验（RR阈值、SL/TP合法性） |
| 4.3 | 仓位管理（固定风险金额 + 动态计算） |
| 4.4 | 持仓监控（价格触发 / 时间触发平仓） |
| 4.5 | 统一交易接口抽象 (open_position, close_position, get_account_info) |
| 4.6 | 回测模式：内存撮合引擎 |
| 4.7 | 模拟盘模式：测试网适配器 |
| 4.8 | 实盘模式：主网适配器 |

### Phase 5: 评估与分析层 (evaluation/)
> **非常驻服务**，按需运行评估脚本

| 步骤 | 内容 |
|------|------|
| 5.1 | 模型评估脚本（方向命中率、盈亏比实现率、止损有效性等） |
| 5.2 | 系统评估脚本（年化收益、最大回撤、夏普比率、盈利因子） |
| 5.3 | 评估报表生成与可视化 |

### Phase 6: 集成与测试
| 步骤 | 内容 |
|------|------|
| 6.1 | 端到端流程测试 |
| 6.2 | 回测验证 |
| 6.3 | 模拟盘部署 |

---

## API 接口设计

### 1. 数据服务 (data-service) - 端口 8001

#### 1.1 获取 K 线数据
```
GET /api/v1/klines
```
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对，如 "BTCUSDT" |
| interval | string | 是 | K线周期，如 "1h" |
| start_time | int | 否 | 开始时间戳(ms) |
| end_time | int | 否 | 结束时间戳(ms) |
| limit | int | 否 | 返回数量，默认 500 |

**响应：**
```json
{
  "code": 0,
  "data": [
    {
      "timestamp": 1704067200000,
      "open": 42000.0,
      "high": 42500.0,
      "low": 41800.0,
      "close": 42300.0,
      "volume": 1234.56
    }
  ]
}
```

#### 1.2 获取最新价格
```
GET /api/v1/ticker
```
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对 |

**响应：**
```json
{
  "code": 0,
  "data": {
    "symbol": "BTCUSDT",
    "price": 42300.0,
    "timestamp": 1704067200000
  }
}
```

#### 1.3 同步历史数据
```
POST /api/v1/sync
```
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对 |
| start_date | string | 是 | 开始日期 "2019-01-01" |
| end_date | string | 否 | 结束日期，默认当前 |

---

### 2. 特征工程服务 (features-service) - 端口 8002

#### 2.1 计算特征
```
POST /api/v1/features/compute
```
**请求体：**
```json
{
  "klines": [
    {"timestamp": 1704067200000, "open": 42000.0, "high": 42500.0, "low": 41800.0, "close": 42300.0, "volume": 1234.56}
  ],
  "feature_names": ["ema_9", "ema_21", "rsi_14", "macd", "atr_14", "bb", "obv"]
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "features": [
      {
        "timestamp": 1704067200000,
        "ema_9": 42100.0,
        "ema_21": 42050.0,
        "rsi_14": 55.3,
        "macd": 120.5,
        "macd_signal": 115.2,
        "macd_hist": 5.3,
        "atr_14": 350.0,
        "bb_upper": 43000.0,
        "bb_middle": 42300.0,
        "bb_lower": 41600.0,
        "obv": 123456.78
      }
    ],
    "feature_columns": ["ema_9", "ema_21", "rsi_14", "macd", "macd_signal", "macd_hist", "atr_14", "bb_upper", "bb_middle", "bb_lower", "obv"]
  }
}
```

#### 2.2 获取可用特征列表
```
GET /api/v1/features/list
```
**响应：**
```json
{
  "code": 0,
  "data": {
    "technical": ["ema_9", "ema_21", "ema_50", "rsi_14", "macd", "atr_14", "bb", "obv"],
    "structural": ["highest_high", "lowest_low", "round_number_dist", "hour", "day_of_week"]
  }
}
```

---

### 3. 预测服务 (predict-service) - 端口 8003
> 内部自动调用 data-service 和 features-service 获取数据

#### 3.1 获取预测信号
```
GET /api/v1/predict
```
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 否 | 交易对，默认 "BTCUSDT" |

**说明：** 服务内部自动：
1. 调用 data-service 获取最新 K 线数据
2. 调用 features-service 计算特征
3. 运行模型推理
4. 返回预测结果

**响应：**
```json
{
  "code": 0,
  "data": {
    "valid": true,
    "signal": "LONG",
    "rr_score": 2.5,
    "entry_price": 42300.0,
    "sl_price": 41500.0,
    "tp_price": 44300.0,
    "sl_pct": 0.019,
    "tp_pct": 0.047,
    "timestamp": 1704067200000
  }
}
```

#### 3.2 触发模型训练
```
POST /api/v1/train
```
**请求体：**
```json
{
  "train_start": "2019-01-01",
  "train_end": "2025-12-31",
  "val_start": "2026-01-01",
  "val_end": "2026-01-31"
}
```

**说明：** 服务内部自动从 data-service 获取训练数据，调用 features-service 计算特征。

**响应：**
```json
{
  "code": 0,
  "data": {
    "model_id": "model_20260302_001",
    "metrics": {
      "direction_accuracy": 0.58,
      "rr_realization": 0.95,
      "mae_sl": 0.005,
      "mae_tp": 0.008
    }
  }
}
```

#### 3.3 获取模型状态
```
GET /api/v1/model/status
```
**响应：**
```json
{
  "code": 0,
  "data": {
    "model_id": "model_20260302_001",
    "loaded": true,
    "train_date": "2026-03-02",
    "feature_count": 25
  }
}
```

---

### 4. 策略与执行服务 (strategy-service) - 主程序
> **不对外提供 API**，作为主程序主动调用其他服务

#### 职责：
1. **时钟调度**：每小时整点触发交易流程
2. **信号获取**：调用 predict-service 获取预测信号
3. **信号校验**：验证 RR 阈值、SL/TP 合法性
4. **仓位管理**：计算开仓数量，管理持仓状态
5. **交易执行**：通过执行层适配器下单（回测/模拟/实盘）
6. **持仓监控**：监听价格变化，触发止损/止盈/时间平仓

#### 内部调用流程：
```
┌─────────────────────────────────────────────────────────┐
│                  strategy-service (主程序)               │
│                                                         │
│  1. 定时触发 (整点)                                      │
│       ↓                                                 │
│  2. GET predict-service/api/v1/predict                  │
│       ↓                                                 │
│  3. 信号校验 (RR >= 阈值？SL/TP 合法？)                   │
│       ↓                                                 │
│  4. 仓位计算 (风险金额 / 止损距离)                        │
│       ↓                                                 │
│  5. 执行交易 (executor.open_position)                    │
│       ↓                                                 │
│  6. 持仓监控 (价格触发 / 时间触发)                        │
│       ↓                                                 │
│  7. 平仓执行 (executor.close_position)                   │
└─────────────────────────────────────────────────────────┘
```

#### 运行模式（通过环境变量配置）：
| 模式 | 环境变量 | 说明 |
|------|----------|------|
| backtest | `MODE=backtest` | 内存撮合引擎，历史数据回测 |
| paper | `MODE=paper` | Binance 测试网 |
| live | `MODE=live` | Binance 主网实盘 |

---

### 通用响应格式

**成功：**
```json
{
  "code": 0,
  "data": { ... }
}
```

**失败：**
```json
{
  "code": 1001,
  "message": "错误描述",
  "data": null
}
```

### 错误码定义
| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 数据不存在 |
| 1003 | 服务内部错误 |
| 2001 | 模型未加载 |
| 2002 | 信号无效 |
| 3001 | 已有持仓 |
| 3002 | 余额不足 |
| 3003 | 交易所 API 错误 |

---

## 预期目录结构
```
btc_quant/
├── docs/
│   └── 系统详细设计.md        # 系统详细设计文档
├── docker-compose.yml         # 容器编排（使用 Docker Network 通信）
├── config.py                  # 全局配置
│
├── features/                  # 特征工程服务 (常驻)
│   ├── Dockerfile
│   ├── __init__.py
│   ├── base.py
│   ├── technical.py
│   ├── structural.py
│   ├── registry.py
│   ├── pipeline.py
│   └── api.py                 # FastAPI 服务接口
│
├── data/                      # 数据服务 (常驻)
│   ├── Dockerfile
│   ├── fetcher.py             # Binance API 数据获取
│   ├── websocket.py           # 实时数据订阅
│   ├── preprocessor.py
│   ├── database.py            # SQLite 数据库操作
│   ├── api.py
│   └── btc_quant.db           # SQLite 数据库文件 (gitignore)
│
├── predict/                   # 预测服务 (常驻)
│   ├── Dockerfile
│   ├── config.py
│   ├── src/
│   │   ├── label_generator.py
│   │   ├── model_trainer.py
│   │   └── inference.py
│   ├── api.py
│   ├── main.py
│   └── models/
│
├── strategy/                  # 策略与执行服务 (常驻)
│   ├── Dockerfile
│   ├── state_machine.py       # 状态机与时钟同步
│   ├── signal_validator.py    # 信号校验
│   ├── position_manager.py    # 仓位管理与持仓监控
│   ├── executor/              # 执行层抽象
│   │   ├── interface.py       # 统一交易接口
│   │   ├── backtest_engine.py # 回测撮合引擎
│   │   ├── paper_adapter.py   # 模拟盘适配器
│   │   └── live_adapter.py    # 实盘适配器
│   └── api.py
│
├── evaluation/                # 评估脚本 (按需运行，非常驻)
│   ├── model_evaluator.py
│   ├── system_evaluator.py
│   └── run_evaluation.py      # 评估入口脚本
│
└── requirements.txt
```

### .gitignore 规则
```
# 敏感数据 - 不提交
*.db                          # SQLite 数据库
btc_quant.db
.env                          # 环境变量（含 API 密钥）

# 模型文件 - 不提交
predict/models/*.pkl
predict/models/*.joblib
*.pkl
*.joblib

# 数据文件 - 不提交
data/storage/
*.parquet
*.csv

# 日志 - 不提交
logs/
*.log

# Python
__pycache__/
*.pyc
.venv/
```

---

## 验证方式
1. **单元测试**：各模块独立测试
2. **回测验证**：使用 **2026-02** 测试集数据回测
3. **模拟盘**：测试网运行 2 周，对比回测结果偏差 ≤ 20%
4. **指标检查**：
   - 模型维度：盈亏比实现率 0.8~1.2，方向命中率 > 55%
   - 系统维度：最大回撤 < 15%，盈利因子 > 1.5
