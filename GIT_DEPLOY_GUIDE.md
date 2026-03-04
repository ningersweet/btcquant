# 🚀 Git部署快速指南

## ✅ 代码已提交到GitHub

**仓库地址：** https://github.com/ningersweet/btcquant.git

**最新提交：**
- 完整的TCN量化交易系统
- 47个文件更新
- 7131行新增代码

## 📋 服务器部署（3步）

### 步骤1：部署数据服务器（CPU服务器）

```bash
# 登录CPU服务器
ssh cpu_server
cd /root/workspace/btcquant

# 拉取最新代码
git pull origin main

# 启动数据服务
docker-compose up -d data-service

# 准备训练数据
./prepare_training_data.sh
```

### 步骤2：部署GPU服务器

```bash
# 登录GPU服务器
ssh gpu_server
cd ~/btc_quant

# 拉取最新代码（首次则 git clone）
git pull origin main

# 初始化GPU环境（首次，约5-10分钟）
./setup_gpu_env.sh

# 重新登录激活环境
exit
ssh gpu_server

# 从CPU服务器获取训练数据（在CPU服务器上执行）
# ssh cpu_server
# scp /root/workspace/btcquant/training_data_cache.pkl gpu_server:~/btc_quant/predict/data_cache.pkl

# 启动训练
cd ~/btc_quant
./deploy_gpu_training.sh
```

### 步骤3：部署推理服务器（可选）

```bash
# 上传训练好的模型到CPU服务器
scp -r gpu_server:~/btc_quant/predict/models/tcn_* cpu_server:/root/workspace/btcquant/predict/models/

# 重启推理服务
ssh cpu_server "cd /root/workspace/btcquant && docker-compose restart predict-service"
```

## 🔄 后续更新（超快！）

### 本地修改代码后

```bash
# 提交更新
git add .
git commit -m "优化训练参数"
git push

# 更新CPU服务器
ssh cpu_server "cd /root/workspace/btcquant && git pull origin main"

# 更新GPU服务器
ssh gpu_server "cd ~/btc_quant && git pull origin main"
```

### 或者在服务器上直接更新

```bash
# 登录CPU服务器
ssh cpu_server
cd /root/workspace/btcquant
git pull
docker-compose restart

# 登录GPU服务器
ssh gpu_server
cd ~/btc_quant
git pull
```

## 📊 Git vs 打包部署对比

| 操作 | Git方式 | 打包方式 | 优势 |
|------|---------|---------|------|
| 首次部署 | 1-2分钟 | 2-3分钟 | Git略快 |
| 代码更新 | **5-10秒** | 1-2分钟 | **Git快12倍** |
| 版本控制 | ✅ | ❌ | Git支持 |
| 回滚 | ✅ 一键 | ❌ 困难 | Git方便 |
| 多服务器 | ✅ 简单 | ⚠️ 繁琐 | Git便捷 |

## 🎯 完整工作流程

### 开发 → 测试 → 部署

```bash
# 1. 本地开发
cd /Users/lemonshwang/project/btc_quant
# 修改代码...

# 2. 本地测试
python predict/train_fast.py

# 3. 提交到Git
git add .
git commit -m "新功能：增加XXX"
git push

# 4. 部署到服务器（5秒）
./git_deploy.sh DATA_SERVER_IP data
./git_deploy.sh GPU_SERVER_IP gpu

# 5. 服务器上验证
ssh root@GPU_SERVER
cd ~/btc_quant
./deploy_gpu_training.sh
```

### 定期训练流程

```bash
# 每周自动化训练
#!/bin/bash
# weekly_training.sh

# 1. 更新代码
ssh cpu_server "cd /root/workspace/btcquant && git pull origin main"
ssh gpu_server "cd ~/btc_quant && git pull origin main"

# 2. 准备数据（在CPU服务器上）
ssh cpu_server "cd /root/workspace/btcquant && ./prepare_training_data.sh"

# 3. 从CPU服务器传输数据到GPU服务器
ssh cpu_server "scp /root/workspace/btcquant/training_data_cache.pkl gpu_server:~/btc_quant/predict/data_cache.pkl"

# 4. 启动训练
ssh gpu_server "cd ~/btc_quant && ./deploy_gpu_training.sh"

# 5. 等待完成并下载模型
# ...
```

## 🔧 常用Git命令

### 查看状态
```bash
# 在任一服务器上
cd ~/btc_quant  # 或 cd /root/workspace/btcquant（CPU服务器）
git status                    # 查看状态
git log --oneline -10         # 查看最近10次提交
git branch -a                 # 查看所有分支
```

### 更新代码
```bash
git pull                      # 拉取最新代码
git fetch && git reset --hard origin/main  # 强制更新（丢弃本地修改）
```

### 回滚版本
```bash
git log --oneline             # 查看提交历史
git checkout <commit-id>      # 回滚到指定版本
git checkout main             # 回到最新版本
```

### 切换分支
```bash
git checkout -b dev           # 创建并切换到dev分支
git checkout main             # 切换回main分支
```

## 📝 服务器配置文件

### CPU 服务器 (`ssh cpu_server`)
```bash
/root/workspace/btcquant/
├── docker-compose.yml        # Docker配置
├── prepare_training_data.sh  # 数据准备脚本
└── training_data_cache.pkl   # 训练数据缓存
```

### GPU 服务器 (`ssh gpu_server`)
```bash
~/btc_quant/
├── setup_gpu_env.sh          # 环境初始化
├── deploy_gpu_training.sh    # 训练启动
├── predict/
│   ├── data_cache.pkl        # 数据缓存（从CPU服务器传输）
│   ├── train_cached.py       # 训练脚本
│   └── models/               # 训练好的模型
```

## ✅ 部署检查清单

### CPU 服务器 (`ssh cpu_server`)
- [ ] 代码已克隆：`cd /root/workspace/btcquant && git status`
- [ ] Docker已安装：`docker --version`
- [ ] 数据服务运行：`docker-compose ps`
- [ ] 数据已准备：`ls -lh training_data_cache.pkl`

### GPU 服务器 (`ssh gpu_server`)
- [ ] 代码已克隆：`cd ~/btc_quant && git status`
- [ ] GPU可用：`nvidia-smi`
- [ ] Conda环境：`conda env list | grep btc_quant`
- [ ] PyTorch GPU：`python -c "import torch; print(torch.cuda.is_available())"`
- [ ] 数据缓存：`ls -lh predict/data_cache.pkl`

## 🎊 总结

**Git部署的优势：**
1. ✅ 更新速度快（5-10秒）
2. ✅ 版本控制完善
3. ✅ 支持回滚
4. ✅ 多服务器同步方便
5. ✅ 团队协作友好

**快速命令：**
```bash
# 更新CPU服务器
ssh cpu_server "cd /root/workspace/btcquant && git pull"

# 更新GPU服务器
ssh gpu_server "cd ~/btc_quant && git pull"

# 回滚
ssh cpu_server "cd /root/workspace/btcquant && git checkout <commit-id>"
ssh gpu_server "cd ~/btc_quant && git checkout <commit-id>"
```

---

**代码已推送到GitHub，随时可以开始部署！** 🚀

**仓库地址：** https://github.com/ningersweet/btcquant.git
