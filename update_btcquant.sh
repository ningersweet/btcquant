#!/bin/bash
# 更新btcquant脚本

# 1. 更新 train_sync_data 函数 (687-694行)
sed -i.bak '687,694c\
train_sync_data() {\
    print_header "同步训练数据到GPU服务器"\
    \
    # 从CPU服务器传输到GPU服务器\
    ssh $CPU_SERVER "scp /root/workspace/btcquant/training_data_cache.pkl $GPU_SERVER:~/workspace/btcquant/storage/cache/data_cache.pkl"\
    \
    # 验证文件\
    ssh $GPU_SERVER "ls -lh ~/workspace/btcquant/storage/cache/data_cache.pkl"\
    \
    print_success "数据同步完成"\
}
' btcquant

# 2. 更新 gpu_setup 函数 (757-803行)
sed -i.bak2 '757,803c\
# 初始化GPU环境\
gpu_setup() {\
    print_header "初始化GPU环境"\
    ssh $GPU_SERVER << '\''EOF'\''\
set -e\
\
# 安装git\
if ! command -v git &> /dev/null; then\
    echo "安装Git..."\
    yum install -y git || apt-get install -y git\
fi\
\
# 安装Python 3.11（如果不存在）\
if ! command -v python3.11 &> /dev/null; then\
    echo "安装Python 3.11..."\
    if command -v yum &> /dev/null; then\
        yum install -y python3.11 python3.11-devel python3.11-pip\
    elif command -v apt-get &> /dev/null; then\
        apt-get update\
        apt-get install -y python3.11 python3.11-venv python3.11-dev\
    fi\
fi\
\
# 克隆或更新代码\
if [ -d ~/workspace/btcquant ]; then\
    echo "更新代码..."\
    cd ~/workspace/btcquant\
    git pull origin main\
else\
    echo "克隆代码..."\
    mkdir -p ~/workspace\
    cd ~/workspace\
    git clone https://github.com/ningersweet/btcquant.git\
    cd btcquant\
fi\
\
# 创建venv环境（使用Python 3.11）\
if [ ! -d ~/workspace/btcquant/venv ]; then\
    echo "创建Python 3.11虚拟环境..."\
    cd ~/workspace/btcquant\
    python3.11 -m venv venv\
fi\
\
# 激活环境并安装依赖\
echo "安装依赖..."\
cd ~/workspace/btcquant\
source venv/bin/activate\
pip install --upgrade pip\
\
# 安装PyTorch GPU版本\
echo "安装PyTorch GPU版本..."\
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118\
\
# 安装项目依赖\
echo "安装项目依赖..."\
pip install -r predict/requirements.txt\
\
# 创建存储目录\
mkdir -p storage/logs storage/cache storage/models\
\
# 验证GPU可用性\
echo ""\
echo "验证PyTorch GPU..."\
python -c "import torch; print(f'\''PyTorch版本: {torch.__version__}'\''); print(f'\''CUDA可用: {torch.cuda.is_available()}'\''); print(f'\''GPU数量: {torch.cuda.device_count()}'\''); print(f'\''GPU名称: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}'\'')"\
\
echo ""\
echo "✓ GPU环境初始化完成"\
echo ""\
echo "下一步："\
echo "1. 同步配置文件: btcquant train sync-config"\
echo "2. 同步训练数据: btcquant train sync-data"\
echo "3. 启动训练: btcquant train start --gpu"\
EOF\
    print_success "GPU环境初始化完成"\
}
' btcquant

echo "✓ btcquant脚本已更新"
echo "备份文件: btcquant.bak, btcquant.bak2"
