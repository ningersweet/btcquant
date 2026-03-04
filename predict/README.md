# 预测服务 (Predict Service)

基于TCN（时间卷积网络）的比特币价格预测服务。

## 目录结构

```
predict/
├── src/                    # 核心代码库
│   ├── label_generator.py  # 标签生成器（多核并行）
│   ├── tcn_model.py        # TCN模型架构
│   ├── model_trainer.py    # 模型训练器
│   ├── data_loader.py      # 数据加载器
│   ├── backtest.py         # 回测引擎
│   ├── inference.py        # 推理引擎
│   └── hyperparameter_tuner.py  # 超参数优化
├── training/               # 训练脚本
│   ├── train.py           # 主训练脚本
│   ├── train_with_notification.py  # 带通知的训练
│   └── post_training.py   # 训练后处理
├── api/                    # API服务
│   └── api.py             # FastAPI接口
├── scripts/                # 工具脚本
│   ├── sync_data.py       # 数据同步
│   └── check_model.py     # 模型检查
├── docs/                   # 文档
│   ├── README.md          # 服务文档
│   ├── QUICKSTART.md      # 快速开始
│   ├── 模型设计.md         # 模型设计文档
│   ├── 特征工程.md         # 特征工程文档
│   └── TRAINING_AUTOMATION.md  # 训练自动化文档
├── models/                 # 本地模型（已废弃，使用storage/models/）
├── logs/                   # 本地日志（已废弃，使用storage/logs/）
├── config.py              # 配置管理
├── requirements.txt       # Python依赖
└── Dockerfile            # Docker镜像
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

配置文件位于项目根目录：`../config.yaml`

```bash
# 从根目录
cp config.yaml.example config.yaml
vim config.yaml
```

### 3. 训练模型

```bash
# 使用btcquant命令（推荐）
btcquant train start --gpu

# 或本地训练
cd training
python train.py --mode cache
```

### 4. 启动API服务

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
from src.label_generator import LabelGenerator

generator = LabelGenerator(n_jobs=-1)  # 使用所有CPU核心
df_with_labels = generator.generate_labels(df)
```

### 模型训练

```python
from src.model_trainer import ModelTrainer
from src.tcn_model import TCNModel

model = TCNModel(...)
trainer = ModelTrainer(model, ...)
history = trainer.train(train_df, val_df, epochs=100)
```

### 模型推理

```python
from src.inference import load_inference_model

inference = load_inference_model(model_dir, use_onnx=True)
prediction = inference.predict(klines)
```

### 回测

```python
from src.backtest import Backtester

backtester = Backtester(model, ...)
metrics = backtester.backtest(test_df)
```

## 配置说明

所有配置在根目录的 `config.yaml` 中：

```yaml
predict:
  # 标签生成
  label:
    alpha: 0.0015
    gamma: 0.0040
    beta: 0.0025
    theta_min: 0.0100
    K: 12
  
  # 模型架构
  model:
    channels: 64
    num_layers: 8
    dropout: 0.2
  
  # 训练参数
  training:
    batch_size: 128
    learning_rate: 0.001
    epochs: 100
    device: "cuda"
```

## 训练模式

### 1. Cache模式（推荐）
使用预先准备的数据缓存，速度最快：
```bash
python training/train.py --mode cache
```

### 2. Full模式
从数据服务加载完整数据：
```bash
python training/train.py --mode full
```

### 3. Incremental模式
在已有模型基础上继续训练：
```bash
python training/train.py --mode incremental --base-model ../storage/models/tcn_xxx/best_model.pt
```

## 日志和存储

### 日志位置
所有日志统一存放在：`../storage/logs/`

```bash
# 查看训练日志
tail -f ../storage/logs/training.log
```

### 数据缓存
数据缓存统一存放在：`../storage/cache/`

### 模型存储
训练好的模型存放在：`../storage/models/`

## API接口

### 健康检查
```bash
curl http://localhost:8000/health
```

### 预测
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "klines": [...]
  }'
```

## 性能优化

### 标签生成
- 使用多核并行处理（5-8倍提速）
- 自动检测CPU核心数

### 模型训练
- 支持GPU加速
- 批量训练优化
- 早停机制

### 模型推理
- ONNX Runtime加速（3-5倍提速）
- 批量推理支持

## 开发指南

### 添加新特征
1. 在 `src/` 中添加特征提取代码
2. 更新 `data_loader.py`
3. 更新模型输入维度

### 修改模型架构
1. 编辑 `src/tcn_model.py`
2. 更新 `config.yaml` 中的模型参数
3. 重新训练模型

### 自定义训练流程
1. 参考 `training/train.py`
2. 使用 `ModelTrainer` 类
3. 自定义损失函数和优化器

## 故障排查

### 训练失败
```bash
# 查看日志
tail -100 ../storage/logs/training.log

# 检查配置
cat ../config.yaml

# 检查GPU
nvidia-smi
```

### API无响应
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs predict-service
```

## 更多文档

- [快速开始](docs/QUICKSTART.md)
- [模型设计](docs/模型设计.md)
- [特征工程](docs/特征工程.md)
- [训练自动化](docs/TRAINING_AUTOMATION.md)
- [训练报告](docs/TRAINING_REPORT.md)

## 相关链接

- [项目主页](../README.md)
- [项目规范](../PROJECT_STANDARDS.md)
- [项目规则](../PROJECT_RULES.md)
