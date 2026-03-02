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

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

# 创建项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "创建项目目录: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# 拉取或更新代码
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin main
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
fi

# 构建并启动服务
echo "构建 Docker 镜像..."
docker-compose build

echo "启动服务..."
docker-compose up -d

# 检查服务状态
echo "等待服务启动..."
sleep 10

echo "服务状态:"
docker-compose ps

echo "========================================"
echo "部署完成!"
echo "服务端口:"
echo "  - Data Service:     http://localhost:8001"
echo "  - Features Service: http://localhost:8002"
echo "  - Predict Service:  http://localhost:8003"
echo "  - Strategy Service: http://localhost:8004"
echo "========================================"
