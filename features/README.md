# 特征工程服务 (Features Service) 详细设计

## 1. 模块概述

特征工程服务负责从 K 线数据中提取技术指标和结构特征，为预测模型提供输入。

### 1.1 核心职责

- 计算技术指标 (EMA, RSI, MACD, ATR, BB, OBV)
- 提取结构特征 (高低点, 整数关口, 时间, K线形态)
- 特征注册与管理
- 特征流水线批量计算

### 1.2 服务端口

- **端口**: 8002
- **健康检查**: `GET /health`

---

## 2. 文件结构

```
features/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── base.py              # 特征基类
├── technical.py         # 技术指标特征
├── structural.py        # 结构特征
├── registry.py          # 特征注册中心
├── pipeline.py          # 特征流水线
├── api.py               # FastAPI 接口
├── requirements.txt     # 依赖列表
└── Dockerfile           # Docker 镜像
```

---

## 3. 特征基类设计

### 3.1 BaseFeature 抽象类

```python
class BaseFeature(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """特征名称"""
        pass
    
    @property
    @abstractmethod
    def output_columns(self) -> List[str]:
        """输出列名列表"""
        pass
    
    @property
    def required_columns(self) -> List[str]:
        """所需的输入列"""
        return ["open", "high", "low", "close", "volume"]
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算特征"""
        pass
```

---

## 4. 技术指标特征

### 4.1 EMA (指数移动平均)

```python
class EMAFeature(BaseFeature):
    """指数移动平均特征"""
    periods: tuple = (9, 21, 50)
    
    # 输出列: ema_9, ema_21, ema_50
    # 计算: (EMA - close) / close (相对距离)
```

### 4.2 RSI (相对强弱指数)

```python
class RSIFeature(BaseFeature):
    """相对强弱指数特征"""
    period: int = 14
    
    # 输出列: rsi_14
    # 计算: RSI / 100 (归一化到 0-1)
```

### 4.3 MACD

```python
class MACDFeature(BaseFeature):
    """MACD 指标特征"""
    fast: int = 12
    slow: int = 26
    signal: int = 9
    
    # 输出列: macd, macd_signal, macd_hist
    # 计算: 各值 / close (相对价格)
```

### 4.4 ATR (平均真实波幅)

```python
class ATRFeature(BaseFeature):
    """平均真实波幅特征"""
    period: int = 14
    
    # 输出列: atr_14
    # 计算: ATR / close (相对波动率)
```

### 4.5 Bollinger Bands (布林带)

```python
class BollingerBandsFeature(BaseFeature):
    """布林带特征"""
    period: int = 20
    std: float = 2.0
    
    # 输出列: bb_upper, bb_middle, bb_lower, bb_width, bb_pct
```

### 4.6 OBV (能量潮)

```python
class OBVFeature(BaseFeature):
    """能量潮特征"""
    ema_period: int = 20
    
    # 输出列: obv_norm, obv_ema_norm
    # 计算: 归一化到 0-1 范围
```

---

## 5. 结构特征

### 5.1 高低点特征

```python
class HighLowFeature(BaseFeature):
    """N 周期高低点特征"""
    periods: tuple = (5, 10, 20)
    
    # 输出列: highest_high_5, lowest_low_5, ...
    # 计算: (highest - close) / close, (close - lowest) / close
```

### 5.2 整数关口特征

```python
class RoundNumberFeature(BaseFeature):
    """整数关口距离特征"""
    base: int = 1000  # 1000 USDT 为一个关口
    
    # 输出列: round_dist_pct, round_above_pct, round_below_pct
    # 计算: 到最近整数关口的距离百分比
```

### 5.3 时间特征

```python
class TimeFeature(BaseFeature):
    """时间特征"""
    
    # 输出列: hour, day_of_week, is_weekend, hour_sin, hour_cos
    # 计算: 周期性编码
```

### 5.4 收益率特征

```python
class ReturnFeature(BaseFeature):
    """收益率特征"""
    periods: tuple = (1, 5, 10)
    
    # 输出列: return_1, return_5, return_10
    # 计算: pct_change(periods)
```

### 5.5 K 线形态特征

```python
class CandleFeature(BaseFeature):
    """K 线形态特征"""
    
    # 输出列: body_ratio, upper_shadow, lower_shadow, is_bullish
```

### 5.6 波动率特征

```python
class VolatilityFeature(BaseFeature):
    """波动率特征"""
    periods: tuple = (5, 10, 20)
    
    # 输出列: volatility_5, volatility_10, volatility_20
    # 计算: 收益率的滚动标准差
```

---

## 6. 特征注册中心

```python
class FeatureRegistry:
    def register(self, name: str, feature_class: Type[BaseFeature]) -> None
    def get(self, name: str) -> Optional[Type[BaseFeature]]
    def create(self, name: str, **kwargs) -> Optional[BaseFeature]
    def list_features(self) -> Dict[str, List[str]]
    def get_all_names(self) -> List[str]

# 默认注册的特征
TECHNICAL_FEATURES = ["ema", "rsi", "macd", "atr", "bb", "obv"]
STRUCTURAL_FEATURES = ["highlow", "round_number", "time", "return", "candle", "volatility"]
```

---

## 7. 特征流水线

```python
class FeaturePipeline:
    def __init__(self, feature_names: Optional[List[str]] = None):
        """初始化流水线"""
        self.feature_names = feature_names or registry.get_all_names()
    
    def compute(self, df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
        """计算所有特征"""
        result = df.copy()
        for feature in self.features:
            result = feature.compute(result)
        if drop_na:
            result = result.dropna()
        return result
    
    def get_feature_columns(self) -> List[str]:
        """获取所有特征列名"""
        columns = []
        for feature in self.features:
            columns.extend(feature.output_columns)
        return columns
```

---

## 8. API 接口

### 8.1 计算特征

```
POST /api/v1/features/compute
```

**请求体**:

```json
{
  "klines": [
    {
      "timestamp": 1709251200000,
      "open": 62500.0,
      "high": 62800.0,
      "low": 62300.0,
      "close": 62600.0,
      "volume": 1234.56
    }
  ],
  "feature_names": ["ema", "rsi", "macd"]
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "features": [
      {
        "timestamp": 1709251200000,
        "ema_9": 0.0012,
        "ema_21": -0.0023,
        "rsi_14": 0.65,
        "macd": 0.0015
      }
    ],
    "feature_columns": ["ema_9", "ema_21", "ema_50", "rsi_14", "macd", "macd_signal", "macd_hist"]
  }
}
```

### 8.2 获取可用特征列表

```
GET /api/v1/features/list
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "technical": ["ema", "rsi", "macd", "atr", "bb", "obv"],
    "structural": ["highlow", "round_number", "time", "return", "candle", "volatility"]
  }
}
```

### 8.3 获取特征列名

```
GET /api/v1/features/columns?feature_names=ema,rsi
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "columns": ["ema_9", "ema_21", "ema_50", "rsi_14"],
    "count": 4
  }
}
```

---

## 9. 配置项

```yaml
features:
  host: "0.0.0.0"
  port: 8002
  data_service_url: "http://data-service:8001"
  
  technical:
    ema_periods: [9, 21, 50]
    rsi_period: 14
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    atr_period: 14
    bb_period: 20
    bb_std: 2.0
    obv_ema_period: 20
  
  structural:
    lookback_periods: [5, 10, 20]
    return_periods: [1, 5, 10]
    round_number_base: 1000
```

---

## 10. 特征列表汇总

| 类别 | 特征名 | 输出列数 | 说明 |
|------|--------|----------|------|
| 技术指标 | ema | 3 | EMA 相对距离 |
| 技术指标 | rsi | 1 | RSI 归一化值 |
| 技术指标 | macd | 3 | MACD 三线 |
| 技术指标 | atr | 1 | ATR 相对值 |
| 技术指标 | bb | 5 | 布林带指标 |
| 技术指标 | obv | 2 | OBV 归一化 |
| 结构特征 | highlow | 6 | 高低点距离 |
| 结构特征 | round_number | 3 | 整数关口距离 |
| 结构特征 | time | 5 | 时间编码 |
| 结构特征 | return | 3 | 收益率 |
| 结构特征 | candle | 4 | K线形态 |
| 结构特征 | volatility | 3 | 波动率 |
| **总计** | 12 | **39** | |
