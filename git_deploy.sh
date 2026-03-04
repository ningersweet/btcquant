#!/bin/bash
# Git方式一键部署到服务器

set -e

echo "=========================================="
echo "BTC Quant - Git部署"
echo "=========================================="
echo ""

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <服务器IP> <服务器类型> [Git分支]"
    echo ""
    echo "服务器类型:"
    echo "  data    - 数据服务器（准备训练数据）"
    echo "  gpu     - GPU训练服务器"
    echo "  infer   - 推理服务器"
    echo ""
    echo "示例:"
    echo "  $0 192.168.1.100 data       # 部署数据服务器"
    echo "  $0 192.168.1.101 gpu main   # 部署GPU服务器（main分支）"
    exit 1
fi

SERVER_IP=$1
SERVER_TYPE=$2
GIT_BRANCH=${3:-main}
GIT_REPO="https://github.com/ningersweet/btcquant.git"

echo "目标服务器: $SERVER_IP"
echo "部署类型: $SERVER_TYPE"
echo "Git分支: $GIT_BRANCH"
echo "Git仓库: $GIT_REPO"
echo ""

# 部署函数
deploy_to_server() {
    ssh root@$SERVER_IP << EOF
set -e

echo "检查项目目录..."
if [ -d ~/btc_quant ]; then
    echo "✓ 项目已存在，更新代码..."
    cd ~/btc_quant
    git fetch origin
    git checkout $GIT_BRANCH
    git pull origin $GIT_BRANCH
    echo "✓ 代码已更新到最新版本"
else
    echo "✓ 首次部署，克隆代码..."
    cd ~
    git clone -b $GIT_BRANCH $GIT_REPO btc_quant
    cd btc_quant
    echo "✓ 代码克隆完成"
fi

# 设置执行权限
chmod +x *.sh 2>/dev/null || true
chmod +x predict/*.sh 2>/dev/null || true

echo ""
echo "当前版本信息:"
git log -1 --oneline
echo ""
EOF
}

# 执行部署
echo "[1/2] 部署/更新代码..."
deploy_to_server

# 根据服务器类型执行相应操作
echo ""
echo "[2/2] 配置服务器..."

case $SERVER_TYPE in
    data)
        echo "配置数据服务器..."
        ssh root@$SERVER_IP << 'DATA_SETUP'
cd ~/btc_quant

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 启动数据服务
echo "启动数据服务..."
docker-compose up -d data-service
sleep 5

# 检查服务状态
docker-compose ps

echo ""
echo "✓ 数据服务器配置完成"
echo ""
echo "下一步："
echo "  cd ~/btc_quant"
echo "  ./prepare_training_data.sh    # 准备训练数据"
DATA_SETUP
        ;;
        
    gpu)
        echo "配置GPU训练服务器..."
        ssh root@$SERVER_IP << 'GPU_SETUP'
cd ~/btc_quant

# 检查GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "✗ 未检测到GPU，请确保使用GPU实例"
    exit 1
fi

echo "✓ GPU检测正常"
nvidia-smi

# 检查是否已初始化环境
if conda env list | grep -q btc_quant; then
    echo "✓ Conda环境已存在"
    conda activate btc_quant
    python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
else
    echo "首次部署，需要初始化GPU环境..."
    echo "运行: ./setup_gpu_env.sh"
fi

echo ""
echo "✓ GPU服务器配置完成"
echo ""
echo "下一步："
echo "  1. 如果是首次部署: ./setup_gpu_env.sh"
echo "  2. 从数据服务器获取数据缓存"
echo "  3. 启动训练: ./deploy_gpu_training.sh"
GPU_SETUP
        ;;
        
    infer)
        echo "配置推理服务器..."
        ssh root@$SERVER_IP << 'INFER_SETUP'
cd ~/btc_quant

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 启动推理服务
echo "启动推理服务..."
docker-compose up -d predict-service
sleep 5

# 检查服务状态
docker-compose ps

echo ""
echo "✓ 推理服务器配置完成"
echo ""
echo "测试API:"
echo "  curl http://localhost:8000/health"
INFER_SETUP
        ;;
        
    *)
        echo "✗ 未知的服务器类型: $SERVER_TYPE"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "SSH登录: ssh root@$SERVER_IP"
echo "项目目录: ~/btc_quant"
echo ""
echo "查看日志:"
echo "  cd ~/btc_quant"
echo "  git log --oneline -10"
echo ""
