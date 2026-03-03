# 服务器部署完整指南

## 架构说明

```
┌─────────────────────────────────────┐
│   数据服务器（常驻运行）              │
│   - Docker运行数据服务                │
│   - SQLite数据库（68万条数据）        │
│   - 准备训练数据缓存                  │
└─────────────────────────────────────┘
              ↓ 传输数据缓存
┌─────────────────────────────────────┐
│   GPU训练服务器（按需启动）           │
│   - 接收数据缓存                      │
│   - GPU训练模型                       │
│   - 训练完成后释放                    │
└─────────────────────────────────────┘
              ↓ 传输训练好的模型
┌─────────────────────────────────────┐
│   推理服务器（常驻运行）              │
│   - CPU推理服务                       │
│   - 实盘交易                          │
└─────────────────────────────────────┘
```

## 🚀 完整部署流程

### 步骤1：在数据服务器上准备训练数据

```bash
# 1. 上传脚本到数据服务器
scp prepare_training_data.sh root@DATA_SERVER:~/

# 2. SSH登录数据服务器
ssh root@DATA_SERVER

# 3. 进入项目目录
cd ~/btc_quant

# 4. 运行数据准备脚本
chmod +x prepare_training_data.sh
./prepare_training_data.sh

# 预计时间：2-5分钟
# 输出：training_data_cache.pkl（约100-200MB）
```

### 步骤2：传输数据到GPU服务器

```bash
# 在数据服务器上执行
scp training_data_cache.pkl root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 或者使用OSS中转（推荐，更快）
# 1. 上传到OSS
aliyun oss cp training_data_cache.pkl oss://your-bucket/training/

# 2. 在GPU服务器下载
aliyun oss cp oss://your-bucket/training/training_data_cache.pkl \
  ~/btc_quant/predict/data_cache.pkl
```

### 步骤3：在GPU服务器上训练

```bash
# 1. SSH登录GPU服务器
ssh root@GPU_SERVER

# 2. 初始化环境（首次）
cd ~/btc_quant
./setup_gpu_env.sh

# 3. 确认数据缓存已就位
ls -lh predict/data_cache.pkl

# 4. 启动训练
./deploy_gpu_training.sh

# 5. 监控训练
tail -f predict/training_gpu.log
watch -n 5 nvidia-smi
```

### 步骤4：下载模型到推理服务器

```bash
# 方法1：直接SCP
scp -r root@GPU_SERVER:~/btc_quant/predict/models/tcn_* \
  root@INFERENCE_SERVER:~/btc_quant/predict/models/

# 方法2：通过OSS中转
# 在GPU服务器
aliyun oss cp predict/models/tcn_* oss://your-bucket/models/ -r

# 在推理服务器
aliyun oss cp oss://your-bucket/models/tcn_* predict/models/ -r

# 方法3：下载到本地再上传
scp -r root@GPU_SERVER:~/btc_quant/predict/models/tcn_* ./models/
scp -r ./models/tcn_* root@INFERENCE_SERVER:~/btc_quant/predict/models/
```

## 📋 服务器配置建议

### 数据服务器
- **配置：** 2核4G，50GB磁盘
- **成本：** ¥50-100/月
- **用途：** 运行数据服务，存储历史数据
- **常驻运行**

### GPU训练服务器
- **配置：** ecs.gn6i-c4g1.xlarge (T4 16GB)
- **成本：** ¥2-3/小时（抢占式）
- **用途：** 模型训练
- **按需启动，训练完释放**

### 推理服务器
- **配置：** 2核4G
- **成本：** ¥50-100/月
- **用途：** 运行推理服务，实盘交易
- **常驻运行**

## 💰 成本分析

### 方案A：三台服务器分离（推荐）
- 数据服务器：¥80/月
- GPU训练：¥2/次 × 4次/月 = ¥8/月
- 推理服务器：¥80/月
- **总计：¥168/月**

### 方案B：数据+推理合并
- 数据+推理服务器：¥100/月
- GPU训练：¥8/月
- **总计：¥108/月**

### 方案C：全部本地（如果有GPU）
- 本地服务器：一次性投入
- 电费：¥50/月
- **总计：¥50/月（不含硬件）**

## 🔧 自动化脚本

### 定时训练脚本

```bash
#!/bin/bash
# auto_weekly_training.sh
# 每周自动训练

# 1. 在数据服务器准备数据
ssh root@DATA_SERVER "cd ~/btc_quant && ./prepare_training_data.sh"

# 2. 创建GPU实例（使用阿里云CLI）
aliyun ecs RunInstances \
  --InstanceType ecs.gn6i-c4g1.xlarge \
  --SpotStrategy SpotWithPriceLimit \
  --SpotPriceLimit 3.0

# 3. 等待实例启动
sleep 60

# 4. 传输数据
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
  root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 5. 启动训练
ssh root@GPU_SERVER "cd ~/btc_quant && ./deploy_gpu_training.sh"

# 6. 等待训练完成（监控日志）
# ...

# 7. 下载模型
scp -r root@GPU_SERVER:~/btc_quant/predict/models/tcn_* \
  root@INFERENCE_SERVER:~/btc_quant/predict/models/

# 8. 释放GPU实例
aliyun ecs DeleteInstance --InstanceId xxx

# 9. 重启推理服务
ssh root@INFERENCE_SERVER "cd ~/btc_quant && docker-compose restart predict-service"
```

## ✅ 检查清单

### 数据服务器
- [ ] Docker已安装并运行
- [ ] 数据服务正常运行
- [ ] 数据库包含68万条数据
- [ ] 可以成功生成训练数据缓存

### GPU服务器
- [ ] GPU驱动正常
- [ ] CUDA环境正确
- [ ] PyTorch可以使用GPU
- [ ] 数据缓存已传输
- [ ] 训练脚本可以正常运行

### 推理服务器
- [ ] Docker已安装
- [ ] 推理服务正常运行
- [ ] 可以加载模型
- [ ] API响应正常

## 🎯 快速命令参考

```bash
# 数据服务器
./prepare_training_data.sh                    # 准备数据
docker-compose ps                             # 检查服务
curl http://localhost:8001/health             # 测试API

# GPU服务器
./setup_gpu_env.sh                            # 初始化环境
./deploy_gpu_training.sh                      # 启动训练
tail -f predict/training_gpu.log              # 查看日志
nvidia-smi                                    # 查看GPU

# 推理服务器
docker-compose up -d predict-service          # 启动服务
curl http://localhost:8000/health             # 测试API
docker-compose logs -f predict-service        # 查看日志
```

## 📞 故障排查

### 问题1：数据服务连接失败
```bash
# 检查服务状态
docker-compose ps
docker-compose logs data-service

# 重启服务
docker-compose restart data-service
```

### 问题2：GPU不可用
```bash
# 检查驱动
nvidia-smi

# 检查CUDA
nvcc --version

# 检查PyTorch
python -c "import torch; print(torch.cuda.is_available())"
```

### 问题3：数据传输慢
```bash
# 使用压缩传输
tar -czf data.tar.gz training_data_cache.pkl
scp data.tar.gz root@GPU_SERVER:~/
ssh root@GPU_SERVER "cd ~ && tar -xzf data.tar.gz"

# 或使用OSS
aliyun oss cp training_data_cache.pkl oss://bucket/
```

---

**下一步：** 运行 `prepare_training_data.sh` 在数据服务器上准备训练数据
