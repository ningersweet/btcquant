# 🚀 快速部署指南（你的服务器）

## 服务器信息

- **IP地址：** 47.236.94.252
- **项目目录：** /root/workspace/btcquant
- **配置：** 2核4G，100GB磁盘
- **已安装：** Docker, Git

## 📋 快速开始（3步）

### 步骤1：首次部署

```bash
cd /Users/lemonshwang/project/btc_quant

# 首次部署（克隆代码）
./deploy.sh init

# 输出：
# ✓ 克隆项目...
# ✓ 代码部署完成
```

### 步骤2：启动数据服务

```bash
# 启动数据服务
./deploy.sh data

# 输出：
# ✓ 数据服务已启动
```

### 步骤3：准备训练数据

```bash
# 准备训练数据（约2-5分钟）
./deploy.sh prepare

# 输出：
# ✓ 共获取 681,959 条K线数据
# ✓ 缓存文件大小: 150-200 MB
```

## 🔄 日常使用

### 更新代码

```bash
# 本地修改后推送
git add .
git commit -m "更新XXX"
git push

# 服务器更新（5秒）
./deploy.sh update
```

### 查看状态

```bash
# 查看服务状态
./deploy.sh status

# 输出：
# - Docker服务状态
# - 磁盘使用情况
# - 内存使用情况
# - 训练数据缓存
```

### 查看日志

```bash
# 查看数据服务日志
./deploy.sh logs data-service

# 查看其他服务日志
./deploy.sh logs predict-service
```

### SSH登录

```bash
# 直接登录服务器
./deploy.sh shell

# 或者
ssh root@47.236.94.252
```

## 📊 命令速查表

| 命令 | 说明 | 用途 |
|------|------|------|
| `./deploy.sh init` | 首次部署 | 克隆代码 |
| `./deploy.sh update` | 更新代码 | 拉取最新代码 |
| `./deploy.sh data` | 启动数据服务 | 启动Docker服务 |
| `./deploy.sh prepare` | 准备训练数据 | 获取历史数据 |
| `./deploy.sh status` | 查看状态 | 检查服务和资源 |
| `./deploy.sh logs` | 查看日志 | 排查问题 |
| `./deploy.sh shell` | SSH登录 | 进入服务器 |

## 🎯 完整工作流程

### 首次部署

```bash
# 1. 部署代码
./deploy.sh init

# 2. 启动数据服务
./deploy.sh data

# 3. 准备训练数据
./deploy.sh prepare

# 4. 查看状态
./deploy.sh status
```

### 日常开发

```bash
# 1. 本地修改代码
# ...

# 2. 提交到Git
git add .
git commit -m "优化XXX"
git push

# 3. 服务器更新
./deploy.sh update

# 4. 重启服务（如需要）
./deploy.sh shell
cd /root/workspace/btcquant
docker-compose restart
```

## ⚠️ 注意事项

### 资源限制

你的服务器配置：
- **CPU：** 2核（系统可用1核）
- **内存：** 4GB（系统可用2GB）
- **磁盘：** 100GB

**建议：**
- ✅ 数据服务：可以运行
- ✅ 准备训练数据：可以运行
- ❌ GPU训练：不支持（需要GPU服务器）
- ✅ CPU推理：可以运行（但速度慢）

### 服务器用途

**推荐用途：**
1. ✅ 数据服务器（存储历史数据）
2. ✅ 准备训练数据缓存
3. ✅ 代码仓库和版本管理

**不推荐：**
1. ❌ 模型训练（资源不足）
2. ❌ 高频推理（性能不够）

### GPU训练方案

由于你的服务器没有GPU，建议：

```bash
# 1. 在你的服务器准备数据
./deploy.sh prepare

# 2. 下载数据到本地
scp root@47.236.94.252:/root/workspace/btcquant/training_data_cache.pkl ./

# 3. 上传到GPU服务器
scp training_data_cache.pkl root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 4. 在GPU服务器训练
ssh root@GPU_SERVER
cd ~/btc_quant
./deploy_gpu_training.sh
```

## 📝 服务器目录结构

```
/root/workspace/btcquant/
├── docker-compose.yml
├── data/                      # 数据服务
├── predict/                   # 预测服务
├── common/                    # 公共模块
├── prepare_training_data.sh   # 数据准备脚本
└── training_data_cache.pkl    # 训练数据缓存（约150-200MB）
```

## 🔧 常见操作

### 检查数据服务

```bash
./deploy.sh shell
cd /root/workspace/btcquant

# 检查服务
docker-compose ps

# 测试API
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/status?symbol=BTCUSDT&interval=5m
```

### 清理磁盘空间

```bash
./deploy.sh shell

# 清理Docker
docker system prune -a

# 清理日志
cd /root/workspace/btcquant
rm -f *.log
```

### 备份数据

```bash
# 下载训练数据缓存到本地
scp root@47.236.94.252:/root/workspace/btcquant/training_data_cache.pkl \
    ~/backup/training_data_cache_$(date +%Y%m%d).pkl
```

## ✅ 快速检查清单

- [ ] 代码已部署：`./deploy.sh status`
- [ ] 数据服务运行：`docker-compose ps`
- [ ] 训练数据已准备：`ls -lh training_data_cache.pkl`
- [ ] API可访问：`curl http://localhost:8001/health`

## 🎊 总结

**你的服务器角色：数据服务器**

**主要用途：**
1. ✅ 运行数据服务（Docker）
2. ✅ 存储历史数据（SQLite）
3. ✅ 准备训练数据缓存
4. ✅ 代码版本管理

**GPU训练：**
- 需要另外租用GPU服务器
- 从你的服务器获取数据缓存
- 训练完成后下载模型

**快速命令：**
```bash
./deploy.sh init      # 首次部署
./deploy.sh update    # 更新代码
./deploy.sh prepare   # 准备数据
./deploy.sh status    # 查看状态
```

---

**服务器已就绪，随时可以开始！** 🚀
