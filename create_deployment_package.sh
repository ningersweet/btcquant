#!/bin/bash
# 创建服务器部署包

echo "创建部署包..."

# 创建临时目录
mkdir -p deploy_package

# 复制必要文件
cp -r predict deploy_package/
cp -r data deploy_package/
cp -r common deploy_package/
cp docker-compose.yml deploy_package/
cp requirements.txt deploy_package/ 2>/dev/null || true

# 复制部署脚本
cp setup_gpu_env.sh deploy_package/
cp deploy_gpu_training.sh deploy_package/
cp prepare_training_data.sh deploy_package/

# 复制文档
cp GPU_QUICKSTART.md deploy_package/
cp GPU_TRAINING_GUIDE.md deploy_package/
cp SERVER_DEPLOYMENT_GUIDE.md deploy_package/

# 打包
tar -czf btc_quant_deploy.tar.gz deploy_package/

# 清理
rm -rf deploy_package

echo "✓ 部署包已创建: btc_quant_deploy.tar.gz"
ls -lh btc_quant_deploy.tar.gz
