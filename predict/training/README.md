# 训练脚本目录

此目录包含所有训练相关的脚本。

## 文件说明

- `train.py` - 主训练脚本，支持多种训练模式
- `train_with_notification.py` - 带通知的训练包装脚本
- `post_training.py` - 训练后处理脚本（模型传输、邮件通知）

## 使用方法

### 本地训练
```bash
cd training
python train.py --mode cache
```

### GPU训练（推荐使用btcquant命令）
```bash
# 从项目根目录
btcquant train start --gpu
```

### 训练模式

1. **cache模式** - 使用预先准备的数据缓存（推荐）
   ```bash
   python train.py --mode cache
   ```

2. **full模式** - 从数据服务加载完整数据
   ```bash
   python train.py --mode full
   ```

3. **incremental模式** - 增量训练
   ```bash
   python train.py --mode incremental --base-model ../storage/models/tcn_xxx/best_model.pt
   ```

## 配置

训练配置在根目录的 `config.yaml` 中：

```yaml
predict:
  training:
    batch_size: 128
    learning_rate: 0.001
    epochs: 100
    device: "cuda"
```

## 日志

训练日志输出到：`../../storage/logs/training.log`

查看日志：
```bash
tail -f ../../storage/logs/training.log
```
