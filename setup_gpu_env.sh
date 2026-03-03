#!/bin/bash
# GPU服务器环境初始化脚本
# 适用于阿里云GPU实例（Ubuntu 20.04 + CUDA）

set -e

echo "=========================================="
echo "BTC Quant - GPU环境初始化"
echo "=========================================="

# 1. 更新系统
echo ""
echo "[1/8] 更新系统包..."
sudo apt-get update
sudo apt-get install -y wget git vim curl

# 2. 检查CUDA
echo ""
echo "[2/8] 检查CUDA环境..."
if command -v nvcc &> /dev/null; then
    echo "✓ CUDA已安装"
    nvcc --version
else
    echo "✗ CUDA未安装，请选择带CUDA的镜像"
    exit 1
fi

if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA驱动已安装"
    nvidia-smi
else
    echo "✗ NVIDIA驱动未安装"
    exit 1
fi

# 3. 安装Miniconda
echo ""
echo "[3/8] 安装Miniconda..."
if [ ! -d "$HOME/miniconda3" ]; then
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p $HOME/miniconda3
    rm /tmp/miniconda.sh
    echo "✓ Miniconda安装完成"
else
    echo "✓ Miniconda已存在"
fi

# 初始化conda
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda init bash
source ~/.bashrc

# 4. 创建Python环境
echo ""
echo "[4/8] 创建Python环境..."
conda create -n btc_quant python=3.10 -y
conda activate btc_quant

# 5. 安装PyTorch (GPU版本)
echo ""
echo "[5/8] 安装PyTorch GPU版本..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 6. 安装项目依赖
echo ""
echo "[6/8] 安装项目依赖..."
pip install pandas numpy scikit-learn requests python-dotenv pyyaml
pip install fastapi uvicorn pydantic
pip install onnx onnxruntime-gpu

# 7. 验证GPU可用性
echo ""
echo "[7/8] 验证PyTorch GPU..."
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU数量: {torch.cuda.device_count()}'); print(f'GPU名称: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# 8. 安装Docker (可选，用于数据服务)
echo ""
echo "[8/8] 安装Docker (可选)..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✓ Docker安装完成"
else
    echo "✓ Docker已安装"
fi

echo ""
echo "=========================================="
echo "环境初始化完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重新登录以激活conda环境"
echo "2. 上传项目代码: scp -r btc_quant user@server:~/"
echo "3. 启动数据服务: docker-compose up -d data-service"
echo "4. 运行训练: conda activate btc_quant && python train_cached.py"
echo ""
echo "快速测试GPU："
echo "  python -c 'import torch; print(torch.cuda.is_available())'"
echo ""
