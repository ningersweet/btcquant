#!/bin/bash
# 快速部署到CPU服务器
# 使用 ssh cpu_server 连接

set -e

SERVER="cpu_server"
PROJECT_DIR="/root/workspace/btcquant"
GIT_REPO="https://github.com/ningersweet/btcquant.git"

echo "=========================================="
echo "BTC Quant - 快速部署"
echo "=========================================="
echo ""
echo "目标服务器: $SERVER"
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查参数
ACTION=${1:-update}

case $ACTION in
    init)
        echo "首次部署..."
        ssh $SERVER << EOF
set -e

# 检查项目目录
if [ -d $PROJECT_DIR ]; then
    echo "✓ 项目目录已存在"
    cd $PROJECT_DIR
    git pull origin main
else
    echo "✓ 克隆项目..."
    mkdir -p /root/workspace
    cd /root/workspace
    git clone $GIT_REPO btcquant
    cd btcquant
fi

# 设置执行权限
chmod +x *.sh 2>/dev/null || true

# 显示当前版本
echo ""
echo "当前版本:"
git log -1 --oneline

echo ""
echo "✓ 代码部署完成"
EOF
        ;;
        
    update)
        echo "更新代码..."
        ssh $SERVER << EOF
set -e
cd $PROJECT_DIR
git pull origin main
echo ""
echo "✓ 代码已更新到最新版本"
git log -1 --oneline
EOF
        ;;
        
    data)
        echo "启动数据服务..."
        ssh $SERVER << EOF
set -e
cd $PROJECT_DIR
docker-compose up -d data-service
sleep 5
docker-compose ps
echo ""
echo "✓ 数据服务已启动"
echo ""
echo "准备训练数据:"
echo "  cd $PROJECT_DIR"
echo "  ./prepare_training_data.sh"
EOF
        ;;
        
    prepare)
        echo "准备训练数据..."
        ssh $SERVER << EOF
set -e
cd $PROJECT_DIR
./prepare_training_data.sh
EOF
        ;;
        
    status)
        echo "检查服务状态..."
        ssh $SERVER << EOF
cd $PROJECT_DIR
echo "Docker服务状态:"
docker-compose ps
echo ""
echo "磁盘使用:"
df -h | grep -E "Filesystem|/dev/"
echo ""
echo "内存使用:"
free -h
echo ""
if [ -f training_data_cache.pkl ]; then
    echo "训练数据缓存:"
    ls -lh training_data_cache.pkl
fi
EOF
        ;;
        
    logs)
        echo "查看日志..."
        SERVICE=${2:-data-service}
        ssh $SERVER << EOF
cd $PROJECT_DIR
docker-compose logs --tail=50 $SERVICE
EOF
        ;;
        
    shell)
        echo "登录服务器..."
        ssh $SERVER
        ;;
        
    *)
        echo "用法: $0 <命令>"
        echo ""
        echo "命令:"
        echo "  init      - 首次部署（克隆代码）"
        echo "  update    - 更新代码（默认）"
        echo "  data      - 启动数据服务"
        echo "  prepare   - 准备训练数据"
        echo "  status    - 查看服务状态"
        echo "  logs      - 查看日志"
        echo "  shell     - SSH登录服务器"
        echo ""
        echo "示例:"
        echo "  $0 init       # 首次部署"
        echo "  $0 update     # 更新代码"
        echo "  $0 data       # 启动数据服务"
        echo "  $0 prepare    # 准备训练数据"
        echo "  $0 status     # 查看状态"
        echo "  $0 logs data-service  # 查看数据服务日志"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="
