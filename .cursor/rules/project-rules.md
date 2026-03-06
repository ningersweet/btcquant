# BTC Quant 项目规则

## 服务器部署信息

### SSH 连接方式
- **CPU 服务器（数据服务）**: `ssh cpu_server`
- **GPU 服务器（模型训练）**: `ssh gpu_server`
- **CPU 服务器可直接访问 GPU 服务器**: 在 cpu_server 上执行 `ssh gpu_server` 即可，便于数据传输

### CPU 服务器配置
- **SSH 别名**: cpu_server
- **CPU**: 2 核 (系统可用 1 核)
- **内存**: 4 GB (系统可用 2 GB)
- **磁盘**: 100 GB
- **已安装**: Docker, Git

### 项目部署
- **项目目录**: /root/workspace/btcquant
- **代码仓库**: https://github.com/ningersweet/btcquant.git
- **拉取方式**: HTTPS (服务端使用)
- **SSH 仓库**: git@github.com:ningersweet/btcquant.git (本地开发使用)

### 资源限制（CPU 服务器）
每个服务的资源限制：
- CPU: 0.25 核
- 内存: 512 MB
- 总计: 1 核 CPU, 2 GB 内存

### 日志配置
- 日志驱动: json-file
- 单文件大小: 10 MB
- 保留文件数: 3

## 开发规范

### 分支管理
- main: 主分支，用于生产部署
- develop: 开发分支
- feature/*: 功能分支

### 配置文件管理

**重要：配置文件不在Git中，需要通过SCP传输！**

配置文件包含敏感信息（如API密钥、邮箱密码等），不会提交到Git仓库。

#### 统一配置文件

**使用根目录的 config.yaml：**
- 项目只使用一个配置文件：`config.yaml`
- 位置：项目根目录
- 不要在子目录（如predict/）创建独立配置

#### 配置文件传输

**使用btcquant命令（推荐）：**
```bash
# 同步配置到GPU服务器
btcquant train sync-config

# 启动训练时自动传输
btcquant train start --gpu  # 自动传输config.yaml
```

**手动传输：**
```bash
# GPU服务器
scp config.yaml gpu_server:~/workspace/btcquant/

# CPU服务器
scp config.yaml cpu_server:/root/workspace/btcquant/
```

#### 首次部署配置
```bash
# 1. 在本地创建配置文件
cp config.yaml.example config.yaml
vim config.yaml  # 编辑配置

# 2. 初始化GPU环境（自动安装git和venv）
btcquant gpu setup

# 3. 同步配置文件
btcquant train sync-config

# 4. 配置邮件通知（可选）
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export TO_EMAIL=your_email@gmail.com
```

#### 配置文件更新流程
```bash
# 1. 本地修改配置文件
vim config.yaml

# 2. 同步到GPU服务器
btcquant train sync-config

# 3. 重启训练（如需要）
btcquant train start --gpu
```

#### 注意事项
- ⚠️ 配置文件包含敏感信息，不要提交到Git
- ⚠️ 只使用根目录的config.yaml，不要创建多个配置文件
- ⚠️ 修改配置后使用 btcquant train sync-config 同步
- ⚠️ 训练前会自动传输配置文件
- ⚠️ GPU服务器使用venv管理Python环境（不使用conda）

### 代码部署流程

**CPU服务器：**
```bash
# 使用btcquant命令
btcquant server update cpu

# 或手动更新
ssh cpu_server
cd /root/workspace/btcquant
git pull origin main
docker-compose restart
```

**GPU服务器：**
```bash
# 首次部署（自动安装git和venv）
btcquant gpu setup

# 更新代码
ssh gpu_server
cd ~/workspace/btcquant
git pull origin main

# 同步配置文件
btcquant train sync-config
```

### GPU训练流程

**完整流程：**
```bash
# 1. 准备训练数据（CPU服务器）
btcquant data prepare

# 2. 同步数据到GPU服务器
btcquant train sync-data

# 3. 同步配置文件
btcquant train sync-config

# 4. 启动训练（自动检查已有任务）
btcquant train start --gpu

# 5. 查看状态
btcquant train status
btcquant train logs

# 6. 训练完成后自动：
#    - 传输模型到CPU服务器
#    - 发送邮件通知
```

### 训练任务管理

**自动检查机制：**
- 启动训练前自动检查是否有正在运行的任务
- 如果有，提示用户确认是否停止
- 用户确认后停止旧任务，启动新训练

**手动管理：**
```bash
# 查看状态
btcquant train status

# 停止训练
btcquant train stop

# 查看日志
btcquant train logs
```

### 注意事项
- 服务器资源有限，避免运行资源密集型任务
- 前期不考虑高可用和数据备份
- 确保日志正常输出用于问题排查
- **配置文件不在Git中，修改后需手动同步到服务器**
