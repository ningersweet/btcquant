# BTC Quant 统一命令行工具

一个统一的命令行工具，整合了所有脚本功能，通过子命令执行不同操作。

## 安装

```bash
# 克隆项目
git clone https://github.com/ningersweet/btcquant.git
cd btcquant

# 添加到 PATH（可选）
echo 'export PATH="$PATH:'$(pwd)'"' >> ~/.bashrc
source ~/.bashrc

# 或者创建软链接
sudo ln -s $(pwd)/btcquant /usr/local/bin/btcquant
```

## 快速开始

```bash
# 查看帮助
./btcquant help

# 首次部署到CPU服务器
./btcquant server init cpu

# 启动数据服务
./btcquant data start

# 准备训练数据
./btcquant data prepare

# 查看服务器状态
./btcquant server status cpu
```

## 命令参考

### 服务器管理

```bash
# 首次部署
./btcquant server init cpu          # 部署到CPU服务器
./btcquant server init gpu          # 部署到GPU服务器

# 更新代码
./btcquant server update cpu        # 更新CPU服务器代码
./btcquant server update gpu        # 更新GPU服务器代码

# 查看状态
./btcquant server status cpu        # 查看CPU服务器状态
./btcquant server status gpu        # 查看GPU服务器状态

# SSH登录
./btcquant server shell cpu         # 登录CPU服务器
./btcquant server shell gpu         # 登录GPU服务器

# 查看日志
./btcquant server logs cpu data-service     # 查看数据服务日志
./btcquant server logs gpu                  # 查看GPU服务器日志
```

### 数据服务

```bash
# 启动/停止/重启
./btcquant data start               # 启动数据服务
./btcquant data stop                # 停止数据服务
./btcquant data restart             # 重启数据服务

# 查看状态
./btcquant data status              # 查看数据服务状态

# 数据准备
./btcquant data prepare             # 准备训练数据
./btcquant data sync                # 同步历史数据（从Binance）
```

### Docker容器管理

```bash
# 构建镜像
./btcquant docker build             # 构建所有镜像
./btcquant docker build data-service    # 构建指定服务

# 启动/停止容器
./btcquant docker up                # 启动所有容器
./btcquant docker up data-service   # 启动指定容器
./btcquant docker down              # 停止所有容器

# 查看状态
./btcquant docker ps                # 查看容器状态
./btcquant docker logs data-service # 查看容器日志
./btcquant docker monitor           # 监控容器资源
```

### GPU训练

```bash
# 环境初始化
./btcquant gpu setup                # 初始化GPU环境（首次）

# 训练
./btcquant gpu train                # 启动GPU训练
./btcquant gpu deploy               # 部署训练任务

# 数据同步
./btcquant gpu sync-data            # 从CPU服务器同步训练数据
./btcquant gpu sync-model tcn_xxx   # 同步模型到CPU服务器
```

### 本地开发

```bash
# 训练
./btcquant local train              # 本地快速训练

# 测试
./btcquant local test               # 运行测试

# 代码检查
./btcquant local lint               # 代码风格检查
```

### Git操作

```bash
# 提交代码
./btcquant git push                 # 提交并推送代码

# Git部署
./btcquant git deploy cpu           # Git部署到CPU服务器
./btcquant git deploy gpu           # Git部署到GPU服务器
```

### 其他工具

```bash
# 修复并部署
./btcquant fix deploy               # 修复容器问题并部署

# 版本信息
./btcquant version                  # 显示版本信息

# 帮助
./btcquant help                     # 显示帮助信息
```

## 典型工作流程

### 首次部署

```bash
# 1. 部署到CPU服务器
./btcquant server init cpu

# 2. 启动数据服务
./btcquant data start

# 3. 准备训练数据
./btcquant data prepare

# 4. 部署到GPU服务器
./btcquant server init gpu

# 5. 初始化GPU环境
./btcquant gpu setup

# 6. 同步训练数据
./btcquant gpu sync-data

# 7. 启动训练
./btcquant gpu train
```

### 日常开发

```bash
# 1. 本地修改代码
# ... 编辑代码 ...

# 2. 本地测试
./btcquant local train

# 3. 提交代码
./btcquant git push

# 4. 更新服务器
./btcquant server update cpu
./btcquant server update gpu

# 5. 重启服务
./btcquant data restart
```

### 训练新模型

```bash
# 1. 更新训练数据
./btcquant data prepare

# 2. 同步到GPU服务器
./btcquant gpu sync-data

# 3. 启动训练
./btcquant gpu train

# 4. 训练完成后同步模型
./btcquant gpu sync-model tcn_20260304_123456
```

### 故障排查

```bash
# 1. 查看服务器状态
./btcquant server status cpu

# 2. 查看容器状态
./btcquant docker ps

# 3. 查看日志
./btcquant server logs cpu data-service

# 4. 监控资源
./btcquant docker monitor

# 5. 重启服务
./btcquant data restart

# 6. 如果问题严重，修复并重新部署
./btcquant fix deploy
```

## 配置

### SSH配置

在 `~/.ssh/config` 中配置服务器别名：

```
Host cpu_server
    HostName 47.236.94.252
    User root
    IdentityFile ~/.ssh/id_rsa

Host gpu_server
    HostName YOUR_GPU_SERVER_IP
    User root
    IdentityFile ~/.ssh/id_rsa
```

### 环境变量

可以通过环境变量覆盖默认配置：

```bash
export CPU_SERVER="cpu_server"
export GPU_SERVER="gpu_server"
export PROJECT_DIR="/root/workspace/btcquant"
```

## 与原有脚本的对应关系

| 原脚本 | 新命令 |
|--------|--------|
| `deploy.sh init` | `btcquant server init cpu` |
| `deploy.sh update` | `btcquant server update cpu` |
| `deploy.sh data` | `btcquant data start` |
| `deploy.sh prepare` | `btcquant data prepare` |
| `deploy.sh status` | `btcquant server status cpu` |
| `deploy.sh logs` | `btcquant server logs cpu` |
| `prepare_training_data.sh` | `btcquant data prepare` |
| `monitor_container.sh` | `btcquant docker monitor` |
| `deploy_gpu_training.sh` | `btcquant gpu train` |
| `setup_gpu_env.sh` | `btcquant gpu setup` |
| `git_deploy.sh` | `btcquant git deploy` |
| `fix_and_deploy.sh` | `btcquant fix deploy` |

## 优势

1. **统一接口**：所有操作通过一个命令完成
2. **清晰分类**：命令按功能分组（server、data、docker、gpu等）
3. **易于记忆**：命令结构一致，符合直觉
4. **彩色输出**：成功/错误/警告有不同颜色
5. **完整帮助**：内置详细的帮助文档
6. **向后兼容**：原有脚本仍然可用

## 故障排除

### 命令找不到

```bash
# 确保脚本有执行权限
chmod +x btcquant

# 使用完整路径
./btcquant help
```

### SSH连接失败

```bash
# 检查SSH配置
cat ~/.ssh/config

# 测试SSH连接
ssh cpu_server "echo 'Connection OK'"
```

### 权限问题

```bash
# 确保有Docker权限
sudo usermod -aG docker $USER

# 重新登录使权限生效
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
