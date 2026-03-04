# 工具脚本目录

此目录包含各种辅助脚本。

## 文件说明

- `sync_data.py` - 数据同步脚本
- `check_model.py` - 模型检查脚本

## 使用方法

### 数据同步
```bash
python sync_data.py
```

### 检查模型
```bash
python check_model.py --model-dir ../storage/models/tcn_20260305_120000
```

## 推荐使用btcquant命令

大部分功能已集成到btcquant命令中：

```bash
# 同步数据
btcquant train sync-data

# 查看训练状态
btcquant train status
```
