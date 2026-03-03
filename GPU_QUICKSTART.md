# GPU训练快速上手

## 🚀 3步开始GPU训练

### 1. 准备GPU服务器

在阿里云创建GPU实例：
- **实例规格：** ecs.gn6i-c4g1.xlarge (T4 16GB)
- **镜像：** Ubuntu 20.04 + CUDA 11.8
- **付费模式：** 抢占式实例（出价60%）
- **成本：** ¥2-3/小时

### 2. 上传代码和初始化

```bash
# 在本地Mac执行
cd /Users/lemonshwang/project/btc_quant

# 打包项目（包含数据缓存）
tar -czf btc_quant_deploy.tar.gz \
  predict/ data/ common/ \
  docker-compose.yml \
  setup_gpu_env.sh \
  deploy_gpu_training.sh \
  GPU_TRAINING_GUIDE.md

# 上传到GPU服务器
scp btc_quant_deploy.tar.gz root@YOUR_GPU_IP:~/

# SSH登录
ssh root@YOUR_GPU_IP

# 解压
cd ~
tar -xzf btc_quant_deploy.tar.gz
cd btc_quant

# 初始化环境（首次运行，约5-10分钟）
chmod +x setup_gpu_env.sh
./setup_gpu_env.sh

# 重新登录激活环境
exit
ssh root@YOUR_GPU_IP
```

### 3. 启动训练

```bash
cd ~/btc_quant
chmod +x deploy_gpu_training.sh
./deploy_gpu_training.sh

# 监控训练
tail -f predict/training_gpu.log

# 监控GPU
watch -n 5 nvidia-smi
```

## ⏱️ 预计时间

- **环境初始化：** 5-10分钟（首次）
- **数据获取：** 2-3分钟（如果有缓存则秒级）
- **训练时间：** 30-60分钟（T4 GPU）

## 💰 成本

- **抢占式T4：** ¥2-3/小时
- **单次训练：** ¥1-2元
- **每周训练：** ¥4-8元/月

## 📦 训练完成后

```bash
# 1. 下载模型到本地
scp -r root@YOUR_GPU_IP:~/btc_quant/predict/models/tcn_* \
  /Users/lemonshwang/project/btc_quant/predict/models/

# 2. 释放GPU实例（在阿里云控制台）

# 3. 部署到CPU推理服务
cd /Users/lemonshwang/project/btc_quant
docker-compose restart predict-service
```

## 📋 文件清单

已为你准备好以下文件：

- ✅ `setup_gpu_env.sh` - GPU环境初始化脚本
- ✅ `deploy_gpu_training.sh` - 快速部署训练脚本
- ✅ `GPU_TRAINING_GUIDE.md` - 详细使用指南
- ✅ `train_cached.py` - 支持缓存的训练脚本
- ✅ `train_incremental.py` - 增量训练脚本

## 🎯 下一步

1. 创建阿里云GPU实例
2. 按照上面3步操作
3. 等待30-60分钟训练完成
4. 下载模型部署到生产环境

详细说明请查看：`GPU_TRAINING_GUIDE.md`
