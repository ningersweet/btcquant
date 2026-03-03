# Git部署方案

## 🚀 使用Git部署（推荐）

### 优势
- ✅ 无需打包上传
- ✅ 版本控制
- ✅ 增量更新快速
- ✅ 多服务器同步方便

## 📋 部署步骤

### 步骤1：提交代码到Git仓库

```bash
# 在本地Mac执行
cd /Users/lemonshwang/project/btc_quant

# 添加.gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# 环境
.env
venv/
env/

# 数据和模型
*.pkl
*.pth
*.pt
*.onnx
data_storage/
models/*/
!models/.gitkeep

# 日志
*.log
nohup.out

# IDE
.vscode/
.idea/
*.swp
*.swo

# 临时文件
*.tar.gz
deploy_package/

# Mac
.DS_Store
EOF

# 提交代码
git add .
git commit -m "完整的TCN量化交易系统 - 支持GPU训练"
git push origin main
```

### 步骤2：在服务器上克隆代码

```bash
# SSH登录到数据服务器
ssh root@YOUR_DATA_SERVER_IP

# 克隆代码
cd ~
git clone YOUR_GIT_REPO_URL btc_quant
cd btc_quant

# 设置执行权限
chmod +x *.sh

# 启动数据服务
docker-compose up -d data-service

# 准备训练数据
./prepare_training_data.sh
```

### 步骤3：在GPU服务器上克隆代码

```bash
# SSH登录到GPU服务器
ssh root@YOUR_GPU_SERVER_IP

# 克隆代码
cd ~
git clone YOUR_GIT_REPO_URL btc_quant
cd btc_quant

# 初始化GPU环境
./setup_gpu_env.sh

# 从数据服务器获取数据缓存
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
    predict/data_cache.pkl

# 启动训练
./deploy_gpu_training.sh
```

### 步骤4：后续更新（超快！）

```bash
# 在本地修改代码后
git add .
git commit -m "更新训练参数"
git push

# 在服务器上更新
ssh root@YOUR_SERVER
cd ~/btc_quant
git pull
# 完成！无需重新上传
```

## 🔧 自动化部署脚本

### 创建一键Git部署脚本

```bash
#!/bin/bash
# git_deploy.sh - Git方式部署

SERVER_IP=$1
SERVER_TYPE=$2
GIT_REPO=$3

if [ $# -lt 3 ]; then
    echo "用法: $0 <服务器IP> <类型> <Git仓库URL>"
    echo "类型: data | gpu"
    exit 1
fi

echo "通过Git部署到 $SERVER_IP ($SERVER_TYPE)"

# 在服务器上克隆或更新代码
ssh root@$SERVER_IP << EOF
# 检查是否已存在
if [ -d ~/btc_quant ]; then
    echo "更新现有代码..."
    cd ~/btc_quant
    git pull
else
    echo "克隆代码..."
    cd ~
    git clone $GIT_REPO btc_quant
    cd btc_quant
    chmod +x *.sh
fi

# 根据类型执行相应操作
if [ "$SERVER_TYPE" = "data" ]; then
    echo "启动数据服务..."
    docker-compose up -d data-service
    sleep 5
    ./prepare_training_data.sh
elif [ "$SERVER_TYPE" = "gpu" ]; then
    echo "初始化GPU环境..."
    ./setup_gpu_env.sh
fi
EOF

echo "✓ 部署完成"
```

## 📊 Git vs 打包部署对比

| 方式 | 首次部署 | 更新速度 | 版本控制 | 推荐度 |
|------|---------|---------|---------|--------|
| Git | 1-2分钟 | 5-10秒 | ✅ | ⭐⭐⭐⭐⭐ |
| 打包上传 | 2-3分钟 | 1-2分钟 | ❌ | ⭐⭐⭐ |

## 🎯 推荐工作流程

### 开发流程

```bash
# 1. 本地开发和测试
cd /Users/lemonshwang/project/btc_quant
# 修改代码...

# 2. 提交到Git
git add .
git commit -m "优化训练参数"
git push

# 3. 服务器更新（5秒完成）
ssh root@DATA_SERVER "cd ~/btc_quant && git pull"
ssh root@GPU_SERVER "cd ~/btc_quant && git pull"

# 4. 重启服务（如需要）
ssh root@DATA_SERVER "cd ~/btc_quant && docker-compose restart"
```

### 训练流程

```bash
# 1. 更新代码
ssh root@GPU_SERVER "cd ~/btc_quant && git pull"

# 2. 获取最新数据
ssh root@DATA_SERVER "cd ~/btc_quant && ./prepare_training_data.sh"
scp root@DATA_SERVER:~/btc_quant/training_data_cache.pkl \
    root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl

# 3. 启动训练
ssh root@GPU_SERVER "cd ~/btc_quant && ./deploy_gpu_training.sh"
```

## 🔐 Git仓库选择

### 选项1：GitHub（推荐）
```bash
# 创建私有仓库
# 在GitHub上创建新仓库：btc_quant

# 添加远程仓库
git remote add origin git@github.com:YOUR_USERNAME/btc_quant.git
git push -u origin main
```

### 选项2：GitLab
```bash
git remote add origin git@gitlab.com:YOUR_USERNAME/btc_quant.git
git push -u origin main
```

### 选项3：自建Git服务器
```bash
# 在数据服务器上
cd ~
git init --bare btc_quant.git

# 在本地
git remote add origin root@DATA_SERVER:~/btc_quant.git
git push -u origin main
```

## 📝 .gitignore 配置

已为你准备好的 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/

# 数据和模型（不提交到Git）
*.pkl
*.pth
*.pt
*.onnx
data_storage/
models/*/

# 日志
*.log

# 环境配置
.env

# 临时文件
*.tar.gz
```

## ✅ Git部署检查清单

- [ ] 代码已提交到Git仓库
- [ ] .gitignore配置正确
- [ ] 服务器可以访问Git仓库
- [ ] SSH密钥已配置（如使用SSH）
- [ ] 服务器已安装Git

## 🎊 总结

**使用Git部署的优势：**
1. ✅ 更新速度快（5-10秒 vs 1-2分钟）
2. ✅ 版本控制，可回滚
3. ✅ 多服务器同步方便
4. ✅ 团队协作友好

**推荐流程：**
```bash
# 首次部署
git clone YOUR_REPO btc_quant

# 后续更新
cd btc_quant && git pull
```

---

**下一步：提交代码到Git仓库，然后在服务器上 `git clone`** 🚀
