# GPU训练环境部署指南

## 📋 前置要求

- 阿里云GPU实例（推荐：ecs.gn6i-c4g1.xlarge）
- Ubuntu 20.04 + CUDA 11.8 镜像
- 至少50GB系统盘

## 🚀 快速部署（3步完成）

### 步骤1：部署代码到GPU服务器

```bash
# SSH登录GPU服务器
ssh gpu_server

# 克隆代码（首次）
cd ~
git clone https://github.com/ningersweet/btcquant.git btc_quant
cd btc_quant
```

### 步骤2：初始化GPU环境

```bash
# 运行环境初始化脚本（首次运行，约5-10分钟）
chmod +x setup_gpu_env.sh
./setup_gpu_env.sh

# 重新登录以激活环境
exit
ssh gpu_server
```

### 步骤3：启动训练

```bash
# 快速部署训练
cd ~/btc_quant
chmod +x deploy_gpu_training.sh
./deploy_gpu_training.sh

# 或手动启动
cd ~/btc_quant/predict
conda activate btc_quant
python train_cached.py > training_gpu.log 2>&1 &
```

## 📊 监控训练

### 实时查看训练日志
```bash
tail -f ~/btc_quant/predict/training_gpu.log
```

### 监控GPU使用率
```bash
watch -n 5 nvidia-smi
```

### 查看训练进度
```bash
# 查看epoch进度
grep "Epoch" ~/btc_quant/predict/training_gpu.log | tail -10

# 查看最佳模型
grep "Best model saved" ~/btc_quant/predict/training_gpu.log
```

## ⏱️ 预计时间

| GPU型号 | Batch Size | 每Epoch | 20 Epochs | 50 Epochs |
|---------|-----------|---------|-----------|-----------|
| T4 16GB | 1024 | 1.5分钟 | 30分钟 | 1.2小时 |
| A10 24GB | 2048 | 1分钟 | 20分钟 | 50分钟 |
| V100 16GB | 1024 | 1.2分钟 | 24分钟 | 1小时 |

## 💰 成本控制

### 使用抢占式实例
```bash
# 在阿里云控制台创建实例时：
# 1. 选择"抢占式实例"
# 2. 出价策略：市场价格的60%
# 3. 成本：¥2-3/小时（vs 按量¥7-9/小时）
```

### 训练完成后自动关机
```bash
# 在训练脚本最后添加
echo "训练完成，5分钟后自动关机..."
sleep 300
sudo shutdown -h now
```

### 自动化脚本
```bash
#!/bin/bash
# auto_train_and_shutdown.sh

cd ~/btc_quant/predict
conda activate btc_quant

# 训练
python train_cached.py > training_gpu.log 2>&1

# 下载模型到OSS（可选）
# aliyun oss cp models/ oss://your-bucket/models/ -r

# 关机
sudo shutdown -h now
```

## 📦 下载训练好的模型

### 方法1：SCP下载
```bash
# 在本地Mac上执行
scp -r gpu_server:~/btc_quant/predict/models/tcn_* \
  /Users/lemonshwang/project/btc_quant/predict/models/
```

### 方法2：使用OSS（推荐）
```bash
# 在GPU服务器上
pip install aliyun-python-sdk-core aliyun-python-sdk-oss2
aliyun oss cp models/ oss://your-bucket/models/ -r

# 在本地下载
aliyun oss cp oss://your-bucket/models/ models/ -r
```

## 🔧 常见问题

### Q1: CUDA版本不匹配
```bash
# 检查CUDA版本
nvcc --version
nvidia-smi

# 安装对应版本的PyTorch
# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118
# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Q2: 显存不足
```bash
# 减小batch size
# 在.env中修改
TRAIN_BATCH_SIZE=512  # 从1024减到512
```

### Q3: 数据服务连接失败
```bash
# 检查Docker服务
docker ps

# 重启数据服务
docker-compose restart data-service

# 或使用缓存数据（推荐）
# train_cached.py会自动使用本地缓存
```

## 📝 完整工作流程

```bash
# 1. 在CPU服务器上准备好训练数据
ssh cpu_server
cd /root/workspace/btcquant && ./prepare_training_data.sh

# 2. 从CPU服务器传输数据到GPU服务器
scp training_data_cache.pkl gpu_server:~/btc_quant/predict/data_cache.pkl

# 3. 登录GPU服务器，初始化环境（首次）
ssh gpu_server
cd ~/btc_quant && ./setup_gpu_env.sh

# 4. 启动训练
./deploy_gpu_training.sh

# 5. 监控训练（20-60分钟）
tail -f predict/training_gpu.log

# 6. 下载模型到本地
# 在本地执行：
scp -r gpu_server:~/btc_quant/predict/models/tcn_* ./predict/models/

# 7. 部署到CPU推理服务
ssh cpu_server
cd /root/workspace/btcquant && docker-compose restart predict-service
```

## ✅ 验证清单

- [ ] GPU可用：`python -c "import torch; print(torch.cuda.is_available())"`
- [ ] CUDA版本匹配
- [ ] 数据缓存已上传
- [ ] .env配置正确（TRAIN_DEVICE=cuda）
- [ ] 训练日志正常输出
- [ ] GPU使用率>80%（nvidia-smi）
- [ ] 模型正常保存

## 🎯 优化建议

1. **使用数据缓存**：首次训练后保存data_cache.pkl，后续直接使用
2. **混合精度训练**：可以再快30%，显存减少40%
3. **多GPU训练**：如果使用多GPU实例，可以并行训练
4. **定时任务**：使用crontab定期自动训练

---

**预计总成本：** ¥2-3/次训练（使用抢占式T4实例）
**预计时间：** 30-60分钟
