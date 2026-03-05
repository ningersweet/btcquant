# 预测服务 (Predict Service)

基于TCN（时间卷积网络）的比特币价格预测服务。

## 目录结构

```
predict/
├── models/                 # 模型模块
│   ├── tcn_model.py       # TCN模型架构
│   ├── model_trainer.py   # 模型训练器
│   └── __init__.py
├── data/                   # 数据模块
│   ├── data_loader.py     # 数据加载
│   ├── label_generator.py # 标签生成（多核并行）
│   └── __init__.py
├── evaluation/             # 评估模块
│   ├── backtest.py        # 回测引擎
│   ├── inference.py       # 推理引擎
│   └── __init__.py
├── utils/                  # 工具模块
│   ├── hyperparameter_tuner.py  # 超参数优化
│   └── __init__.py
├── training/               # 训练脚本
│   ├── train.py           # 主训练脚本
│   ├── train_with_notification.py  # 带通知的训练
│   └── post_training.py   # 训练后处理
├── api/                    # API服务
│   └── api.py             # FastAPI接口
├── scripts/                # 工具脚本
│   ├── sync_data.py       # 数据同步
│   └── check_model.py     # 模型检查
├── config.py              # 配置管理
├── requirements.txt       # Python依赖
└── Dockerfile            # Docker镜像
```

## 快速开始

详细的快速开始指南请查看：[项目README](../README.md)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 训练模型

```bash
# 使用btcquant命令（推荐）
btcquant train start --gpu

# 或本地训练
cd training
python train.py --mode cache
```

### 启动API服务

```bash
# 使用Docker
docker-compose up -d predict-service

# 或直接运行
cd api
uvicorn api:app --host 0.0.0.0 --port 8000
```

## 核心功能

### 标签生成（多核并行）

```python
from data import LabelGenerator

generator = LabelGenerator(n_jobs=-1)  # 使用所有CPU核心
df_with_labels = generator.generate_labels(df)
```

### 模型训练

```python
from models import TCNModel, ModelTrainer

model = TCNModel(...)
trainer = ModelTrainer(model, ...)
history = trainer.train(train_df, val_df, epochs=100)
```

### 模型推理

```python
from evaluation import load_inference_model

inference = load_inference_model(model_dir, use_onnx=True)
prediction = inference.predict(klines)
```

### 回测

```python
from evaluation import BacktestEngine

backtester = BacktestEngine(model, ...)
metrics = backtester.backtest(test_df)
```

## 配置说明

所有配置在根目录的 `config.yaml` 中，详见：[项目规范](../PROJECT.md)

## 训练模式

### 1. Cache模式（推荐）
```bash
python training/train.py --mode cache
```

### 2. Full模式
```bash
python training/train.py --mode full
```

### 3. Incremental模式
```bash
python training/train.py --mode incremental --base-model ../storage/models/tcn_xxx/best_model.pt
```

## 日志和存储

### 日志位置
```bash
tail -f ../storage/logs/training.log
```

### 数据缓存
`../storage/cache/`

### 模型存储
`../storage/models/`

## API接口

### 健康检查
```bash
curl http://localhost:8000/health
```

### 预测
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "klines": [...]}'
```

## 性能优化

- 标签生成：多核并行（5-8倍提速）
- 模型训练：GPU加速
- 模型推理：ONNX Runtime（3-5倍提速）

## 相关文档

- [项目主页](../README.md)
- [命令使用](../COMMANDS.md)
- [项目规范](../PROJECT.md)
- [系统设计](../docs/系统设计.md)
- [模型训练详解](../docs/模型训练与评估详细文档.md)
