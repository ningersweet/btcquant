# BTC Quant 项目规范

## 目录结构规范

```
btc_quant/
├── btcquant                    # 统一命令行工具（主入口）
├── common/                     # 公共模块
├── data/                       # 数据服务
├── predict/                    # 预测服务
│   ├── src/                   # 核心代码
│   ├── models/                # 训练好的模型
│   ├── logs/                  # 日志文件（统一存放）
│   ├── train.py               # 统一训练脚本
│   ├── train_with_notification.py  # 带通知的训练脚本
│   ├── post_training.py       # 训练后处理脚本
│   ├── start_training.sh      # GPU训练启动脚本
│   └── config.py              # 配置管理
├── strategy/                   # 策略服务
└── docs/                      # 文档目录
```

## 代码规范

### 1. 命令行工具

**统一使用 `btcquant` 命令**，不要创建多个独立的shell脚本。

```bash
# ✅ 推荐
btcquant train start --gpu
btcquant data prepare
btcquant server status gpu

# ❌ 不推荐
./deploy_gpu_training.sh
./prepare_training_data.sh
```

### 2. 训练脚本

**只使用一个主训练脚本 `train.py`**，通过参数控制不同模式。

```bash
# ✅ 推荐
python train.py --mode cache
python train.py --mode full
python train.py --mode incremental --base-model models/tcn_xxx/best_model.pt

# ❌ 不推荐
python train_cached.py
python train_fast.py
python train_incremental.py
```

**已废弃的训练脚本（将被删除）：**
- `train_cached.py` → 使用 `train.py --mode cache`
- `train_fast.py` → 使用 `train.py --mode cache`
- `train_db.py` → 使用 `train.py --mode full`
- `train_incremental.py` → 使用 `train.py --mode incremental`
- `train_mock.py` → 仅用于测试

### 3. 日志管理

**所有日志统一存放在 `logs/` 目录**。

```
predict/logs/
├── training.log              # 训练日志
├── inference.log             # 推理日志
└── backtest.log              # 回测日志
```

**日志配置：**
```python
import logging
from pathlib import Path

log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'training.log'),
        logging.StreamHandler()
    ]
)
```

### 4. 配置管理

**使用 YAML 配置文件统一管理配置**。

```python
from config import Config

# 使用默认配置文件 (config.yaml)
config = Config()

# 使用指定配置文件
config = Config('custom_config.yaml')

# 访问配置
print(config.label_alpha)
print(config.train_batch_size)

# 使用点号路径访问
value = config.get('predict.label.alpha')

# 设置配置
config.set('predict.training.epochs', 50)

# 保存配置
config.save_to_file('my_config.yaml')
```

**配置文件示例 (config.yaml)：**
```yaml
predict:
  label:
    alpha: 0.0015
    gamma: 0.0040
  training:
    batch_size: 128
    epochs: 100
    device: "cuda"
```

**邮件配置（通过环境变量）：**
```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export TO_EMAIL=your_email@gmail.com
```

**向后兼容：**
旧代码仍然可以使用：
```python
from config import label_config, train_config

print(label_config.ALPHA)
print(train_config.BATCH_SIZE)
```

### 5. 模型管理

**模型命名规范：**
```
models/tcn_YYYYMMDD_HHMMSS/
├── best_model.pt              # 最佳模型
├── final_model.pt             # 最终模型（可选）
├── model.onnx                 # ONNX模型（可选）
├── training_history.json      # 训练历史
└── backtest_metrics.json      # 回测指标
```

## 工作流程规范

### 本地开发流程

```bash
# 1. 修改代码
vim predict/src/model_trainer.py

# 2. 本地测试
python predict/train.py --mode cache

# 3. 提交代码
git add .
git commit -m "优化训练器"
git push origin main

# 4. 部署到服务器
btcquant server update cpu
btcquant server update gpu
```

### GPU训练流程

```bash
# 1. 准备数据（在CPU服务器）
btcquant data prepare

# 2. 同步数据到GPU服务器
btcquant train sync-data

# 3. 启动GPU训练
btcquant train start --gpu

# 4. 查看训练状态
btcquant train status
btcquant train logs

# 5. 训练完成后自动：
#    - 传输模型到CPU服务器
#    - 发送邮件通知
#    - 可以释放GPU服务器
```

### 模型部署流程

```bash
# 1. 训练完成后，模型已自动同步到CPU服务器

# 2. 重启推理服务
btcquant server shell cpu
cd /root/workspace/btcquant
docker-compose restart predict-service

# 3. 验证推理服务
curl http://localhost:8003/health
```

## 文件命名规范

### Python文件

- 模块文件：小写+下划线，如 `data_loader.py`
- 类名：大驼峰，如 `class ModelTrainer`
- 函数名：小写+下划线，如 `def load_data()`
- 常量：大写+下划线，如 `MAX_EPOCHS = 100`

### Shell脚本

- 统一使用 `btcquant` 命令，避免创建独立脚本
- 如必须创建，使用小写+下划线，如 `setup_env.sh`

### 配置文件

- `.env` - 环境变量配置
- `.env.example` - 环境变量示例
- `config.yaml` - YAML配置文件
- `config.yaml.example` - YAML配置示例

## Git提交规范

### 提交信息格式

```
<类型>: <简短描述>

<详细描述>

<相关Issue>
```

### 类型标签

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
git commit -m "feat: 添加多核并行标签生成

- 使用multiprocessing实现并行处理
- 性能提升5-8倍
- 自动检测CPU核心数

Closes #123"
```

## 代码审查清单

提交代码前检查：

- [ ] 代码符合PEP 8规范
- [ ] 添加了必要的注释和文档字符串
- [ ] 日志输出到统一的logs目录
- [ ] 使用config.py管理配置
- [ ] 没有硬编码的路径和密码
- [ ] 测试通过
- [ ] 更新了相关文档

## 性能优化规范

### 1. 数据处理

- 大数据集使用多核并行处理
- 使用numpy数组而非pandas DataFrame进行密集计算
- 缓存中间结果避免重复计算

### 2. 模型训练

- 使用GPU加速（如果可用）
- 合理设置batch_size
- 使用早停机制避免过拟合
- 定期保存checkpoint

### 3. 推理优化

- 使用ONNX Runtime加速推理
- 批量推理而非单条推理
- 缓存模型避免重复加载

## 安全规范

### 1. 敏感信息

**禁止提交到Git：**
- `.env` 文件（包含密码、API密钥）
- 数据库文件
- 训练数据缓存
- 私钥文件

**使用 .gitignore：**
```
.env
*.pkl
*.db
*.pem
logs/*.log
```

### 2. 服务器访问

- 使用SSH密钥而非密码
- 定期更新服务器
- 限制端口访问
- 使用防火墙

## 文档规范

### 1. 代码文档

每个模块、类、函数都应有文档字符串：

```python
def train_model(train_df, val_df, config):
    """
    训练TCN模型
    
    Args:
        train_df: 训练数据集
        val_df: 验证数据集
        config: 配置对象
        
    Returns:
        训练历史记录
        
    Raises:
        ValueError: 如果数据集为空
    """
    pass
```

### 2. README文档

每个子项目都应有README：
- 功能说明
- 快速开始
- 配置说明
- API文档
- 常见问题

### 3. 更新日志

重要更新应记录在CHANGELOG.md：
```markdown
## [1.1.0] - 2026-03-05

### Added
- 多核并行标签生成
- 训练完成自动化处理

### Changed
- 统一训练脚本

### Deprecated
- train_cached.py, train_fast.py等旧脚本
```

## 测试规范

### 1. 单元测试

```python
import pytest

def test_label_generator():
    """测试标签生成器"""
    generator = LabelGenerator()
    df = load_test_data()
    result = generator.generate_labels(df)
    
    assert 'y_dir' in result.columns
    assert len(result) == len(df)
```

### 2. 集成测试

```bash
# 测试完整训练流程
python train.py --mode cache --epochs 1

# 测试推理服务
curl http://localhost:8003/predict -d @test_data.json
```

## 监控规范

### 1. 训练监控

- 记录训练损失和准确率
- 监控GPU/CPU使用率
- 记录训练时间
- 保存训练历史

### 2. 服务监控

- 健康检查端点
- 请求响应时间
- 错误率统计
- 资源使用监控

## 备份规范

### 1. 代码备份

- 使用Git版本控制
- 定期推送到远程仓库
- 重要版本打tag

### 2. 数据备份

- 定期备份数据库
- 保存训练数据缓存
- 备份训练好的模型

### 3. 配置备份

- 备份.env文件（加密存储）
- 备份服务器配置
- 文档化部署流程

## 故障处理规范

### 1. 日志查看

```bash
# 查看训练日志
btcquant train logs

# 查看服务日志
btcquant server logs cpu data-service

# 查看容器日志
btcquant docker logs data-service
```

### 2. 问题排查

1. 检查日志文件
2. 检查服务状态
3. 检查资源使用
4. 查看错误堆栈
5. 搜索相关Issue

### 3. 回滚流程

```bash
# 回滚代码
git checkout <commit-id>
btcquant server update cpu

# 回滚模型
cp models/tcn_old/best_model.pt models/current/
docker-compose restart predict-service
```

## 更新记录

- 2026-03-05: 初始版本
- 统一命令行工具
- 整合训练脚本
- 规范日志目录
