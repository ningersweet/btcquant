#!/bin/bash
# GPU服务器训练启动脚本
# 
# 功能：
# 1. 激活conda环境
# 2. 启动训练（后台运行）
# 3. 训练完成后自动传输模型到CPU服务器
# 4. 发送邮件通知

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}BTC Quant - GPU训练启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否在正确的目录
if [ ! -f "train.py" ]; then
    echo -e "${RED}错误: 请在predict目录下运行此脚本${NC}"
    exit 1
fi

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo -e "${RED}错误: 未找到conda${NC}"
    exit 1
fi

# 激活conda环境
echo -e "${YELLOW}激活conda环境...${NC}"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate btc_quant || {
    echo -e "${RED}错误: 无法激活btc_quant环境${NC}"
    echo -e "${YELLOW}请先运行: btcquant gpu setup${NC}"
    exit 1
}

# 检查GPU
echo -e "${YELLOW}检查GPU状态...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo -e "${YELLOW}警告: 未检测到GPU，将使用CPU训练${NC}"
fi

# 检查环境变量
if [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo -e "${YELLOW}警告: 未设置邮件配置，训练完成后不会发送邮件${NC}"
    echo -e "${YELLOW}设置方法: export \$(cat .env.email | xargs)${NC}"
fi

# 创建存储目录
mkdir -p ../storage/logs ../storage/cache ../storage/models

# 选择训练模式
echo ""
echo "请选择训练模式:"
echo "  1) 使用缓存数据（推荐，快速）"
echo "  2) 完整训练（从数据服务加载）"
echo "  3) 增量训练（在已有模型基础上）"
read -p "请输入选择 [1/2/3]: " train_mode

case $train_mode in
    1)
        MODE="cache"
        ;;
    2)
        MODE="full"
        ;;
    3)
        MODE="incremental"
        read -p "请输入基础模型路径: " base_model
        ;;
    *)
        MODE="cache"
        ;;
esac

# 选择运行模式
echo ""
echo "请选择运行模式:"
echo "  1) 前台运行（可查看实时日志）"
echo "  2) 后台运行（推荐，可关闭SSH）"
read -p "请输入选择 [1/2]: " run_mode

if [ "$run_mode" = "2" ]; then
    # 后台运行
    echo -e "${GREEN}启动后台训练...${NC}"
    
    # 构建命令
    CMD="python train_with_notification.py --mode $MODE"
    if [ "$train_mode" = "3" ] && [ -n "$base_model" ]; then
        CMD="$CMD --base-model $base_model"
    fi
    
    # 保存PID
    nohup $CMD > ../storage/logs/training.log 2>&1 &
    PID=$!
    echo $PID > ~/training.pid
    
    echo -e "${GREEN}✓ 训练已在后台启动${NC}"
    echo -e "  PID: ${PID}"
    echo -e "  日志文件: $(pwd)/../storage/logs/training.log"
    echo ""
    echo "查看实时日志:"
    echo -e "  ${YELLOW}tail -f $(pwd)/../storage/logs/training.log${NC}"
    echo ""
    echo "检查进程状态:"
    echo -e "  ${YELLOW}ps -p $PID${NC}"
    echo ""
    echo "停止训练:"
    echo -e "  ${YELLOW}kill $PID${NC}"
    echo ""
    echo -e "${GREEN}训练完成后会自动传输模型并发送邮件通知${NC}"
    
else
    # 前台运行
    echo -e "${GREEN}启动前台训练...${NC}"
    
    if [ "$train_mode" = "3" ] && [ -n "$base_model" ]; then
        python train_with_notification.py --mode $MODE --base-model $base_model
    else
        python train_with_notification.py --mode $MODE
    fi
fi

echo -e "${GREEN}========================================${NC}"
