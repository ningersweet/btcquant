# 🚀 BTC Quant 快速开始

## 统一命令行工具已就绪！

所有脚本功能已整合到 `btcquant` 命令中。

## 当前状态

✅ **数据服务运行正常**
- 容器状态：健康
- 内存使用：463MB / 2GB
- 数据库：753,598 条 K线数据
- 完整度：99.89%
- 时间范围：2019-01-01 至 2026-03-04

✅ **代码已修复**
- 内存限制：512MB → 2GB
- API端点：期货API → 现货API
- 批量获取：优化重试机制

## 快速命令

### 查看帮助
```bash
./btcquant help
```

### 服务器管理
```bash
# 查看服务器状态
./btcquant server status cpu

# 更新代码
./btcquant server update cpu

# SSH登录
./btcquant server shell cpu
```

### 数据服务
```bash
# 查看数据服务状态
./btcquant data status

# 重启数据服务
./btcquant data restart

# 准备训练数据（已完成，数据充足）
./btcquant data prepare
```

### Docker管理
```bash
# 查看容器状态
./btcquant docker ps

# 监控容器资源
./btcquant docker monitor

# 查看日志
./btcquant docker logs data-service
```

### GPU训练
```bash
# 同步训练数据到GPU服务器
./btcquant gpu sync-data

# 启动GPU训练
./btcquant gpu train
```

## 下一步：申请GPU服务器

数据已准备就绪（753K+ 条），现在可以：

1. **申请GPU服务器**
   - 推荐：T4 16GB
   - 平台：AutoDL / 恒源云 / 阿里云
   - 成本：约 2-3 元/小时

2. **配置GPU服务器SSH**
   ```bash
   # 编辑 ~/.ssh/config
   Host gpu_server
       HostName YOUR_GPU_IP
       User root
       IdentityFile ~/.ssh/id_rsa
   ```

3. **部署到GPU服务器**
   ```bash
   # 首次部署
   ./btcquant server init gpu
   
   # 初始化GPU环境
   ./btcquant gpu setup
   
   # 同步训练数据
   ./btcquant gpu sync-data
   
   # 启动训练
   ./btcquant gpu train
   ```

## 命令速查表

| 操作 | 命令 |
|------|------|
| 查看帮助 | `./btcquant help` |
| 服务器状态 | `./btcquant server status cpu` |
| 数据服务状态 | `./btcquant data status` |
| 容器监控 | `./btcquant docker monitor` |
| 查看日志 | `./btcquant docker logs data-service` |
| 更新代码 | `./btcquant server update cpu` |
| SSH登录 | `./btcquant server shell cpu` |
| GPU训练 | `./btcquant gpu train` |

## 故障排查

### 查看完整状态
```bash
./btcquant server status cpu
./btcquant data status
./btcquant docker ps
```

### 查看日志
```bash
./btcquant docker logs data-service
```

### 重启服务
```bash
./btcquant data restart
```

### 监控资源
```bash
./btcquant docker monitor
```

## 原有脚本对照

| 原脚本 | 新命令 |
|--------|--------|
| `deploy.sh status` | `./btcquant server status cpu` |
| `deploy.sh data` | `./btcquant data start` |
| `prepare_training_data.sh` | `./btcquant data prepare` |
| `monitor_container.sh` | `./btcquant docker monitor` |
| `deploy_gpu_training.sh` | `./btcquant gpu train` |

## 总结

✅ **已完成**
- 修复容器内存溢出问题
- 修复API端点错误
- 准备训练数据（753K+ 条）
- 创建统一命令行工具

🎯 **下一步**
- 申请GPU服务器
- 部署并启动训练
- 评估模型效果

---

**所有功能已整合到 `btcquant` 命令，开始使用吧！** 🚀
