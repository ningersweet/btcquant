# BTC Quant 命令使用指南

## 📋 命令分类和使用场景

### 1. 服务器管理 (server)
**用途**: 管理CPU和GPU服务器的部署和维护

```bash
# 首次部署到服务器（安装环境、克隆代码）
btcquant server init cpu      # 部署到CPU服务器
btcquant server init gpu      # 部署到GPU服务器（已废弃，使用 gpu setup）

# 更新服务器代码
btcquant server update cpu    # 更新CPU服务器代码
btcquant server update gpu    # 更新GPU服务器代码

# 查看服务器状态
btcquant server status cpu    # 查看CPU服务器状态
btcquant server status gpu    # 查看GPU服务器状态

# SSH登录服务器
btcquant server shell cpu     # 登录CPU服务器
btcquant server shell gpu     # 登录GPU服务器

# 查看服务日志
btcquant server logs cpu data-service    # 查看CPU服务器数据服务日志
```

**使用场景**:
- 首次部署项目到新服务器
- 定期更新服务器代码
- 快速登录服务器进行调试

---

### 2. 数据服务 (data)
**用途**: 管理数据服务（运行在CPU服务器上）

```bash
# 启动数据服务
btcquant data start           # 启动数据服务容器

# 停止数据服务
btcquant data stop            # 停止数据服务

# 重启数据服务
btcquant data restart         # 重启数据服务

# 查看数据服务状态
btcquant data status          # 查看服务运行状态

# 准备训练数据（生成标签和缓存）
btcquant data prepare         # 在CPU服务器上准备训练数据

# 同步历史数据
btcquant data sync            # 从数据源同步历史K线数据
```

**使用场景**:
- 启动/停止数据服务API
- 准备训练数据（生成标签、创建缓存）
- 同步最新的历史数据

---

### 3. 容器管理 (docker)
**用途**: 管理Docker容器（主要用于数据服务）

```bash
# 构建Docker镜像
btcquant docker build         # 构建所有服务
btcquant docker build data-service  # 只构建数据服务

# 启动容器
btcquant docker up            # 启动所有容器
btcquant docker up data-service     # 只启动数据服务

# 停止容器
btcquant docker down          # 停止所有容器

# 查看容器状态
btcquant docker ps            # 查看运行中的容器

# 查看容器日志
btcquant docker logs data-service   # 查看数据服务日志

# 监控容器资源
btcquant docker monitor       # 监控CPU、内存使用情况
```

**使用场景**:
- 开发环境下使用Docker运行数据服务
- 调试容器问题
- 监控资源使用

---

### 4. 训练管理 (train) ⭐ 最常用
**用途**: 管理模型训练流程

```bash
# 启动训练
btcquant train start          # 本地CPU训练
btcquant train start --gpu    # GPU服务器训练（推荐）

# 查看训练状态
btcquant train status         # 查看GPU服务器训练进程状态

# 查看训练日志
btcquant train logs           # 查看GPU服务器训练日志

# 停止训练
btcquant train stop           # 停止GPU服务器训练

# 同步配置文件到GPU服务器
btcquant train sync-config    # 传输config.yaml到GPU服务器

# 同步训练数据到GPU服务器
btcquant train sync-data      # 从CPU服务器传输训练数据缓存到GPU服务器

# 同步训练好的模型到CPU服务器
btcquant train sync-model     # 从GPU服务器传输模型到CPU服务器
```

**完整训练流程**:
```bash
# 1. 在CPU服务器准备数据
btcquant data prepare

# 2. 同步配置到GPU服务器
btcquant train sync-config

# 3. 同步训练数据到GPU服务器
btcquant train sync-data

# 4. 启动GPU训练
btcquant train start --gpu

# 5. 查看训练进度
btcquant train logs

# 6. 训练完成后同步模型
btcquant train sync-model
```

---

### 5. GPU管理 (gpu)
**用途**: GPU环境初始化

```bash
# GPU环境初始化（首次使用必须执行）
btcquant gpu setup
```

**功能说明**：
- 安装 Git（如果不存在）
- 安装 Python 3.11（如果不存在）
- 克隆或更新项目代码
- 创建 Python 3.11 虚拟环境
- 安装 PyTorch GPU 版本（CUDA 11.8）
- 安装项目依赖
- 创建存储目录
- 验证 GPU 可用性

**使用场景**:
- 首次在GPU服务器上训练（必须执行）
- 重新安装环境
- 环境损坏需要重建

**完整的首次部署流程**：
```bash
# 1. 初始化GPU环境
btcquant gpu setup

# 2. 在CPU服务器准备数据
btcquant data prepare

# 3. 同步配置和数据
btcquant train sync-config
btcquant train sync-data

# 4. 启动训练
btcquant train start --gpu
```

---

### 6. 本地开发 (local)
**用途**: 本地开发和测试

```bash
# 运行测试
btcquant local test           # 运行单元测试

# 代码检查
btcquant local lint           # 运行代码风格检查
```

**使用场景**:
- 运行单元测试
- 代码提交前检查

---

### 7. Git管理 (git)
**用途**: 代码版本管理

```bash
# 提交并推送代码
btcquant git push             # 交互式提交并推送
```

**使用场景**:
- 快速提交代码到远程仓库

---

### 8. 工具命令
```bash
# 显示版本信息
btcquant version

# 显示帮助信息
btcquant help
```

---

## 🎯 常见使用场景

### 场景1: 首次部署项目
```bash
# 1. 初始化GPU环境
btcquant gpu setup

# 2. 在CPU服务器准备数据
btcquant data prepare

# 3. 同步配置和数据
btcquant train sync-config
btcquant train sync-data

# 4. 启动训练
btcquant train start --gpu
```

### 场景2: 日常训练流程
```bash
# 1. 更新数据（如果需要）
btcquant data sync
btcquant data prepare

# 2. 同步到GPU服务器
btcquant train sync-data

# 3. 启动训练
btcquant train start --gpu

# 4. 监控训练
btcquant train logs
```

### 场景3: 代码更新后重新训练
```bash
# 1. 推送代码
btcquant git push

# 2. 更新GPU服务器代码
btcquant server update gpu

# 3. 重启训练
btcquant train stop
btcquant train start --gpu
```

### 场景4: 调试问题
```bash
# 查看各种状态
btcquant train status
btcquant train logs
btcquant server status gpu

# 登录服务器调试
btcquant server shell gpu
```

---

## 📝 命令优先级建议

### 高频使用（每天）:
- `btcquant train start --gpu`
- `btcquant train logs`
- `btcquant train status`

### 中频使用（每周）:
- `btcquant data prepare`
- `btcquant train sync-data`
- `btcquant git push`

### 低频使用（偶尔）:
- `btcquant gpu setup`
- `btcquant server update`
- `btcquant docker build`

---

## ⚠️ 注意事项

1. **GPU训练前必须**:
   - 先运行 `btcquant gpu setup` 初始化环境
   - 同步配置文件 `btcquant train sync-config`
   - 同步训练数据 `btcquant train sync-data`

2. **数据准备**:
   - `btcquant data prepare` 在CPU服务器运行（计算密集）
   - 生成的缓存文件需要同步到GPU服务器

3. **配置文件**:
   - 修改 `config.yaml` 后需要重新同步到GPU服务器
   - 使用 `btcquant train sync-config`

4. **邮件通知配置**:
   - 在 `config.yaml` 中配置邮件信息（推荐）
   - 或使用环境变量 `SMTP_USER`, `SMTP_PASSWORD`, `TO_EMAIL`
   - 环境变量优先级高于配置文件
   - 训练完成后自动发送邮件通知

5. **废弃命令**:
   - `btcquant gpu train/sync-*` 已废弃
   - 使用 `btcquant train` 系列命令代替
