# BTC量化交易系统

基于TCN（时间卷积网络）的比特币量化交易系统，支持自动标签生成、模型训练、回测和实盘推理。

## 🎯 项目特点

- ✅ **TCN模型架构**：时间卷积网络，专为时序数据设计
- ✅ **自动标签生成**：基于数学公式的标签生成器
- ✅ **完整训练流程**：数据获取、特征工程、模型训练、回测评估
- ✅ **GPU/CPU兼容**：支持GPU训练，CPU推理
- ✅ **增量训练**：支持模型增量更新
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
│   - 标签生成                         │
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

### 1. 部署到服务器

```bash
# 克隆代码（服务器上）
cd /root/workspace
git clone https://github.com/ningersweet/btcquant.git
cd btcquant

# 或使用一键部署脚本（本地）
./deploy.sh init
```

### 2. 启动数据服务

```bash
# 启动数据服务
docker-compose up -d data-service

# 准备训练数据
./prepare_training_data.sh
```

### 3. 训练模型

```bash
# 快速训练（3个月数据，约11分钟）
cd predict
python train_fast.py

# 完整训练（需要GPU，约30-60分钟）
python train_cached.py
```

### 4. 启动推理服务

```bash
# 启动推理服务
docker-compose up -d predict-service

# 测试API
curl http://localhost:8000/health
```

## 📚 文档导航

### 核心文档
- **[项目设计.md](./项目设计.md)** - 系统整体设计
- **[DEPLOY_QUICKSTART.md](./DEPLOY_QUICKSTART.md)** - 快速部署指南 ⭐
- **[GIT_DEPLOY_GUIDE.md](./GIT_DEPLOY_GUIDE.md)** - Git部署详细说明

### 训练相关
- **[GPU_TRAINING_GUIDE.md](./GPU_TRAINING_GUIDE.md)** - GPU训练完整指南
- **[predict/TRAINING_REPORT.md](./predict/TRAINING_REPORT.md)** - 训练结果报告
- **[predict/模型设计.md](./predict/模型设计.md)** - TCN模型设计
- **[predict/特征工程.md](./predict/特征工程.md)** - 特征工程说明

### 模块文档
- **[data/README.md](./data/README.md)** - 数据服务说明
- **[predict/README.md](./predict/README.md)** - 预测服务说明
- **[features/README.md](./features/README.md)** - 特征工程说明
- **[strategy/README.md](./strategy/README.md)** - 交易策略说明

### 详细文档（docs/）
- **[系统设计.md](./docs/系统设计.md)** - 系统架构设计
- **[特征工程详细文档.md](./docs/特征工程详细文档.md)** - 特征工程详解
- **[模型训练与评估详细文档.md](./docs/模型训练与评估详细文档.md)** - 训练评估详解
- **[超参数优化指南.md](./docs/超参数优化指南.md)** - 超参数调优
- **[部署指南.md](./docs/部署指南.md)** - 生产部署指南

## 🛠️ 技术栈

- **深度学习**: PyTorch, TCN
- **数据处理**: Pandas, NumPy
- **API服务**: FastAPI, Uvicorn
- **数据存储**: SQLite
- **容器化**: Docker, Docker Compose
- **版本控制**: Git

## 📦 项目结构

```
btcquant/
├── data/                   # 数据服务
│   ├── api.py             # API接口
│   ├── service.py         # 数据服务
│   ├── database.py        # 数据库操作
│   └── fetcher.py         # 数据获取
├── predict/               # 预测服务
│   ├── src/              # 核心模块
│   │   ├── tcn_model.py  # TCN模型
│   │   ├── label_generator.py  # 标签生成
│   │   ├── data_loader.py      # 数据加载
│   │   ├── model_trainer.py    # 模型训练
│   │   ├── backtest.py         # 回测引擎
│   │   └── inference.py        # 推理服务
│   ├── train_cached.py   # 缓存训练脚本
│   ├── train_fast.py     # 快速训练脚本
│   └── train_incremental.py  # 增量训练脚本
├── features/              # 特征工程
├── strategy/              # 交易策略
├── evaluation/            # 评估模块
├── common/                # 公共模块
├── docs/                  # 详细文档
├── deploy.sh             # 部署脚本
├── prepare_training_data.sh  # 数据准备脚本
├── setup_gpu_env.sh      # GPU环境初始化
└── docker-compose.yml    # Docker配置
```

## 🎯 使用场景

### 场景1：数据服务器（你的服务器 47.236.94.252）
```bash
# 启动数据服务
./deploy.sh data

# 准备训练数据
./deploy.sh prepare

# 查看状态
./deploy.sh status
```

### 场景2：GPU训练服务器
```bash
# 初始化GPU环境
./setup_gpu_env.sh

# 启动训练
./deploy_gpu_training.sh

# 监控训练
tail -f predict/training_gpu.log
```

### 场景3：推理服务器
```bash
# 启动推理服务
docker-compose up -d predict-service

# 测试推理
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "interval": "5m"}'
```

## 📊 训练结果

- **验证集准确率**: 81.1%（快速训练，3个月数据）
- **模型参数**: 40,518个（快速模型）/ 208,774个（完整模型）
- **训练时间**: 11分钟（CPU，3个月数据）/ 30-60分钟（GPU，全量数据）

## 🔧 常用命令

```bash
# 部署相关
./deploy.sh init      # 首次部署
./deploy.sh update    # 更新代码
./deploy.sh data      # 启动数据服务
./deploy.sh prepare   # 准备训练数据
./deploy.sh status    # 查看状态

# 训练相关
cd predict
python train_fast.py              # 快速训练
python train_cached.py            # 完整训练
python train_incremental.py       # 增量训练

# 服务相关
docker-compose up -d              # 启动所有服务
docker-compose ps                 # 查看服务状态
docker-compose logs -f            # 查看日志
```

## 💰 成本估算

### 数据服务器（常驻）
- 配置：2核4G
- 成本：¥80/月

### GPU训练服务器（按需）
- 配置：T4 16GB（阿里云抢占式）
- 成本：¥2-3/小时
- 单次训练：¥1-2元

### 总成本
- 月度：¥88/月（每周训练1次）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

- GitHub: https://github.com/ningersweet/btcquant
- 服务器: 47.236.94.252

---

**快速开始：** `./deploy.sh init` 🚀
