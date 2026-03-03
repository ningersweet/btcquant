#!/bin/bash
# 一键部署到服务器

echo "=========================================="
echo "BTC Quant 服务器一键部署"
echo "=========================================="
echo ""

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <服务器IP> [服务器类型]"
    echo ""
    echo "服务器类型:"
    echo "  data    - 数据服务器（准备训练数据）"
    echo "  gpu     - GPU训练服务器"
    echo "  all     - 全部部署（默认）"
    echo ""
    echo "示例:"
    echo "  $0 192.168.1.100 data    # 部署到数据服务器"
    echo "  $0 192.168.1.101 gpu     # 部署到GPU服务器"
    exit 1
fi

SERVER_IP=$1
SERVER_TYPE=${2:-all}

echo "目标服务器: $SERVER_IP"
echo "部署类型: $SERVER_TYPE"
echo ""

# 1. 上传部署包
echo "[1/3] 上传部署包..."
scp btc_quant_deploy.tar.gz root@$SERVER_IP:~/
echo "✓ 上传完成"

# 2. 解压并设置权限
echo ""
echo "[2/3] 解压部署包..."
ssh root@$SERVER_IP << 'REMOTE_COMMANDS'
cd ~
tar -xzf btc_quant_deploy.tar.gz
mv deploy_package btc_quant
cd btc_quant
chmod +x *.sh
echo "✓ 解压完成"
REMOTE_COMMANDS

# 3. 根据服务器类型执行相应操作
echo ""
echo "[3/3] 执行部署..."

case $SERVER_TYPE in
    data)
        echo "部署数据服务器..."
        ssh root@$SERVER_IP << 'DATA_DEPLOY'
cd ~/btc_quant
# 启动数据服务
docker-compose up -d data-service
sleep 5
# 准备训练数据
./prepare_training_data.sh
DATA_DEPLOY
        echo "✓ 数据服务器部署完成"
        echo ""
        echo "训练数据已准备好，位于: ~/btc_quant/training_data_cache.pkl"
        ;;
        
    gpu)
        echo "部署GPU训练服务器..."
        ssh root@$SERVER_IP << 'GPU_DEPLOY'
cd ~/btc_quant
# 初始化GPU环境
./setup_gpu_env.sh
GPU_DEPLOY
        echo "✓ GPU服务器环境初始化完成"
        echo ""
        echo "下一步："
        echo "1. 从数据服务器传输训练数据"
        echo "2. 运行 ./deploy_gpu_training.sh 开始训练"
        ;;
        
    all)
        echo "执行完整部署..."
        ssh root@$SERVER_IP << 'ALL_DEPLOY'
cd ~/btc_quant
# 检查是否有GPU
if command -v nvidia-smi &> /dev/null; then
    echo "检测到GPU，初始化GPU环境..."
    ./setup_gpu_env.sh
else
    echo "未检测到GPU，部署数据服务..."
    docker-compose up -d data-service
    sleep 5
    ./prepare_training_data.sh
fi
ALL_DEPLOY
        echo "✓ 部署完成"
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
