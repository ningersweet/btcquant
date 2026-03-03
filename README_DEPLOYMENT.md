# 🎉 BTC量化交易系统 - 完整部署方案

## ✅ 已完成的工作

### 1. 核心功能实现
- ✅ TCN模型架构（时间卷积网络）
- ✅ 标签生成器（基于数学公式）
- ✅ 数据加载器（滚动窗口、标准化）
- ✅ 模型训练器（早停、学习率调度）
- ✅ 回测引擎（完整交易模拟）
- ✅ 推理服务（PyTorch/ONNX）
- ✅ 数据服务（SQLite + Binance API）

### 2. 训练验证
- ✅ 快速训练完成（11分钟，3个月数据）
- ✅ 验证集准确率：81.1%
- ✅ 模型参数：40,518个
- ✅ 数据缓存机制（68万条数据）

### 3. 部署方案
- ✅ CPU推理支持（GPU训练的模型可在CPU推理）
- ✅ 增量训练脚本
- ✅ GPU环境初始化脚本
- ✅ 服务器一键部署脚本
- ✅ 完整部署文档

## 📦 部署包内容

```
btc_quant_deploy.tar.gz (19MB)
├── predict/                    # 预测服务
│   ├── src/                   # 核心模块
│   ├── train_cached.py        # 缓存训练脚本
│   ├── train_incremental.py   # 增量训练
│   ├── api.py                 # 推理API
│   └── config.py              # 配置管理
├── data/                       # 数据服务
├── common/                     # 公共模块
├── docker-compose.yml          # Docker配置
├── setup_gpu_env.sh           # GPU环境初始化
├── deploy_gpu_training.sh     # 训练启动脚本
├── prepare_training_data.sh   # 数据准备脚本
└── 文档/
    ├── DEPLOYMENT_QUICKSTART.md
    ├── GPU_TRAINING_GUIDE.md
    └── SERVER_DEPLOYMENT_GUIDE.md
```

## 🚀 快速开始（3步）

### 步骤1：部署数据服务器

```bash
# 在本地Mac执行
cd /Users/lemonshwang/project/btc_quant
./deploy_to_server.sh YOUR_DATA_SERVER_IP data

# 自动完成：
# - 上传部署包
# - 启动数据服务
# - 准备训练数据（68万条，约150MB）
```

### 步骤2：传输数据到GPU服务器

```bash
# 方法1：直接传输
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
    root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 方法2：通过本地
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl ./
scp training_data_cache.pkl root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl
```

### 步骤3：GPU训练

```bash
# 部署GPU环境
./deploy_to_server.sh YOUR_GPU_SERVER_IP gpu

# SSH登录并启动训练
ssh root@YOUR_GPU_SERVER_IP
cd ~/btc_quant
./deploy_gpu_training.sh

# 监控训练（30-60分钟）
tail -f predict/training_gpu.log
```

## 📊 架构方案

### 推荐架构：三服务器分离

```
┌─────────────────────────────┐
│   数据服务器（常驻）          │
│   - 2核4G，¥80/月            │
│   - Docker数据服务           │
│   - 68万条历史数据           │
└─────────────────────────────┘
              ↓ 数据缓存
┌─────────────────────────────┐
│   GPU训练服务器（按需）       │
│   - T4 16GB，¥2-3/小时       │
│   - 抢占式实例               │
│   - 训练30-60分钟后释放      │
└─────────────────────────────┘
              ↓ 训练好的模型
┌─────────────────────────────┐
│   推理服务器（常驻）          │
│   - 2核4G，¥80/月            │
│   - CPU推理服务              │
│   - 实盘交易                 │
└─────────────────────────────┘
```

**月度成本：¥88/月**
- 数据服务器：¥80
- GPU训练（每周1次）：¥8

## ⏱️ 时间预估

| 步骤 | 时间 |
|------|------|
| 部署数据服务器 | 5分钟 |
| 准备训练数据 | 2-5分钟 |
| 传输数据到GPU | 1-3分钟 |
| 初始化GPU环境 | 5-10分钟（首次） |
| GPU训练 | 30-60分钟 |
| **总计** | **45-85分钟** |

## 💡 GPU性能对比

| GPU型号 | 显存 | 价格 | 训练时间 | 推荐度 |
|---------|------|------|----------|--------|
| T4 | 16GB | ¥2-3/时 | 30-60分钟 | ⭐⭐⭐⭐⭐ |
| A10 | 24GB | ¥4-6/时 | 20-30分钟 | ⭐⭐⭐⭐ |
| V100 | 16GB | ¥6-8/时 | 25-35分钟 | ⭐⭐⭐ |

**推荐：T4 抢占式实例**（性价比最高）

## 📝 关键命令

```bash
# === 本地Mac ===
# 一键部署到数据服务器
./deploy_to_server.sh DATA_SERVER_IP data

# 一键部署到GPU服务器
./deploy_to_server.sh GPU_SERVER_IP gpu

# === 数据服务器 ===
cd ~/btc_quant
./prepare_training_data.sh              # 准备数据
docker-compose ps                       # 检查服务

# === GPU服务器 ===
cd ~/btc_quant
./setup_gpu_env.sh                      # 初始化（首次）
./deploy_gpu_training.sh                # 启动训练
tail -f predict/training_gpu.log        # 监控日志
nvidia-smi                              # 监控GPU

# === 下载模型 ===
scp -r root@GPU:~/btc_quant/predict/models/tcn_* ./models/
```

## 🎯 工作流程

### 首次部署（约1小时）
1. 部署数据服务器（5分钟）
2. 准备训练数据（5分钟）
3. 部署GPU服务器（10分钟）
4. 传输数据（3分钟）
5. GPU训练（30-60分钟）
6. 下载模型（2分钟）

### 后续增量训练（约1小时）
1. 更新训练数据（2分钟）
2. 启动GPU实例（1分钟）
3. 传输数据（3分钟）
4. 增量训练（30-60分钟）
5. 下载新模型（2分钟）
6. 释放GPU实例

## 📚 文档索引

- **DEPLOYMENT_QUICKSTART.md** - 快速部署指南（本文档）
- **GPU_TRAINING_GUIDE.md** - GPU训练详细指南
- **SERVER_DEPLOYMENT_GUIDE.md** - 服务器部署完整说明
- **GPU_QUICKSTART.md** - GPU快速上手

## ✅ 检查清单

### 部署前
- [ ] 已创建阿里云账号
- [ ] 已准备好服务器IP
- [ ] 本地已有部署包（btc_quant_deploy.tar.gz）

### 数据服务器
- [ ] Docker已安装
- [ ] 数据服务正常运行
- [ ] 训练数据已准备（training_data_cache.pkl）

### GPU服务器
- [ ] GPU驱动正常（nvidia-smi）
- [ ] CUDA环境正确
- [ ] PyTorch可用GPU
- [ ] 数据缓存已传输

### 训练完成
- [ ] 模型已保存
- [ ] 回测指标正常
- [ ] 模型已下载到本地

## 🔧 故障排查

### 问题1：数据服务连接失败
```bash
docker-compose ps
docker-compose restart data-service
curl http://localhost:8001/health
```

### 问题2：GPU不可用
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### 问题3：训练超时
```bash
# 检查数据缓存是否存在
ls -lh predict/data_cache.pkl

# 如果不存在，从数据服务器传输
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
    predict/data_cache.pkl
```

## 🎊 总结

**已完成：**
- ✅ 完整的TCN模型系统
- ✅ 训练验证通过（81.1%准确率）
- ✅ GPU训练环境脚本
- ✅ 服务器部署方案
- ✅ 完整文档

**下一步：**
1. 部署到服务器
2. GPU训练完整模型
3. 部署推理服务
4. 实盘测试

**所有准备工作已完成，随时可以开始部署！** 🚀

---

**快速开始命令：**
```bash
./deploy_to_server.sh YOUR_DATA_SERVER_IP data
```
