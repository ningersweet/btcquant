# 快速启动指南

## 1. 安装依赖

```bash
cd predict
pip install -r requirements.txt
```

## 2. 配置

```bash
# 复制配置文件
cp config.yaml.example config.yaml

# 编辑配置（可选，默认配置已经可用）
vim config.yaml
```

## 3. 开始训练

### 方式1：使用缓存数据（推荐，快速）

```bash
# 确保有数据缓存文件
ls -lh data_cache.pkl

# 开始训练
python train.py --mode cache
```

### 方式2：从数据服务加载（完整训练）

```bash
# 确保数据服务运行
curl http://localhost:8001/health

# 开始训练
python train.py --mode full
```

### 方式3：增量训练

```bash
# 在已有模型基础上继续训练
python train.py --mode incremental --base-model models/tcn_20260305_005329/best_model.pt
```

## 4. 查看训练日志

```bash
# 实时查看
tail -f logs/training.log

# 查看最后100行
tail -100 logs/training.log
```

## 5. 使用模型进行推理

```python
from pathlib import Path
from src.inference import load_inference_model
import pandas as pd
import requests

# 加载模型
model_dir = Path('models/tcn_20260305_005329')
inference = load_inference_model(model_dir, use_onnx=True)

# 获取最近的K线数据
response = requests.get('http://localhost:8001/api/v1/klines', params={
    'symbol': 'BTCUSDT',
    'interval': '5m',
    'limit': 288
})
klines_data = response.json()['data']
klines = pd.DataFrame(klines_data)

# 预测
prediction = inference.predict(klines)
print(f"方向: {['Hold', 'Long', 'Short'][prediction['direction']]}")
print(f"置信度: {prediction['confidence']:.2%}")

# 计算订单价格
current_price = klines.iloc[-1]['close']
order = inference.calculate_order_prices(prediction, current_price)
if order:
    print(f"\n交易信号:")
    print(f"  方向: {order['side']}")
    print(f"  入场价: {order['entry_price']:.2f}")
    print(f"  止盈价: {order['tp_price']:.2f}")
    print(f"  止损价: {order['sl_price']:.2f}")
    print(f"  盈亏比: {order['rr_ratio']:.2f}")
else:
    print("无交易信号")
```

## 配置说明

主要配置项在 `config.yaml` 中：

```yaml
predict:
  label:
    alpha: 0.0015      # 入场缓冲系数
    gamma: 0.0040      # 止盈缓冲系数
    beta: 0.0025       # 止损缓冲系数
    theta_min: 0.0100  # 最小净利阈值
    K: 12              # 预测窗口长度
  
  training:
    batch_size: 128    # 批次大小
    learning_rate: 0.001  # 学习率
    epochs: 100        # 训练轮数
    device: "cpu"      # 设备（cpu/cuda）
```

## 故障排查

### 数据服务无法连接
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs data-service

# 重启服务
docker-compose restart data-service
```

### 训练过程中内存不足

编辑 `config.yaml`，减小以下参数：
```yaml
predict:
  training:
    batch_size: 64  # 从128减小到64
  data:
    window_size: 144  # 从288减小到144（12小时）
```

### 训练速度太慢
- 使用GPU：修改 `config.yaml` 中 `device: "cuda"`
- 减少训练轮数：`epochs: 50`
- 减少模型层数：`num_layers: 6`

## 超参数优化（可选）

如果想找到最优超参数：

```python
from src.hyperparameter_tuner import tune_hyperparameters
from src.data_loader import split_data
import pandas as pd

# 加载数据
df = pd.read_csv('your_data.csv')  # 或从API获取

# 划分数据集
train_df, val_df, test_df = split_data(df, 0.7, 0.15, 0.15)

# 运行优化（50次试验）
best_params = tune_hyperparameters(
    train_df, val_df,
    window_size=288,
    n_trials=50,
    device='cpu',
    save_path=Path('best_params.json')
)

print(best_params)
```

## 下一步

1. 训练完成后，检查回测指标是否满足要求：
   - 胜率 > 45%
   - 最大回撤 < 15%
   - 盈利因子 > 1.5
   - 夏普比率 > 1.5

2. 如果指标不理想，可以：
   - 调整标签生成参数（α, γ, β, θ_min）
   - 增加训练数据量
   - 运行超参数优化
   - 调整损失函数权重

3. 指标满意后，可以部署到策略服务进行实盘测试
