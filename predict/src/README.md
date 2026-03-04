# 核心代码库 (src)

预测服务的核心代码，按功能模块组织。

## 目录结构

```
src/
├── models/         # 模型相关
│   ├── tcn_model.py       # TCN模型架构
│   ├── model_trainer.py   # 模型训练器
│   └── __init__.py
├── data/           # 数据相关
│   ├── data_loader.py     # 数据加载
│   ├── label_generator.py # 标签生成（多核并行）
│   └── __init__.py
├── evaluation/     # 评估相关
│   ├── backtest.py        # 回测引擎
│   ├── inference.py       # 推理引擎
│   └── __init__.py
├── utils/          # 工具函数
│   ├── hyperparameter_tuner.py  # 超参数优化
│   └── __init__.py
└── __init__.py     # 主入口
```

## 模块说明

### 1. models/ - 模型模块

**TCN模型架构 (tcn_model.py)**
- 时间卷积网络实现
- 残差连接和空洞卷积
- 支持多层堆叠

**模型训练器 (model_trainer.py)**
- 训练循环管理
- 早停机制
- 损失函数和优化器
- 模型保存和加载

**使用示例：**
```python
from src.models import TCNModel, ModelTrainer

model = TCNModel(
    input_dim=5,
    num_channels=64,
    num_layers=8
)

trainer = ModelTrainer(model, batch_size=128)
history = trainer.train(train_df, val_df, epochs=100)
```

### 2. data/ - 数据模块

**数据加载器 (data_loader.py)**
- 从数据服务加载K线
- 数据集划分
- 序列生成
- 数据预处理

**标签生成器 (label_generator.py)**
- 基于数学公式的标签生成
- 多核并行处理（5-8倍提速）
- 支持自定义参数

**使用示例：**
```python
from src.data import load_klines_from_service, LabelGenerator

# 加载数据
df = load_klines_from_service(
    symbol='BTCUSDT',
    interval='5m',
    start_date='2019-01-01'
)

# 生成标签
generator = LabelGenerator(n_jobs=-1)
df_labeled = generator.generate_labels(df)
```

### 3. evaluation/ - 评估模块

**回测引擎 (backtest.py)**
- 历史数据回测
- 性能指标计算
- 交易模拟

**推理引擎 (inference.py)**
- 模型推理
- ONNX加速
- 订单价格计算

**使用示例：**
```python
from src.evaluation import Backtester, load_inference_model

# 回测
backtester = Backtester(model)
metrics = backtester.backtest(test_df)

# 推理
inference = load_inference_model(model_dir, use_onnx=True)
prediction = inference.predict(klines)
```

### 4. utils/ - 工具模块

**超参数优化 (hyperparameter_tuner.py)**
- 基于Optuna的超参数搜索
- 自动化调优
- 结果保存

**使用示例：**
```python
from src.utils import tune_hyperparameters

best_params = tune_hyperparameters(
    train_df, val_df,
    n_trials=50,
    device='cuda'
)
```

## 导入方式

### 方式1: 从子模块导入（推荐）
```python
from src.models import TCNModel, ModelTrainer
from src.data import LabelGenerator
from src.evaluation import Backtester
```

### 方式2: 从主模块导入
```python
from src import (
    TCNModel,
    ModelTrainer,
    LabelGenerator,
    Backtester
)
```

### 方式3: 直接导入
```python
from src.models.tcn_model import TCNModel
from src.data.label_generator import LabelGenerator
```

## 设计原则

### 1. 单一职责
每个模块只负责一个功能领域：
- models/ 只关注模型
- data/ 只关注数据
- evaluation/ 只关注评估
- utils/ 提供通用工具

### 2. 高内聚低耦合
- 模块内部高度相关
- 模块之间依赖最小
- 便于独立测试和维护

### 3. 可复用性
- 所有模块都可以独立使用
- 提供清晰的接口
- 避免硬编码

### 4. 易于扩展
- 新增模型放在 models/
- 新增数据处理放在 data/
- 新增评估方法放在 evaluation/
- 新增工具放在 utils/

## 开发指南

### 添加新模型
1. 在 `models/` 创建新文件
2. 继承基础模型类
3. 在 `models/__init__.py` 中导出
4. 更新文档

### 添加新数据处理
1. 在 `data/` 创建新文件
2. 实现数据处理逻辑
3. 在 `data/__init__.py` 中导出
4. 添加单元测试

### 添加新评估方法
1. 在 `evaluation/` 创建新文件
2. 实现评估逻辑
3. 在 `evaluation/__init__.py` 中导出
4. 提供使用示例

## 测试

每个模块都应该有对应的测试：

```
tests/
├── test_models.py
├── test_data.py
├── test_evaluation.py
└── test_utils.py
```

运行测试：
```bash
pytest tests/
```

## 性能优化

### 数据处理
- 使用numpy数组而非pandas
- 多核并行处理
- 缓存中间结果

### 模型训练
- GPU加速
- 混合精度训练
- 梯度累积

### 模型推理
- ONNX Runtime加速
- 批量推理
- 模型量化

## 依赖关系

```
models/
  └── 依赖: torch, numpy

data/
  └── 依赖: pandas, numpy, multiprocessing

evaluation/
  └── 依赖: models/, data/, torch, onnxruntime

utils/
  └── 依赖: models/, data/, optuna
```

## 相关文档

- [训练脚本](../training/README.md)
- [API服务](../api/README.md)
- [项目规范](../../PROJECT_STANDARDS.md)
