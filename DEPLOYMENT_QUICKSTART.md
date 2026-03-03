# 🚀 服务器部署快速指南

## 📦 已准备好的文件

- ✅ `btc_quant_deploy.tar.gz` (19MB) - 完整部署包
- ✅ `deploy_to_server.sh` - 一键部署脚本
- ✅ `prepare_training_data.sh` - 数据准备脚本
- ✅ `setup_gpu_env.sh` - GPU环境初始化
- ✅ `deploy_gpu_training.sh` - 训练启动脚本

## 🎯 三步完成部署

### 方案A：数据服务器 + GPU服务器（推荐）

#### 步骤1：部署数据服务器

```bash
# 在本地Mac执行
cd /Users/lemonshwang/project/btc_quant

# 一键部署到数据服务器
./deploy_to_server.sh YOUR_DATA_SERVER_IP data

# 脚本会自动：
# 1. 上传部署包
# 2. 启动数据服务
# 3. 准备训练数据（约2-5分钟）
```

#### 步骤2：传输数据到GPU服务器

```bash
# 方法1：直接传输
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
    root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 方法2：通过本地中转
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl ./
scp training_data_cache.pkl root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl
```

#### 步骤3：在GPU服务器上训练

```bash
# 部署GPU环境
./deploy_to_server.sh YOUR_GPU_SERVER_IP gpu

# SSH登录GPU服务器
ssh root@YOUR_GPU_SERVER_IP

# 启动训练
cd ~/btc_quant
./deploy_gpu_training.sh

# 监控训练（30-60分钟）
tail -f predict/training_gpu.log
```

### 方案B：单服务器部署（测试用）

```bash
# 一键部署所有内容
./deploy_to_server.sh YOUR_SERVER_IP all

# SSH登录
ssh root@YOUR_SERVER_IP

# 如果是GPU服务器，启动训练
cd ~/btc_quant
./deploy_gpu_training.sh

# 如果是普通服务器，准备数据
cd ~/btc_quant
./prepare_training_data.sh
```

## 📋 详细步骤说明

### 1. 在数据服务器上准备训练数据

```bash
# SSH登录数据服务器
ssh root@YOUR_DATA_SERVER_IP

# 进入项目目录
cd ~/btc_quant

# 检查数据服务状态
docker-compose ps
curl http://localhost:8001/health

# 准备训练数据
./prepare_training_data.sh

# 输出：
# ✓ 共获取 681,959 条K线数据
# ✓ 缓存文件大小: 150-200 MB
# ✓ 文件位置: ~/btc_quant/training_data_cache.pkl
```

### 2. 传输数据到GPU服务器

```bash
# 在数据服务器上执行
cd ~/btc_quant
scp training_data_cache.pkl root@GPU_SERVER_IP:~/

# 在GPU服务器上移动文件
ssh root@GPU_SERVER_IP
mv ~/training_data_cache.pkl ~/btc_quant/predict/data_cache.pkl
```

### 3. 在GPU服务器上训练

```bash
# SSH登录GPU服务器
ssh root@GPU_SERVER_IP

# 初始化环境（首次运行）
cd ~/btc_quant
./setup_gpu_env.sh
# 预计时间：5-10分钟

# 重新登录激活环境
exit
ssh root@GPU_SERVER_IP

# 确认数据文件
ls -lh ~/btc_quant/predict/data_cache.pkl

# 启动训练
cd ~/btc_quant
./deploy_gpu_training.sh

# 实时监控
tail -f predict/training_gpu.log

# 另开一个终端监控GPU
ssh root@GPU_SERVER_IP
watch -n 5 nvidia-smi
```

## 🔍 验证部署

### 数据服务器检查

```bash
# 检查Docker服务
docker-compose ps

# 测试数据API
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/status?symbol=BTCUSDT&interval=5m

# 检查数据缓存
ls -lh training_data_cache.pkl
```

### GPU服务器检查

```bash
# 检查GPU
nvidia-smi

# 检查CUDA
nvcc --version

# 检查PyTorch
conda activate btc_quant
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"

# 检查数据文件
ls -lh predict/data_cache.pkl
```

## ⏱️ 时间预估

| 步骤 | 时间 |
|------|------|
| 上传部署包 | 1-2分钟 |
| 初始化GPU环境 | 5-10分钟（首次） |
| 准备训练数据 | 2-5分钟 |
| 传输数据文件 | 1-3分钟 |
| GPU训练 | 30-60分钟 |
| **总计** | **40-80分钟** |

## 💰 成本估算

### 阿里云配置

**数据服务器（常驻）：**
- 配置：2核4G，50GB
- 价格：¥80/月

**GPU服务器（按需）：**
- 配置：ecs.gn6i-c4g1.xlarge (T4 16GB)
- 价格：¥2-3/小时（抢占式）
- 单次训练：¥1-2元

**月度成本：**
- 数据服务器：¥80
- GPU训练（每周1次）：¥8
- **总计：¥88/月**

## 🎯 快速命令参考

```bash
# === 本地Mac ===
# 创建部署包
./create_deployment_package.sh

# 部署到数据服务器
./deploy_to_server.sh DATA_SERVER_IP data

# 部署到GPU服务器
./deploy_to_server.sh GPU_SERVER_IP gpu

# === 数据服务器 ===
cd ~/btc_quant
./prepare_training_data.sh                    # 准备数据
docker-compose ps                             # 检查服务
scp training_data_cache.pkl root@GPU:~/       # 传输数据

# === GPU服务器 ===
cd ~/btc_quant
./setup_gpu_env.sh                            # 初始化（首次）
./deploy_gpu_training.sh                      # 启动训练
tail -f predict/training_gpu.log              # 监控日志
nvidia-smi                                    # 监控GPU

# === 下载模型 ===
scp -r root@GPU:~/btc_quant/predict/models/tcn_* ./models/
```

## 📞 常见问题

### Q1: 数据服务连接失败
```bash
# 检查Docker
docker-compose ps
docker-compose logs data-service

# 重启服务
docker-compose restart data-service
```

### Q2: GPU环境初始化失败
```bash
# 检查CUDA
nvidia-smi
nvcc --version

# 重新安装PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Q3: 数据传输太慢
```bash
# 使用压缩
tar -czf data.tar.gz training_data_cache.pkl
scp data.tar.gz root@GPU:~/
ssh root@GPU "tar -xzf data.tar.gz"
```

## ✅ 下一步

1. ✅ 运行 `./deploy_to_server.sh` 部署到服务器
2. ✅ 在数据服务器上准备训练数据
3. ✅ 传输数据到GPU服务器
4. ✅ 启动GPU训练
5. ✅ 等待30-60分钟完成训练
6. ✅ 下载模型部署到推理服务

---

**所有脚本已准备就绪，随时可以开始部署！** 🚀
