#!/bin/bash
# GPU服务器环境初始化脚本
# 使用Python venv代替conda

set -e

echo "=========================================="
echo "GPU环境初始化"
echo "=========================================="
echo ""

# 检查CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo "✗ 未检测到NVIDIA GPU"
    exit 1
fi

echo "GPU信息:"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
echo ""

# 检查Python 3.11
echo "[1/4] 检查Python环境..."
if ! command -v python3.11 &> /dev/null; then
    echo "安装Python 3.11..."
    sudo yum install -y python3.11 python3.11-pip python3.11-devel
fi

python3.11 --version
echo "✓ Python已准备"

# 创建虚拟环境
echo ""
echo "[2/4] 创建虚拟环境..."
cd /root/workspace/btcquant

if [ -d "venv" ]; then
    echo "虚拟环境已存在"
else
    echo "创建新虚拟环境..."
    python3.11 -m venv venv
fi

source venv/bin/activate
echo "✓ 虚拟环境已激活"
python --version

# 安装PyTorch GPU版本
echo ""
echo "[3/4] 安装PyTorch GPU..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 验证GPU
echo ""
echo "验证PyTorch GPU支持:"
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}'); print(f'GPU名称: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# 安装项目依赖
echo ""
echo "[4/4] 安装项目依赖..."
cd /root/workspace/btcquant/predict
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✓ GPU环境初始化完成！"
echo "=========================================="
echo ""
echo "环境信息:"
echo "  Python: $(python --version)"
echo "  PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo "  CUDA: $(python -c 'import torch; print(torch.version.cuda)')"
echo "  GPU: $(python -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\")')"
echo ""
echo "激活环境:"
echo "  source /root/workspace/btcquant/venv/bin/activate"
echo ""
echo "下一步:"
echo "  1. 同步训练数据: ssh cpu_server 'cat /root/workspace/btcquant/training_data_cache.pkl' > predict/data_cache.pkl"
echo "  2. 启动训练: cd predict && python train_cached.py"
echo ""
