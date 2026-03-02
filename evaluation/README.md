# 评估模块 (Evaluation Module) 详细设计

## 1. 模块概述

评估模块负责计算交易系统和预测模型的各项性能指标。

### 1.1 核心职责

- 系统评估（胜率、盈亏比、最大回撤、Sharpe 等）
- 模型评估（方向准确率、RR 实现率等）
- 生成评估报告

---

## 2. 文件结构

```
evaluation/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── system_evaluator.py  # 系统评估
├── model_evaluator.py   # 模型评估
└── requirements.txt     # 依赖列表
```

---

## 3. 系统评估指标

### 3.1 指标定义

```python
@dataclass
class SystemMetrics:
    total_trades: int       # 总交易次数
    win_rate: float         # 胜率
    profit_factor: float    # 盈亏比
    total_pnl: float        # 总盈亏
    max_drawdown: float     # 最大回撤金额
    max_drawdown_pct: float # 最大回撤百分比
    sharpe_ratio: float     # 夏普比率
    cagr: float             # 年化收益率
    avg_trade_pnl: float    # 平均每笔盈亏
    avg_win: float          # 平均盈利
    avg_loss: float         # 平均亏损
    sl_rate: float          # 止损触发率
    tp_rate: float          # 止盈触发率
    time_rate: float        # 超时触发率
```

### 3.2 计算公式

| 指标 | 公式 |
|------|------|
| 胜率 | wins / total_trades |
| 盈亏比 | total_profit / total_loss |
| 最大回撤 | max(peak - equity) |
| 夏普比率 | mean(returns) × √(365×24) / std(returns) |
| CAGR | (final / initial)^(1/years) - 1 |

### 3.3 评估函数

```python
def evaluate_system(trades_df: pd.DataFrame, initial_balance: float) -> SystemMetrics:
    # 基础统计
    total_trades = len(trades_df)
    wins = trades_df[trades_df["pnl"] > 0]
    losses = trades_df[trades_df["pnl"] <= 0]
    win_rate = len(wins) / total_trades
    
    # 盈亏比
    total_profit = wins["pnl"].sum()
    total_loss = abs(losses["pnl"].sum())
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    # 权益曲线与回撤
    equity_curve = initial_balance + trades_df["pnl"].cumsum()
    peak = equity_curve.expanding().max()
    drawdown = peak - equity_curve
    max_drawdown = drawdown.max()
    max_drawdown_pct = max_drawdown / peak.max()
    
    # 夏普比率
    returns = trades_df["pnl_pct"]
    sharpe_ratio = returns.mean() * np.sqrt(365 * 24) / returns.std()
    
    # 出场原因统计
    exit_reasons = trades_df["exit_reason"].value_counts()
    sl_rate = exit_reasons.get("SL", 0) / total_trades
    tp_rate = exit_reasons.get("TP", 0) / total_trades
    time_rate = exit_reasons.get("TIME", 0) / total_trades
    
    return SystemMetrics(...)
```

---

## 4. 模型评估指标

### 4.1 指标定义

```python
@dataclass
class ModelMetrics:
    direction_accuracy: float  # 方向准确率
    rr_realization: float      # RR 实现率
    sl_effectiveness: float    # 止损有效性
    tp_coverage: float         # 止盈覆盖率
    mae_sl: float              # 止损 MAE
    mae_tp: float              # 止盈 MAE
```

### 4.2 计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| 方向准确率 | sign(pred) == sign(actual) | 预测方向与实际方向一致的比例 |
| RR 实现率 | actual_rr / predicted_rr | 实际盈亏比与预测盈亏比的比值 |
| 止损有效性 | - | 止损价格的合理性评估 |
| 止盈覆盖率 | - | 达到止盈价格的比例 |
| MAE | mean(abs(pred - actual)) | 平均绝对误差 |

### 4.3 评估函数

```python
def evaluate_model(predictions_df: pd.DataFrame) -> ModelMetrics:
    # 方向准确率
    direction_pred = np.sign(predictions_df["y_rr_pred"])
    direction_actual = np.sign(predictions_df["y_rr_actual"])
    direction_accuracy = np.mean(direction_pred == direction_actual)
    
    # RR 实现率
    valid_rr = predictions_df[predictions_df["y_rr_pred"] != 0]
    rr_realization = (valid_rr["y_rr_actual"] / valid_rr["y_rr_pred"]).mean()
    
    # MAE
    mae_sl = np.mean(np.abs(
        predictions_df["y_sl_pct_pred"] - predictions_df["y_sl_pct_actual"]
    ))
    mae_tp = np.mean(np.abs(
        predictions_df["y_tp_pct_pred"] - predictions_df["y_tp_pct_actual"]
    ))
    
    return ModelMetrics(...)
```

---

## 5. 使用示例

### 5.1 系统评估

```python
from evaluation import evaluate_system

# 获取交易记录
trades_df = backtest_engine.get_trades_df()

# 评估系统
metrics = evaluate_system(trades_df, initial_balance=10000)

print(f"总交易次数: {metrics.total_trades}")
print(f"胜率: {metrics.win_rate:.2%}")
print(f"盈亏比: {metrics.profit_factor:.2f}")
print(f"最大回撤: {metrics.max_drawdown_pct:.2%}")
print(f"夏普比率: {metrics.sharpe_ratio:.2f}")
```

### 5.2 模型评估

```python
from evaluation import evaluate_model

# 准备预测数据
predictions_df = pd.DataFrame({
    "y_rr_pred": [...],
    "y_rr_actual": [...],
    "y_sl_pct_pred": [...],
    "y_sl_pct_actual": [...],
    "y_tp_pct_pred": [...],
    "y_tp_pct_actual": [...]
})

# 评估模型
metrics = evaluate_model(predictions_df)

print(f"方向准确率: {metrics.direction_accuracy:.2%}")
print(f"RR 实现率: {metrics.rr_realization:.2f}")
print(f"止损 MAE: {metrics.mae_sl:.6f}")
print(f"止盈 MAE: {metrics.mae_tp:.6f}")
```

---

## 6. 配置项

```yaml
evaluation:
  risk_free_rate: 0.02        # 无风险利率
  trading_days_per_year: 365  # 每年交易天数
  hours_per_day: 24           # 每天交易小时数
```

---

## 7. 评估报告示例

```
================== 系统评估报告 ==================

【基础统计】
总交易次数: 156
盈利交易: 89 (57.05%)
亏损交易: 67 (42.95%)

【盈亏分析】
总盈亏: +2,345.67 USDT
平均每笔: +15.04 USDT
平均盈利: +42.35 USDT
平均亏损: -21.23 USDT
盈亏比: 1.87

【风险指标】
最大回撤: 456.78 USDT (4.12%)
夏普比率: 1.85
年化收益率: 28.5%

【出场统计】
止损触发: 42 (26.92%)
止盈触发: 89 (57.05%)
超时触发: 25 (16.03%)

=============================================
```
