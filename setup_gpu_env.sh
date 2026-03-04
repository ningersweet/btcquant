#!/bin/bash
# GPU服务器环境初始化脚本
# 安装Miniconda和PyTorch GPU环境

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

# 安装Miniconda
if ! command -v conda &> /dev/null; then
    echo "[1/4] 安装Miniconda..."
    cd /tmp
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
    rm Miniconda3-latest-Linux-x86_64.sh
    
    # 初始化conda
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
    conda init bash
    
    echo "✓ Miniconda已安装"
    echo ""
    echo "⚠️  请重新登录以激活conda环境，然后继续执行："
    echo "   ssh gpu_server"
    echo "   cd /root/workspace/btcquant"
    echo "   ./setup_gpu_env.sh"
    exit 0
else
    echo "[1/4] Conda已安装"
    eval "$(conda shell.bash hook)"
fi

# 创建conda环境
echo ""
echo "[2/4] 创建Python环境..."

# 配置conda使用conda-forge，避免服务条款问题
conda config --set channel_priority flexible
conda config --remove channels defaults 2>/dev/null || true
conda config --add channels conda-forge

if conda env list | grep -q "btc_quant"; then
    echo "环境已存在，更新..."
    conda activate btc_quant
else
    echo "创建新环境..."
    conda create -n btc_quant python=3.11 -y
    conda activate btc_quant
fi

echo "✓ Python环境已准备"
python --version

# 安装PyTorch GPU版本
echo ""
echo "[3/4] 安装PyTorch GPU..."
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
echo "下一步:"
echo "  1. 同步训练数据: ./btcquant gpu sync-data"
echo "  2. 启动训练: ./btcquant gpu train"
echo ""
