# 快速启动指南

## 1. 启动数据服务并同步历史数据

```bash
# 启动数据服务容器
docker-compose up -d data-service

# 等待服务启动（约10秒）
sleep 10

# 同步历史数据（2019年至今）
curl -X POST "http://localhost:8001/api/v1/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "start_date": "2019-01-01"
  }'
```

## 2. 安装依赖

```bash
cd predict
pip install -r requirements.txt
```

## 3. 配置环境变量

```bash
# .env 文件已经创建，可以根据需要调整参数
# 默认配置已经是推荐值，可以直接使用
cat .env
```

## 4. 开始训练

```bash
# 完整训练流程（包含数据获取、标签生成、训练、回测）
python train.py

# 训练完成后，模型会保存在 models/tcn_YYYYMMDD_HHMMSS/ 目录
```

## 5. 查看训练结果

训练完成后会自动输出：
- 训练历史（training_history.json）
- 最佳模型（best_model.pt）
- ONNX模型（model.onnx）
- 回测指标（backtest_metrics.json）

## 6. 使用模型进行推理

```python
from pathlib import Path
from src.inference import load_inference_model
import pandas as pd
import requests

# 加载模型
model_dir = Path('models/tcn_20240101_120000')  # 替换为实际目录
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
编辑 `.env` 文件，减小以下参数：
```
TRAIN_BATCH_SIZE=64  # 从128减小到64
DATA_WINDOW_SIZE=144  # 从288减小到144（12小时）
```

### 训练速度太慢
- 使用GPU：修改 `TRAIN_DEVICE=cuda`
- 减少训练轮数：`TRAIN_EPOCHS=50`
- 减少模型层数：`MODEL_NUM_LAYERS=6`

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
