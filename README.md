# BTC量化交易系统

基于TCN（时间卷积网络）的比特币量化交易系统，支持自动标签生成、模型训练、回测和实盘推理。

## 🎯 项目特点

- ✅ **TCN模型架构**：时间卷积网络，专为时序数据设计
- ✅ **自动标签生成**：基于数学公式的标签生成器，支持多核并行
- ✅ **完整训练流程**：数据获取、特征工程、模型训练、回测评估
- ✅ **GPU/CPU兼容**：支持GPU训练，CPU推理
- ✅ **训练自动化**：训练完成自动传输模型、发送邮件通知
- ✅ **统一命令行**：btcquant命令管理所有操作
- ✅ **Docker部署**：完整的Docker化部署方案

## 📊 系统架构

```
┌─────────────────────────────────────┐
│   数据服务 (data/)                   │
│   - Binance API数据获取              │
│   - SQLite数据存储                   │
│   - RESTful API                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   预测服务 (predict/)                │
│   - TCN模型训练                      │
│   - 标签生成（多核并行）              │
│   - 模型推理                         │
│   - 回测引擎                         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   交易策略 (strategy/)               │
│   - 信号生成                         │
│   - 风险管理                         │
│   - 仓位管理                         │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Docker & Docker Compose
- GPU服务器（训练用，可选）

### 1. 安装btcquant命令

```bash
# 克隆代码
git clone https://github.com/ningersweet/btcquant.git
cd btcquant

# 添加到PATH（可选）
chmod +x btcquant
sudo ln -s $(pwd)/btcquant /usr/local/bin/btcquant

# 查看帮助
btcquant help
```

### 2. 部署到CPU服务器

```bash
# 首次部署
btcquant server init cpu

# 启动数据服务
btcquant data start

# 准备训练数据
btcquant data prepare
```

### 3. GPU训练

```bash
# 初始化GPU环境（首次）
btcquant gpu setup

# 同步训练数据
btcquant train sync-data

# 启动训练（后台运行）
btcquant train start --gpu

# 查看训练状态
btcquant train status
btcquant train logs

# 训练完成后会自动：
# - 传输模型到CPU服务器
# - 发送邮件通知
```

### 4. 本地开发

```bash
# 安装依赖
cd predict
pip install -r requirements.txt

# 本地训练（使用缓存数据）
cd training
python train.py --mode cache

# 查看训练日志
tail -f ../storage/logs/training.log
```

## 📖 文档

### 快速入门
- [命令使用指南](COMMANDS.md) - 所有btcquant命令详解 ⭐
- [项目规范](PROJECT.md) - 开发规范和工作流程
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码

### 详细文档
- [文档导航](docs/INDEX.md) - 完整文档索引
- [系统设计](docs/系统设计.md) - 系统架构设计
- [部署指南](docs/部署指南.md) - 生产环境部署
- [特征工程](docs/特征工程详细文档.md) - 特征设计详解
- [模型训练](docs/模型训练与评估详细文档.md) - 训练流程详解
- [超参数优化](docs/超参数优化指南.md) - 调优方法

### 模块文档
- [预测服务](predict/README.md) - TCN模型和训练
- [数据服务](data/README.md) - 数据获取和存储
- [策略服务](strategy/README.md) - 交易策略
- [特征工程](features/README.md) - 特征计算
- [评估模块](evaluation/README.md) - 回测评估

## 🛠️ 常用命令

### 服务器管理

```bash
btcquant server init cpu          # 首次部署到CPU服务器
btcquant server update gpu        # 更新GPU服务器代码
btcquant server status cpu        # 查看服务器状态
btcquant server shell gpu         # SSH登录GPU服务器
btcquant server logs cpu data-service  # 查看数据服务日志
```

### 数据管理

```bash
btcquant data start               # 启动数据服务
btcquant data prepare             # 准备训练数据
btcquant data status              # 查看数据服务状态
```

### 训练管理

```bash
btcquant gpu setup                # 初始化GPU环境（首次必须）
btcquant train start --gpu        # 启动GPU训练
btcquant train status             # 查看训练状态
btcquant train logs               # 查看训练日志
btcquant train stop               # 停止训练
btcquant train sync-data          # 同步数据到GPU服务器
btcquant train sync-model         # 同步模型到CPU服务器
```

### Docker管理

```bash
btcquant docker up                # 启动所有容器
btcquant docker ps                # 查看容器状态
btcquant docker logs data-service # 查看容器日志
btcquant docker monitor           # 监控容器资源
```

## 📁 项目结构

```
btc_quant/
├── btcquant                    # 统一命令行工具
├── storage/                    # 统一存储目录
│   ├── logs/                  # 所有日志文件
│   ├── cache/                 # 数据缓存文件
│   └── models/                # 训练好的模型
├── common/                     # 公共模块
├── data/                       # 数据服务
│   ├── src/                   # 数据服务源码
│   └── Dockerfile             # 数据服务镜像
├── predict/                    # 预测服务
│   ├── src/                   # 核心代码库
│   │   ├── label_generator.py # 标签生成器（多核并行）
│   │   ├── tcn_model.py       # TCN模型
│   │   ├── model_trainer.py   # 模型训练器
│   │   └── backtest.py        # 回测引擎
│   ├── training/              # 训练脚本
│   │   ├── train.py          # 主训练脚本
│   │   ├── train_with_notification.py  # 带通知训练
│   │   └── post_training.py  # 训练后处理
│   ├── api/                   # API服务
│   │   └── api.py            # FastAPI接口
│   ├── scripts/               # 工具脚本
│   ├── docs/                  # 文档
│   └── config.py              # 配置管理
├── strategy/                   # 策略服务
├── docs/                      # 项目文档
├── config.yaml                # 统一配置文件
├── docker-compose.yml         # Docker编排
├── PROJECT_STANDARDS.md       # 项目规范
├── PROJECT_RULES.md           # 项目规则
└── README.md                  # 本文件
```

## 🔧 配置

### YAML配置文件

复制配置文件并修改：

```bash
# 根目录配置
cp config.yaml.example config.yaml
vim config.yaml
```

**⚠️ 重要：配置管理规则**

- ✅ `config.yaml` 以本地环境为准
- ✅ 修改后通过 `btcquant train sync-config` 同步到服务器
- ❌ 禁止直接在服务器上修改配置
- ❌ 禁止提交 `config.yaml` 到 Git

详细规则：[配置管理快速参考](docs/配置管理快速参考.md)

### 邮件通知配置

训练完成后自动发送邮件通知。

**在 config.yaml 中配置（推荐）**：

```yaml
notification:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    smtp_user: "your_email@gmail.com"
    smtp_password: "your_app_password"
```

详细配置说明和常见邮箱设置见 [config.yaml.example](config.yaml.example)

### 主要配置项

```yaml
predict:
  # 标签生成参数
  label:
    alpha: 0.0015              # 入场缓冲系数
    gamma: 0.0040              # 止盈缓冲系数
    beta: 0.0025               # 止损缓冲系数
    theta_min: 0.0100          # 最小净利阈值

  # 模型架构
  model:
    channels: 64               # TCN通道数
    num_layers: 8              # TCN层数

  # 训练参数
  training:
    batch_size: 128            # 批次大小
    learning_rate: 0.001       # 学习率
    epochs: 100                # 训练轮数
    device: cuda               # 设备（cuda/cpu）
```

## 🎓 训练模式

### 1. 缓存模式（推荐）

使用预先准备的数据缓存，速度最快：

```bash
cd training
python train.py --mode cache
```

### 2. 完整模式

从数据服务加载完整数据：

```bash
cd training
python train.py --mode full
```

### 3. 增量模式

在已有模型基础上继续训练：

```bash
cd training
python train.py --mode incremental --base-model ../storage/models/tcn_xxx/best_model.pt
```

## 📊 性能指标

### 标签生成性能

| 数据量 | 单核耗时 | 8核耗时 | 提速比 |
|--------|---------|---------|--------|
| 10万 | 8分钟 | 1.5分钟 | 5.3x |
| 50万 | 42分钟 | 6分钟 | 7.0x |
| 100万 | 85分钟 | 11分钟 | 7.7x |

### 训练性能

- GPU训练：约1-2小时（100万样本，50 epochs）
- CPU训练：约8-12小时（100万样本，50 epochs）

## 🤝 贡献

欢迎提交Issue和Pull Request！详见 [贡献指南](CONTRIBUTING.md)

## 📄 许可证

MIT License

## 📮 联系方式

- GitHub: https://github.com/ningersweet/btcquant
- Email: your_email@example.com

## 🙏 致谢

- Binance API
- PyTorch
- TCN论文作者

---

**快速开始：** `btcquant help` 🚀
