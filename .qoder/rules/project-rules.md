---
trigger: always_on
---
# BTC Quant 项目规则

## 服务器部署信息

### 服务器配置
- **IP 地址**: 47.236.94.252
- **登录方式**: ssh root@47.236.94.252
- **操作系统**: Linux (需登录确认具体版本)
- **CPU**: 2 核 (系统可用 1 核)
- **内存**: 4 GB (系统可用 2 GB)
- **磁盘**: 100 GB
- **已安装**: Docker, Git

### 项目部署
- **项目目录**: /root/workspace/btcquant
- **代码仓库**: https://github.com/ningersweet/btcquant.git
- **拉取方式**: HTTPS (服务端使用)
- **SSH 仓库**: git@github.com:ningersweet/btcquant.git (本地开发使用)

### 资源限制
每个服务的资源限制：
- CPU: 0.25 核
- 内存: 512 MB
- 总计: 1 核 CPU, 2 GB 内存

### 日志配置
- 日志驱动: json-file
- 单文件大小: 10 MB
- 保留文件数: 3

## 开发规范

### 分支管理
- main: 主分支，用于生产部署
- develop: 开发分支
- feature/*: 功能分支

### 部署流程
1. 本地开发完成后推送到 GitHub
2. 登录服务器执行 `git pull`
3. 执行 `docker-compose build && docker-compose up -d`

### 注意事项
- 服务器资源有限，避免运行资源密集型任务
- 前期不考虑高可用和数据备份
- 确保日志正常输出用于问题排查
