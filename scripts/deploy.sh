#!/bin/bash

# BTC Quant 部署脚本
# 服务器: 47.236.94.252
# 项目目录: /root/workspace/btcquant

set -e

PROJECT_DIR="/root/workspace/btcquant"
REPO_URL="https://github.com/ningersweet/btcquant.git"

echo "========================================"
echo "BTC Quant 部署脚本"
echo "========================================"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 检查 docker-compose 或 docker compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "错误: Docker Compose 未安装"
    exit 1
fi

echo "使用 Compose 命令: $COMPOSE_CMD"

# 创建项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "创建项目目录: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# 拉取或更新代码
if [ -d ".git" ]; then
    echo "更新代码..."
    git fetch origin
    git reset --hard origin/main
else
    echo "克隆代码仓库..."
    git clone "$REPO_URL" .
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置 Binance API 密钥"
    echo "vim $PROJECT_DIR/.env"
    echo ""
    echo "配置完成后重新运行此脚本"
    exit 0
fi

# 停止旧容器
echo "停止旧容器..."
$COMPOSE_CMD down 2>/dev/null || true

# 清理旧镜像（可选）
if [ "$1" == "--clean" ]; then
    echo "清理旧镜像..."
    docker system prune -f
fi

# 构建并启动服务
echo "构建 Docker 镜像..."
$COMPOSE_CMD build --no-cache

echo "启动服务..."
$COMPOSE_CMD up -d

# 检查服务状态
echo "等待服务启动..."
sleep 15

echo ""
echo "服务状态:"
$COMPOSE_CMD ps

# 健康检查
echo ""
echo "健康检查:"
for port in 8001; do
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  - 端口 $port: ✓ 健康"
    else
        echo "  - 端口 $port: ✗ 不健康"
    fi
done

echo ""
echo "========================================"
echo "部署完成!"
echo "========================================"
echo ""
echo "服务端口:"
echo "  - Data Service: http://localhost:8001"
echo ""
echo "查看日志:"
echo "  $COMPOSE_CMD logs -f data-service"
echo ""
