#!/bin/bash
# 一键修复并部署到服务器

set -e

SERVER="cpu_server"
PROJECT_DIR="/root/workspace/btcquant"

echo "=========================================="
echo "修复数据服务容器并部署到服务器"
echo "=========================================="
echo ""
echo "服务器: $SERVER"
echo "项目目录: $PROJECT_DIR"
echo ""

# 1. 提交本地修改
echo "[1/5] 提交本地修改到Git..."
git add docker-compose.yml data/api.py data/service.py prepare_training_data.sh monitor_container.sh CONTAINER_FIX.md
git commit -m "修复数据服务容器内存溢出问题" || echo "没有新的修改需要提交"
git push origin main
echo "✓ 代码已推送"
echo ""

# 2. 连接服务器并更新代码
echo "[2/5] 连接服务器并更新代码..."
ssh $SERVER << 'ENDSSH'
cd /root/workspace/btcquant
echo "当前目录: $(pwd)"
echo "拉取最新代码..."
git pull origin main
echo "✓ 代码已更新"
ENDSSH
echo ""

# 3. 重新构建并启动容器
echo "[3/5] 重新构建并启动容器..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /root/workspace/btcquant

echo "停止现有容器..."
docker-compose down

echo "重新构建数据服务镜像..."
docker-compose build data-service

echo "启动数据服务..."
docker-compose up -d data-service

echo "等待容器启动..."
sleep 5

echo "✓ 容器已启动"
ENDSSH
echo ""

# 4. 检查容器状态
echo "[4/5] 检查容器状态..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /root/workspace/btcquant

echo "容器状态:"
docker ps --filter "name=btc_quant_data_service"

echo ""
echo "资源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" btc_quant_data_service

echo ""
echo "健康检查:"
sleep 2
curl -s http://localhost:8001/health && echo " ✓ 服务正常" || echo " ✗ 服务异常"

echo ""
echo "重启次数:"
docker inspect --format='{{.RestartCount}}' btc_quant_data_service
ENDSSH
echo ""

# 5. 准备训练数据
echo "[5/5] 准备训练数据..."
echo ""
read -p "是否立即执行数据准备？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /root/workspace/btcquant
echo "开始准备训练数据..."
./prepare_training_data.sh
ENDSSH
else
    echo "跳过数据准备，稍后可手动执行："
    echo "  ssh root@47.236.94.252"
    echo "  cd /root/workspace/btcquant"
    echo "  ./prepare_training_data.sh"
fi

echo ""
echo "=========================================="
echo "✓ 部署完成！"
echo "=========================================="
echo ""
echo "监控命令："
echo "  ssh root@47.236.94.252 'cd /root/workspace/btcquant && ./monitor_container.sh'"
echo ""
echo "查看日志："
echo "  ssh root@47.236.94.252 'docker logs -f btc_quant_data_service'"
echo ""
