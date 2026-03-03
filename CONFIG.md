# 配置文件说明

## 📋 配置文件结构

### 主配置文件
- **config.yaml** - 系统主配置文件（不提交到Git）
- **config.yaml.example** - 配置文件示例（提交到Git）

### 模块配置文件
- **predict/.env** - 预测服务环境变量（不提交到Git）
- **predict/.env.example** - 环境变量示例（提交到Git）

## 🚀 快速开始

### 1. 创建配置文件

```bash
# 复制主配置文件
cp config.yaml.example config.yaml

# 复制预测服务配置
cp predict/.env.example predict/.env
```

### 2. 修改配置

编辑 `config.yaml`，根据实际情况修改：

```yaml
data:
  interval: "5m"  # K线间隔
  database:
    db_path: "/app/data_storage/btc_quant.db"  # 数据库路径

predict:
  data_service_url: "http://localhost:8001"  # 数据服务地址
  training:
    device: "cpu"  # 或 "cuda"（如果有GPU）
```

编辑 `predict/.env`：

```bash
# 数据参数
DATA_START_DATE=2019-01-01
DATA_INTERVAL=5m

# 训练参数
TRAIN_DEVICE=cpu  # 或 cuda
TRAIN_BATCH_SIZE=256
TRAIN_EPOCHS=50
```

## 📊 配置说明

### config.yaml 配置项

#### 数据服务 (data)
- `symbol`: 交易对（默认：BTCUSDT）
- `interval`: K线间隔（5m, 15m, 1h等）
- `port`: 服务端口（默认：8001）
- `database.db_path`: 数据库文件路径

#### 预测服务 (predict)
- `port`: 服务端口（默认：8000）
- `model.channels`: TCN通道数（默认：64）
- `model.num_layers`: TCN层数（默认：8）
- `training.device`: 训练设备（cpu或cuda）
- `training.batch_size`: 批次大小（默认：256）

#### 标签生成 (predict.label)
- `alpha`: 入场缓冲系数（默认：0.0015）
- `gamma`: 止盈缓冲系数（默认：0.0040）
- `beta`: 止损缓冲系数（默认：0.0025）
- `theta_min`: 最小净利阈值（默认：0.0100）
- `K`: 预测窗口长度（默认：12）

### predict/.env 配置项

#### 数据参数
```bash
DATA_WINDOW_SIZE=288      # 输入窗口长度（24小时）
DATA_INTERVAL=5m          # K线间隔
DATA_START_DATE=2019-01-01  # 训练数据起始日期
DATA_TRAIN_RATIO=0.7      # 训练集比例
DATA_VAL_RATIO=0.15       # 验证集比例
DATA_TEST_RATIO=0.15      # 测试集比例
```

#### 模型参数
```bash
MODEL_INPUT_DIM=5         # 输入特征维度
MODEL_CHANNELS=64         # TCN通道数
MODEL_NUM_LAYERS=8        # TCN层数
MODEL_KERNEL_SIZE=3       # 卷积核大小
MODEL_DROPOUT=0.2         # Dropout率
```

#### 训练参数
```bash
TRAIN_BATCH_SIZE=256      # 批次大小
TRAIN_LEARNING_RATE=0.001 # 学习率
TRAIN_EPOCHS=50           # 训练轮数
TRAIN_EARLY_STOPPING_PATIENCE=10  # 早停耐心值
TRAIN_DEVICE=cpu          # 训练设备（cpu或cuda）
```

#### 标签生成参数
```bash
LABEL_ALPHA=0.0015        # 入场缓冲系数
LABEL_GAMMA=0.0040        # 止盈缓冲系数
LABEL_BETA=0.0025         # 止损缓冲系数
LABEL_THETA_MIN=0.0100    # 最小净利阈值
LABEL_K=12                # 预测窗口长度
```

## 🔒 安全说明

### 不应提交到Git的文件
- ❌ config.yaml - 包含实际配置
- ❌ predict/.env - 包含实际配置
- ❌ *.db - 数据库文件
- ❌ models/* - 训练好的模型

### 应提交到Git的文件
- ✅ config.yaml.example - 配置示例
- ✅ predict/.env.example - 环境变量示例
- ✅ .gitignore - Git忽略规则

## 📝 配置优先级

1. **环境变量** - 最高优先级
2. **predict/.env** - 预测服务配置
3. **config.yaml** - 系统配置
4. **代码默认值** - 最低优先级

## 🎯 不同环境的配置

### 开发环境
```yaml
data:
  database:
    db_path: "./data_storage/btc_quant.db"
predict:
  data_service_url: "http://localhost:8001"
  training:
    device: "cpu"
    epochs: 10  # 快速测试
```

### 生产环境
```yaml
data:
  database:
    db_path: "/app/data_storage/btc_quant.db"
predict:
  data_service_url: "http://data-service:8001"
  training:
    device: "cuda"
    epochs: 50
```

### GPU训练环境
```bash
# predict/.env
TRAIN_DEVICE=cuda
TRAIN_BATCH_SIZE=1024
TRAIN_EPOCHS=50
```

## 🔧 常见问题

### Q: 如何切换到GPU训练？
```bash
# 修改 predict/.env
TRAIN_DEVICE=cuda
TRAIN_BATCH_SIZE=1024  # GPU可以用更大的batch size
```

### Q: 如何修改数据起始日期？
```bash
# 修改 predict/.env
DATA_START_DATE=2019-01-01
```

### Q: 如何调整模型大小？
```bash
# 修改 predict/.env
MODEL_CHANNELS=32  # 减小模型
MODEL_NUM_LAYERS=6
```

---

**记住：永远不要将 config.yaml 和 .env 文件提交到Git！** 🔒
