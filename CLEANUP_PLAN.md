# 文档清理计划

## 需要删除的文档（过时/重复）

### 部署相关（已整合到 PROJECT_STANDARDS.md）
- [x] DEPLOY_QUICKSTART.md - 已过时，使用 btcquant 命令
- [x] GIT_DEPLOY_GUIDE.md - 已过时，使用 btcquant 命令
- [x] GPU_TRAINING_GUIDE.md - 已整合到 TRAINING_AUTOMATION.md
- [x] GPU_QUICKSTART.md - 已整合到 TRAINING_AUTOMATION.md

### 配置相关（已整合）
- [x] CONFIG.md - 已整合到 PROJECT_STANDARDS.md
- [x] CONFIG_OPTIMIZATION_SUMMARY.md - 临时文档，可删除

### 容器相关
- [x] CONTAINER_FIX.md - 临时修复文档，可删除

### 工作总结（临时文档）
- [x] WORK_SUMMARY.md - 临时文档，可删除
- [x] DOCS_CLEANUP_SUMMARY.md - 临时文档，可删除
- [x] DOCS_ACCURACY_REPORT.md - 临时文档，可删除

### CLI相关
- [x] BTCQUANT_CLI.md - 已整合到 btcquant help

## 需要保留的核心文档

### 根目录
- README.md - 项目主文档
- PROJECT_STANDARDS.md - 项目规范（新）
- QUICKSTART.md - 快速开始
- 项目设计.md - 项目设计文档

### predict/
- predict/README.md - 预测服务文档
- predict/QUICKSTART.md - 快速开始
- predict/TRAINING_AUTOMATION.md - 训练自动化文档
- predict/TRAINING_REPORT.md - 训练报告
- predict/模型设计.md - 模型设计
- predict/特征工程.md - 特征工程

### docs/
- docs/INDEX.md - 文档索引
- docs/系统设计.md - 系统设计
- docs/部署指南.md - 部署指南
- docs/特征工程详细文档.md - 特征工程详细
- docs/超参数优化指南.md - 超参数优化
- docs/模型训练与评估详细文档.md - 模型训练详细

### 其他模块
- data/README.md - 数据服务文档
- features/README.md - 特征服务文档
- strategy/README.md - 策略服务文档
- evaluation/README.md - 评估服务文档

## 需要删除的Shell脚本（已整合到 btcquant）

- [x] deploy.sh - 使用 btcquant server init
- [x] deploy_to_server.sh - 使用 btcquant server update
- [x] deploy_gpu_training.sh - 使用 btcquant train start --gpu
- [x] fix_and_deploy.sh - 使用 btcquant fix deploy
- [x] git_deploy.sh - 使用 btcquant git deploy
- [x] monitor_container.sh - 使用 btcquant docker monitor
- [x] prepare_training_data.sh - 使用 btcquant data prepare
- [x] setup_gpu_env.sh - 使用 btcquant gpu setup

保留：
- scripts/deploy.sh - 可能有特殊用途，暂时保留

## 需要删除的训练脚本（已整合到 train.py）

- [x] predict/train_cached.py - 使用 train.py --mode cache
- [x] predict/train_db.py - 使用 train.py --mode full
- [x] predict/train_fast.py - 使用 train.py --mode cache
- [x] predict/train_incremental.py - 使用 train.py --mode incremental
- [x] predict/train_mock.py - 仅测试用，可保留或删除

保留：
- predict/train.py - 主训练脚本
- predict/train_with_notification.py - 带通知的训练脚本
- predict/post_training.py - 训练后处理
- predict/start_training.sh - GPU训练启动脚本

## 需要删除的其他文件

- [x] predict/watch_fast.sh - 已过时
- [x] predict/*.log - 移动到 logs/ 目录
