#!/bin/bash
# 快速部署脚本 - 在GPU服务器上运行
# 假设环境已初始化，快速启动训练

set -e

echo "=========================================="
echo "BTC Quant - 快速训练部署"
echo "=========================================="

# 激活环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate btc_quant

# 进入项目目录
cd ~/btc_quant

# 1. 启动数据服务
echo ""
echo "[1/4] 启动数据服务..."
if command -v docker &> /dev/null; then
    docker-compose up -d data-service
    sleep 5
    echo "✓ 数据服务已启动"
else
    echo "⚠ Docker未安装，跳过数据服务"
fi

# 2. 检查GPU
echo ""
echo "[2/4] 检查GPU状态..."
nvidia-smi
python -c "import torch; assert torch.cuda.is_available(), 'GPU不可用'; print(f'✓ GPU可用: {torch.cuda.get_device_name(0)}')"

# 3. 配置训练参数
echo ""
echo "[3/4] 配置训练参数..."
cd predict

# 修改.env使用GPU
if [ -f .env ]; then
    sed -i 's/TRAIN_DEVICE=cpu/TRAIN_DEVICE=cuda/' .env
    sed -i 's/TRAIN_BATCH_SIZE=256/TRAIN_BATCH_SIZE=1024/' .env
    echo "✓ 配置已更新为GPU模式"
else
    echo "⚠ .env文件不存在"
fi

# 4. 启动训练
echo ""
echo "[4/4] 启动训练..."
echo "训练日志将保存到: training_gpu.log"
echo ""

nohup python train_cached.py > training_gpu.log 2>&1 &
TRAIN_PID=$!

echo "✓ 训练已启动 (PID: $TRAIN_PID)"
echo ""
echo "监控命令："
echo "  tail -f training_gpu.log"
echo "  watch -n 5 nvidia-smi"
echo ""
echo "停止训练："
echo "  kill $TRAIN_PID"
echo ""

# 等待几秒后显示初始日志
sleep 10
echo "初始训练日志："
echo "----------------------------------------"
tail -20 training_gpu.log
echo "----------------------------------------"
