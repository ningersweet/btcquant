# BTC Quant - 预测服务

基于TCN（时间卷积网络）的比特币合约量化交易预测服务。

## 功能特性

- **TCN模型架构**：8层残差空洞卷积，感受野覆盖24小时
- **智能标签生成**：基于极值时序的双向缓冲机制
- **完整训练流程**：数据获取、标签生成、模型训练、回测评估
- **ONNX加速推理**：比PyTorch原生CPU推理快3-5倍
- **回测评估系统**：收益率、最大回撤、夏普比率等指标

## 目录结构

```
predict/
├── src/
│   ├── label_generator.py    # 标签生成器
│   ├── tcn_model.py          # TCN模型架构
│   ├── data_loader.py        # 数据加载器
│   ├── model_trainer.py      # 模型训练器
│   ├── backtest.py           # 回测引擎
│   └── inference.py          # 推理服务
├── models/                   # 模型保存目录
├── config.py                 # 配置管理
├── train.py                  # 训练脚本
├── .env.example              # 环境变量示例
└── requirements.txt          # 依赖包
```

## 快速开始

### 1. 安装依赖

```bash
cd predict
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置超参数
```

### 3. 启动数据服务

```bash
cd ..
docker-compose up -d data-service
```

### 4. 训练模型

```bash
python train.py
```

训练完成后，模型会保存在 `models/tcn_YYYYMMDD_HHMMSS/` 目录下。

## 配置说明

所有超参数都在 `.env` 文件中配置，主要参数包括：

### 标签生成参数

- `LABEL_ALPHA`: 入场缓冲系数（默认0.0015，即0.15%）
- `LABEL_GAMMA`: 止盈缓冲系数（默认0.0040，即0.40%）
- `LABEL_BETA`: 止损缓冲系数（默认0.0025，即0.25%）
- `LABEL_THETA_MIN`: 最小净利阈值（默认0.0100，即1.00%）
- `LABEL_K`: 预测窗口长度（默认12根K线，即1小时）

### 模型架构参数

- `MODEL_INPUT_DIM`: 输入特征维度（5维OHLCV）
- `MODEL_CHANNELS`: TCN通道数（默认64）
- `MODEL_NUM_LAYERS`: TCN层数（默认8）
- `MODEL_KERNEL_SIZE`: 卷积核大小（默认3）
- `MODEL_DROPOUT`: Dropout率（默认0.2）

### 训练参数

- `TRAIN_BATCH_SIZE`: 批次大小（默认128）
- `TRAIN_LEARNING_RATE`: 学习率（默认0.001）
- `TRAIN_EPOCHS`: 训练轮数（默认100）
- `TRAIN_EARLY_STOPPING_PATIENCE`: 早停耐心值（默认15）
- `TRAIN_LAMBDA_CLS`: 分类损失权重（默认1.0）
- `TRAIN_LAMBDA_REG`: 回归损失权重（默认0.5）

## 模型输出

### 分类输出
- 3个类别：Hold（持有）、Long（做多）、Short（做空）
- 输出概率分布

### 回归输出
- `offset`: 入场偏移率（相对于当前价格）
- `tp_dist`: 止盈距离率（相对于入场价）
- `sl_dist`: 止损距离率（相对于入场价）

## 回测指标

训练完成后会自动在测试集上运行回测，输出以下指标：

- **总交易次数**：回测期间的交易数量
- **胜率**：盈利交易占比
- **总收益率**：资金增长百分比
- **最大回撤**：资金曲线最大下跌幅度
- **夏普比率**：风险调整后收益
- **盈利因子**：总盈利/总亏损
- **时间止损率**：因时间到期而平仓的比例

## 推理使用

```python
from pathlib import Path
from src.inference import load_inference_model
import pandas as pd

# 加载模型
model_dir = Path('models/tcn_20240101_120000')
inference = load_inference_model(model_dir, use_onnx=True)

# 准备数据（最近288根5分钟K线）
klines = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 预测
prediction = inference.predict(klines)
print(prediction)

# 计算订单价格
current_price = klines.iloc[-1]['close']
order = inference.calculate_order_prices(prediction, current_price)
if order:
    print(f"开仓方向: {order['side']}")
    print(f"入场价: {order['entry_price']}")
    print(f"止盈价: {order['tp_price']}")
    print(f"止损价: {order['sl_price']}")
    print(f"盈亏比: {order['rr_ratio']:.2f}")
```

## 注意事项

1. **数据要求**：训练需要从2019年至今的完整5分钟K线数据
2. **计算资源**：TCN模型在CPU上训练较慢，建议使用GPU加速
3. **避免过拟合**：严格使用时间序列划分，不要在测试集上调参
4. **未来数据泄露**：标签生成严格避免使用未来数据
5. **配置安全**：`.env` 文件包含敏感参数，不要提交到git

## 性能优化

- 使用ONNX Runtime进行推理，速度提升3-5倍
- 批量推理时增大batch_size
- 生产环境建议使用量化模型（INT8）

## 故障排查

### 数据服务连接失败
```bash
# 检查数据服务是否运行
docker-compose ps

# 查看日志
docker-compose logs data-service
```

### 内存不足
- 减小 `TRAIN_BATCH_SIZE`
- 减小 `DATA_WINDOW_SIZE`
- 使用梯度累积

### 训练不收敛
- 调整学习率 `TRAIN_LEARNING_RATE`
- 检查标签分布是否平衡
- 增加训练数据量

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 实现TCN模型架构
- 完整的训练和回测流程
- ONNX导出支持
