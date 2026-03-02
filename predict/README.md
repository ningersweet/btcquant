# 预测服务 (Predict Service) 详细设计

## 1. 模块概述

预测服务负责训练和运行机器学习模型，预测未来的盈亏比和止损止盈位置。

### 1.1 核心职责

- 生成训练标签 (y_rr, y_sl_pct, y_tp_pct)
- 训练 LightGBM 多输出回归模型
- 执行推理并进行后处理校验
- 模型管理（保存、加载）

### 1.2 服务端口

- **端口**: 8003
- **健康检查**: `GET /health`

---

## 2. 文件结构

```
predict/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── src/
│   ├── __init__.py
│   ├── label_generator.py   # 标签生成
│   ├── model_trainer.py     # 模型训练
│   └── inference.py         # 推理服务
├── api.py               # FastAPI 接口
├── requirements.txt     # 依赖列表
└── Dockerfile           # Docker 镜像
```

---

## 3. 标签生成

### 3.1 标签定义

对于每个时刻 t，查看未来 window 个周期的数据：

| 标签 | 说明 | 计算方式 |
|------|------|----------|
| y_rr | 盈亏比 | tp_pct / sl_pct × direction |
| y_sl_pct | 止损百分比 | 不利方向的最大波动 / close |
| y_tp_pct | 止盈百分比 | 有利方向的最大波动 / close |
| y_direction | 方向 | 1 (LONG) 或 -1 (SHORT) |

### 3.2 标签生成逻辑

```python
def generate_labels(df: pd.DataFrame, window: int = 1) -> pd.DataFrame:
    for i in range(n - window):
        current_close = df["close"].iloc[i]
        future_slice = df.iloc[i+1:i+1+window]
        
        max_high = future_slice["high"].max()
        min_low = future_slice["low"].min()
        
        upside = max_high - current_close
        downside = current_close - min_low
        
        if upside > downside:
            direction = 1  # LONG
            tp_pct = upside / current_close
            sl_pct = downside / current_close
        else:
            direction = -1  # SHORT
            tp_pct = downside / current_close
            sl_pct = upside / current_close
        
        rr = tp_pct / sl_pct * direction if sl_pct > 0 else 0
```

### 3.3 时间衰减样本权重

```python
def compute_sample_weights(timestamps, decay_lambda=0.00095):
    """Weight = exp(-λ × ΔDays)"""
    latest = timestamps.max()
    delta_days = (latest - timestamps).dt.days
    weights = np.exp(-decay_lambda * delta_days)
    return weights
```

---

## 4. 模型训练

### 4.1 模型架构

```
┌─────────────────────────────────────────────────────────┐
│                  MultiOutputRegressor                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  LGBMReg    │  │  LGBMReg    │  │  LGBMReg    │      │
│  │  (y_rr)     │  │  (y_sl_pct) │  │  (y_tp_pct) │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│  输入: 39 维特征向量                                      │
│  输出: [rr, sl_pct, tp_pct]                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 模型参数

```yaml
predict:
  model:
    n_estimators: 500
    max_depth: 6
    min_child_samples: 50
    subsample: 0.8
    colsample_bytree: 0.8
    learning_rate: 0.05
    random_state: 42
```

### 4.3 训练流程

```python
class ModelTrainer:
    def prepare_data(self, df, feature_columns):
        """准备训练数据"""
        X = df[feature_columns].values
        y = df[["y_rr", "y_sl_pct", "y_tp_pct"]].values
        weights = compute_sample_weights(df["timestamp"])
        return X, y, weights
    
    def train(self, X, y, weights, val_size=0.1):
        """训练模型"""
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_size, shuffle=False
        )
        
        self.model = MultiOutputRegressor(LGBMRegressor(...))
        self.model.fit(X_train, y_train, sample_weight=weights)
        
        return self._compute_metrics(y_val, self.model.predict(X_val))
```

---

## 5. 推理服务

### 5.1 预测结果数据结构

```python
@dataclass
class PredictionResult:
    valid: bool           # 是否通过校验
    signal: str           # LONG / SHORT / NONE
    rr_score: float       # 预测的盈亏比
    entry_price: float    # 入场价格
    sl_price: float       # 止损价格
    tp_price: float       # 止盈价格
    sl_pct: float         # 止损百分比
    tp_pct: float         # 止盈百分比
    timestamp: int        # 时间戳
```

### 5.2 后处理校验

```python
def _validate(self, rr_score, sl_pct, tp_pct, current_price, sl_price, tp_price, signal):
    # 1. RR 阈值检查
    if abs(rr_score) < self.min_rr:
        return False
    
    # 2. 止损范围检查
    if sl_pct < self.min_sl_pct or sl_pct > self.max_sl_pct:
        return False
    
    # 3. 价格逻辑检查
    if signal == "LONG":
        if not (sl_price < current_price < tp_price):
            return False
    else:  # SHORT
        if not (tp_price < current_price < sl_price):
            return False
    
    return True
```

### 5.3 推理流程

```
┌─────────────────┐
│   特征向量       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   模型预测       │
│ [rr, sl, tp]    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   确定方向       │
│ rr > 0 ? LONG   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   计算价格       │
│ SL/TP 价格      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   后处理校验     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│ 通过  │  │ 失败  │
│SIGNAL│  │ NONE │
└──────┘  └──────┘
```

---

## 6. API 接口

### 6.1 获取预测信号

```
GET /api/v1/predict?symbol=BTCUSDT
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "valid": true,
    "signal": "LONG",
    "rr_score": 2.35,
    "entry_price": 62500.0,
    "sl_price": 62000.0,
    "tp_price": 63675.0,
    "sl_pct": 0.008,
    "tp_pct": 0.0188,
    "timestamp": 1709251200000
  }
}
```

### 6.2 触发模型训练

```
POST /api/v1/train
```

**请求体**:

```json
{
  "train_start": "2023-01-01",
  "train_end": "2024-01-01",
  "val_start": "2024-01-01",
  "val_end": "2024-03-01"
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "model_id": "model_20240301_120000",
    "metrics": {
      "direction_accuracy": 0.58,
      "mae_rr": 0.45,
      "mae_sl": 0.0023,
      "mae_tp": 0.0034
    }
  }
}
```

### 6.3 获取模型状态

```
GET /api/v1/model/status
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "loaded": true,
    "feature_count": 39,
    "model_path": "/app/models"
  }
}
```

### 6.4 加载模型

```
POST /api/v1/model/load?model_id=model_20240301_120000
```

---

## 7. 配置项

```yaml
predict:
  host: "0.0.0.0"
  port: 8003
  model_path: "/app/models"
  data_service_url: "http://data-service:8001"
  features_service_url: "http://features-service:8002"
  
  model:
    n_estimators: 500
    max_depth: 6
    min_child_samples: 50
    subsample: 0.8
    colsample_bytree: 0.8
    learning_rate: 0.05
    random_state: 42
  
  label:
    window_size: 1
    decay_lambda: 0.00095
  
  validation:
    min_rr: 1.5
    max_sl_pct: 0.05
    min_sl_pct: 0.001
```

---

## 8. 评估指标

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| direction_accuracy | 方向准确率 | sign(y_pred) == sign(y_true) |
| mae_rr | RR 平均绝对误差 | mean(abs(rr_pred - rr_true)) |
| mae_sl | SL 平均绝对误差 | mean(abs(sl_pred - sl_true)) |
| mae_tp | TP 平均绝对误差 | mean(abs(tp_pred - tp_true)) |
