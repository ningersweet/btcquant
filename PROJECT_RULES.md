# BTC Quant 项目规则

## 配置文件管理

### 规则1: 配置文件不提交到Git

**原因：** 配置文件包含敏感信息（如邮件密码）和环境特定配置。

**实施：**
```bash
# .gitignore 已包含
config.yaml
.env
*.env.local
```

### 规则2: 使用统一的config.yaml

**位置：** 项目根目录 `config.yaml`

**不要：** 在子目录（如predict/）创建独立的config.yaml

**原因：** 
- 避免配置分散
- 便于统一管理
- 减少配置冲突

### 规则3: 配置文件通过SCP传输

**GPU服务器配置传输：**
```bash
# 方式1: 使用btcquant命令（推荐）
btcquant train sync-config

# 方式2: 手动传输
scp config.yaml gpu_server:~/workspace/btcquant/

# 方式3: 训练时自动传输
btcquant train start --gpu  # 自动传输配置
```

**CPU服务器配置传输：**
```bash
scp config.yaml cpu_server:/root/workspace/btcquant/
```

### 规则4: 配置文件示例

**提供示例文件：** `config.yaml.example`

**首次使用：**
```bash
cp config.yaml.example config.yaml
vim config.yaml  # 修改为实际配置
```

## 环境管理

### 规则5: GPU服务器使用venv

**不使用：** conda

**使用：** Python venv

**原因：**
- 更轻量
- 更快速
- 避免conda依赖问题

**初始化：**
```bash
btcquant gpu setup  # 自动创建venv并安装依赖
```

### 规则6: GPU服务器必须安装Git

**自动安装：**
```bash
btcquant gpu setup  # 自动检查并安装git
```

**手动安装：**
```bash
# CentOS/RHEL
yum install -y git

# Ubuntu/Debian
apt-get install -y git
```

## 训练管理

### 规则7: 训练前检查已有任务

**自动检查：** `btcquant train start --gpu` 会自动检查

**行为：**
- 如果有正在运行的训练，提示用户
- 用户确认后停止旧任务
- 启动新训练

**手动检查：**
```bash
btcquant train status
```

### 规则8: 使用后台任务训练

**启动方式：**
```bash
btcquant train start --gpu  # 自动后台运行
```

**特点：**
- 使用nohup后台运行
- 日志输出到 storage/logs/training.log
- 可以关闭SSH连接
- 训练完成自动通知

### 规则9: 训练完成自动通知

**配置邮件：**
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export TO_EMAIL=your_email@gmail.com
```

**通知内容：**
- 训练完成时间
- 模型性能指标
- 模型保存位置
- 自动传输状态

## 目录结构

### 规则10: 统一存储目录

**所有运行时数据存放在 storage/ 目录：**

```
storage/
├── logs/           # 所有日志
├── cache/          # 数据缓存
└── models/         # 训练模型
```

**不要：** 在各个子目录创建独立的logs/、cache/等

### 规则11: 日志统一管理

**日志位置：** `storage/logs/`

**命名规范：**
- `training.log` - 训练日志
- `inference.log` - 推理日志
- `backtest.log` - 回测日志
- `api.log` - API日志

**访问日志：**
```bash
# 使用命令
btcquant train logs

# 直接查看
tail -f storage/logs/training.log
```

## 命令行工具

### 规则12: 使用btcquant统一命令

**不要：** 创建独立的shell脚本

**使用：** btcquant子命令

**示例：**
```bash
# ✅ 推荐
btcquant train start --gpu
btcquant data prepare
btcquant server update gpu

# ❌ 不推荐
./start_training.sh
./deploy.sh
```

### 规则13: 脚本整合原则

**新功能添加到btcquant：**
1. 在btcquant中添加函数
2. 在help中添加说明
3. 在main函数中添加路由

**不要：** 创建新的独立脚本

## 代码提交

### 规则14: 提交前检查

**必须检查：**
- [ ] config.yaml 未被提交
- [ ] .env 文件未被提交
- [ ] 日志文件未被提交
- [ ] 缓存文件未被提交
- [ ] 大模型文件未被提交

**检查命令：**
```bash
git status
git diff --cached
```

### 规则15: 提交信息规范

**格式：**
```
<类型>: <简短描述>

<详细描述>

<相关Issue>
```

**类型：**
- feat: 新功能
- fix: 修复
- refactor: 重构
- docs: 文档
- chore: 构建/工具

## 部署流程

### 规则16: GPU服务器部署流程

**标准流程：**
```bash
# 1. 初始化环境（首次）
btcquant gpu setup

# 2. 同步配置文件
btcquant train sync-config

# 3. 同步训练数据
btcquant train sync-data

# 4. 启动训练
btcquant train start --gpu

# 5. 查看状态
btcquant train status
btcquant train logs
```

### 规则17: 代码更新流程

**GPU服务器：**
```bash
# 服务器上有git，直接pull
ssh gpu_server
cd ~/workspace/btcquant
git pull origin main
```

**CPU服务器：**
```bash
btcquant server update cpu
```

## 安全规范

### 规则18: 敏感信息管理

**不要：**
- 硬编码密码
- 提交.env文件
- 提交config.yaml
- 在代码中写API密钥

**使用：**
- 环境变量
- config.yaml（不提交）
- .env文件（不提交）

### 规则19: 服务器访问

**使用SSH密钥：**
```bash
# 配置SSH
vim ~/.ssh/config

Host gpu_server
    HostName YOUR_GPU_IP
    User root
    IdentityFile ~/.ssh/id_rsa
```

**不要：** 使用密码登录

## 性能优化

### 规则20: 标签生成使用多核

**默认：** 自动使用所有CPU核心

**配置：**
```python
from src.label_generator import LabelGenerator

# 使用所有核心
generator = LabelGenerator(n_jobs=-1)

# 指定核心数
generator = LabelGenerator(n_jobs=4)
```

### 规则21: 训练使用GPU

**配置：**
```yaml
predict:
  training:
    device: "cuda"  # GPU
    # device: "cpu"  # CPU
```

**检查GPU：**
```bash
ssh gpu_server
nvidia-smi
```

## 监控和维护

### 规则22: 定期检查

**每日检查：**
- 训练状态
- 日志大小
- 磁盘空间

**命令：**
```bash
btcquant train status
btcquant server status gpu
```

### 规则23: 日志清理

**定期清理旧日志：**
```bash
# 保留最近7天
find storage/logs/ -name "*.log" -mtime +7 -delete

# 压缩旧日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz storage/logs/*.log
```

### 规则24: 模型管理

**保留策略：**
- 保留最近3个模型
- 保留最佳性能模型
- 定期备份到本地

**清理命令：**
```bash
# 保留最近3个
cd storage/models
ls -t | grep tcn_ | tail -n +4 | xargs rm -rf
```

## 故障处理

### 规则25: 训练中断处理

**检查：**
```bash
btcquant train status
tail -100 storage/logs/training.log
```

**重启：**
```bash
btcquant train start --gpu
```

### 规则26: 配置问题

**症状：** 训练失败，提示配置错误

**解决：**
```bash
# 1. 检查本地配置
cat config.yaml

# 2. 重新同步
btcquant train sync-config

# 3. 重启训练
btcquant train start --gpu
```

## 更新记录

- 2026-03-05: 初始版本
- 配置文件不提交到Git
- 使用统一的config.yaml
- GPU服务器使用venv
- 训练前检查已有任务
- 配置文件SCP传输
