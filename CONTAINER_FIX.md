# 数据服务容器重启问题修复

## 问题原因

执行 `prepare_training_data.sh` 时数据服务容器重启，主要原因：

### 1. 内存限制过低（主要原因）
- 原配置：512MB 内存限制
- 问题：处理大量历史数据（2019-01-01至今）时，内存占用超过限制导致容器被 OOM Kill

### 2. API 返回数据量过大
- 原实现：指定时间范围时不限制返回数量
- 问题：一次性返回几万条数据，占用大量内存

### 3. 请求超时时间过长
- 原配置：180秒超时
- 问题：长时间请求导致内存持续增长

### 4. 缺少重试机制
- 原实现：请求失败直接退出
- 问题：容器重启后无法自动恢复

## 修复方案

### 1. 增加容器内存限制
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '0.5'      # 从 0.25 增加到 0.5
      memory: 2G       # 从 512M 增加到 2G
```

### 2. 限制 API 返回数量
```python
# data/api.py
# 限制单次最大返回 5000 条，避免内存溢出
if len(klines) > limit:
    klines = klines[:limit]
```

### 3. 优化数据获取策略
```python
# data/service.py
# 分批获取缺失数据，每批最多 2000 条
max_batch_size = 2000
max_time_range = max_batch_size * interval_ms
```

### 4. 改进脚本重试机制
```python
# prepare_training_data.sh 中的 fetch_training_data.py
- 减少超时时间：180s → 60s
- 增加批次大小：1500 → 2000
- 添加重试机制：最多重试 3 次
- 添加请求延迟：每批间隔 0.1s
```

## 部署步骤

### 服务器信息
- **IP地址：** 47.236.94.252
- **项目目录：** /root/workspace/btcquant
- **配置：** 2核4G，100GB磁盘

### 1. 在服务器上更新代码
```bash
# SSH登录服务器
ssh root@47.236.94.252

# 进入项目目录
cd /root/workspace/btcquant

# 拉取最新代码
git pull origin main
```

### 2. 重新构建并启动容器
```bash
# 停止现有容器
docker-compose down

# 重新构建镜像
docker-compose build data-service

# 启动容器
docker-compose up -d data-service

# 查看容器状态
docker ps
```

### 3. 监控容器状态
```bash
# 使用监控脚本
./monitor_container.sh

# 或手动查看
docker stats btc_quant_data_service
docker logs -f btc_quant_data_service
```

### 4. 重新执行数据准备
```bash
./prepare_training_data.sh
```

## 验证方法

### 1. 检查容器是否稳定运行
```bash
# 查看容器状态（应该是 Up）
docker ps | grep data-service

# 查看重启次数（应该是 0）
docker inspect --format='{{.RestartCount}}' btc_quant_data_service
```

### 2. 监控内存使用
```bash
# 实时监控资源使用
watch -n 2 docker stats --no-stream btc_quant_data_service
```

内存使用应该保持在 2G 以下，正常情况下在 500MB-1.5GB 之间波动。

### 3. 检查数据获取进度
```bash
# 查看日志
docker logs -f btc_quant_data_service

# 查看缓存文件
ls -lh training_data_cache.pkl
```

## 预期结果

- 容器稳定运行，不再重启
- 内存使用在限制范围内
- 数据获取成功完成
- 生成缓存文件 `training_data_cache.pkl`

## 故障排查

### 如果容器仍然重启

1. **查看容器日志**
```bash
docker logs btc_quant_data_service --tail 100
```

2. **检查系统资源**
```bash
# 检查宿主机内存
free -h

# 检查磁盘空间
df -h
```

3. **降低批次大小**
编辑 `prepare_training_data.sh`，将 `batch_size` 从 2000 降低到 1000：
```python
batch_size = 1000  # 减少批次大小
```

4. **分段获取数据**
不要一次性获取所有数据，分段获取：
```bash
# 先获取 2019-2021 的数据
DATA_START_DATE="2019-01-01" DATA_END_DATE="2021-12-31" ./prepare_training_data.sh

# 再获取 2022-2024 的数据
DATA_START_DATE="2022-01-01" DATA_END_DATE="2024-12-31" ./prepare_training_data.sh

# 最后获取 2025 至今的数据
DATA_START_DATE="2025-01-01" ./prepare_training_data.sh
```

### 如果内存仍然不足

进一步增加内存限制：
```yaml
# docker-compose.yml
memory: 4G  # 增加到 4G
```

## 性能优化建议

1. **使用 SSD 存储**：确保数据库文件在 SSD 上，提高 I/O 性能

2. **定期清理日志**：避免日志文件占用过多磁盘空间
```bash
docker logs btc_quant_data_service 2>&1 | tail -1000 > /tmp/recent.log
```

3. **数据库优化**：定期执行 VACUUM 清理数据库
```bash
docker exec btc_quant_data_service sqlite3 /app/data/btc_quant.db "VACUUM;"
```

## 相关文件

- `docker-compose.yml` - 容器配置
- `data/api.py` - API 接口
- `data/service.py` - 数据服务核心逻辑
- `prepare_training_data.sh` - 数据准备脚本
- `monitor_container.sh` - 容器监控脚本
