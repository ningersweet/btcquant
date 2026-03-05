# BTC Quant 项目规范

## 📁 目录结构

```
btc_quant/
├── btcquant                    # 统一命令行工具
├── storage/                    # 统一存储目录
│   ├── logs/                  # 所有日志
│   ├── cache/                 # 数据缓存
│   └── models/                # 训练模型
├── common/                     # 公共模块
├── data/                       # 数据服务
├── predict/                    # 预测服务
│   ├── models/                # 模型模块
│   ├── data/                  # 数据模块
│   ├── evaluation/            # 评估模块
│   ├── utils/                 # 工具模块
│   ├── training/              # 训练脚本
│   ├── api/                   # API服务
│   ├── scripts/               # 工具脚本
│   └── config.py              # 配置管理
├── strategy/                   # 策略服务
├── docs/                      # 项目文档
├── config.yaml                # 统一配置文件
└── PROJECT.md                 # 本文件
```

## ⚙️ 配置管理

### 配置文件位置

```
config.yaml              # 主配置文件（不提交Git）
config.yaml.example      # 配置示例（提交Git）
```

### 配置优先级

```
环境变量 > config.yaml > 默认值
```

### 首次配置

```bash
# 1. 复制示例配置
cp config.yaml.example config.yaml

# 2. 编辑配置
vim config.yaml

# 3. 同步到服务器
btcquant train sync-config  # GPU服务器
```

### 配置更新流程

```bash
# 1. 本地修改
vim config.yaml

# 2. 同步到GPU服务器
btcquant train sync-config

# 3. 重启训练（如需要）
btcquant train stop
btcquant train start --gpu
```

### 重要：配置文件不提交Git

**原因：**
- 包含敏感信息（API密钥、密码）
- 不同环境使用不同配置
- 避免泄露到公开仓库

**检查清单：**
- [ ] config.yaml 在 .gitignore 中
- [ ] 提交前检查 `git status`
- [ ] 配置文件已备份到安全位置

## 💻 代码规范

### 命令行工具

**统一使用 btcquant 命令：**

```bash
# ✅ 推荐
btcquant train start --gpu
btcquant data prepare

# ❌ 不推荐
./deploy_gpu_training.sh
./prepare_data.sh
```

### 训练脚本

**使用统一的 train.py：**

```bash
# ✅ 推荐
python train.py --mode cache
python train.py --mode full
python train.py --mode incremental --base-model path/to/model.pt

# ❌ 不推荐（已废弃）
python train_cached.py
python train_fast.py
```

### Python代码规范

```python
# 文件命名：小写+下划线
data_loader.py

# 类名：大驼峰
class ModelTrainer:
    pass

# 函数名：小写+下划线
def load_data():
    pass

# 常量：大写+下划线
MAX_EPOCHS = 100
```

### 日志管理

**所有日志统一存放：**

```python
from config import Config

config = Config()
log_file = config.get_log_path('training.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
```

**日志位置：**
```
storage/logs/
├── training.log
├── inference.log
├── backtest.log
└── api.log
```

### 配置使用

```python
from config import Config

# 加载配置
config = Config()

# 访问配置
batch_size = config.train_batch_size
alpha = config.label_alpha

# 获取路径
model_dir = config.get_model_path('tcn_20260305')
cache_file = config.get_cache_path('data_cache.pkl')
log_file = config.get_log_path('training.log')
```

## 🔄 工作流程

### 本地开发

```bash
# 1. 修改代码
vim predict/models/model_trainer.py

# 2. 本地测试
python predict/training/train.py --mode cache

# 3. 提交代码
git add .
git commit -m "feat: 优化训练器"
git push origin main

# 4. 更新服务器
btcquant server update gpu
```

### GPU训练流程

```bash
# 1. 准备数据（CPU服务器）
btcquant data prepare

# 2. 同步配置和数据
btcquant train sync-config
btcquant train sync-data

# 3. 启动训练
btcquant train start --gpu

# 4. 监控训练
btcquant train status
btcquant train logs

# 5. 训练完成后自动：
#    - 传输模型到CPU服务器
#    - 发送邮件通知
```

### 配置文件管理

```bash
# 首次部署
cp config.yaml.example config.yaml
vim config.yaml
btcquant train sync-config

# 配置更新
vim config.yaml
btcquant train sync-config

# 配置备份（推荐）
tar -czf config_backup_$(date +%Y%m%d).tar.gz config.yaml
```

## 📝 Git提交规范

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
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具

### 示例

```bash
git commit -m "feat: 添加多核并行标签生成

- 使用multiprocessing实现并行
- 性能提升5-8倍
- 自动检测CPU核心数

Closes #123"
```

### 提交前检查

- [ ] 代码符合规范
- [ ] 添加了必要注释
- [ ] config.yaml 未被提交
- [ ] .env 文件未被提交
- [ ] 测试通过
- [ ] 更新了相关文档

## 🔒 安全规范

### 敏感信息管理

**禁止提交到Git：**
```
config.yaml          # 配置文件
.env                 # 环境变量
*.pkl                # 数据缓存
*.db                 # 数据库文件
*.pem                # 私钥文件
storage/logs/*.log   # 日志文件
```

**使用环境变量：**
```bash
# 邮件配置
export SMTP_SERVER=smtp.gmail.com
export SMTP_USER=your_email@gmail.com
export SMTP_PASSWORD=your_app_password

# Binance API
export BINANCE_API_KEY=your_api_key
export BINANCE_API_SECRET=your_api_secret
```

### 服务器访问

```bash
# 使用SSH密钥
ssh-keygen -t rsa -b 4096
ssh-copy-id gpu_server

# 配置SSH
vim ~/.ssh/config
```

```
Host gpu_server
    HostName YOUR_GPU_IP
    User root
    IdentityFile ~/.ssh/id_rsa
```

## 🚀 性能优化

### 数据处理

- ✅ 大数据集使用多核并行
- ✅ 使用numpy数组进行密集计算
- ✅ 缓存中间结果

```python
# 多核并行标签生成
generator = LabelGenerator(n_jobs=-1)  # 使用所有核心
```

### 模型训练

- ✅ 使用GPU加速
- ✅ 合理设置batch_size
- ✅ 使用早停机制
- ✅ 定期保存checkpoint

```yaml
predict:
  training:
    device: "cuda"
    batch_size: 128
    early_stopping_patience: 10
```

### 推理优化

- ✅ 使用ONNX Runtime
- ✅ 批量推理
- ✅ 缓存模型

```python
# 使用ONNX加速推理
inference = load_inference_model(model_dir, use_onnx=True)
```

## 📊 监控和维护

### 训练监控

```bash
# 查看训练状态
btcquant train status

# 查看训练日志
btcquant train logs

# 实时监控
tail -f storage/logs/training.log
```

### 服务监控

```bash
# 查看服务器状态
btcquant server status gpu

# 查看容器状态
btcquant docker ps

# 监控资源
btcquant docker monitor
```

### 日志清理

```bash
# 保留最近7天
find storage/logs/ -name "*.log" -mtime +7 -delete

# 压缩旧日志
tar -czf logs_backup_$(date +%Y%m%d).tar.gz storage/logs/*.log
```

### 模型管理

```bash
# 保留最近3个模型
cd storage/models
ls -t | grep tcn_ | tail -n +4 | xargs rm -rf
```

## 🐛 故障排查

### 查看日志

```bash
# 训练日志
btcquant train logs
tail -100 storage/logs/training.log

# 服务日志
btcquant server logs cpu data-service
btcquant docker logs data-service
```

### 常见问题

**1. 训练失败**
```bash
# 检查日志
btcquant train logs

# 检查配置
cat config.yaml

# 重新同步配置
btcquant train sync-config
```

**2. 配置文件问题**
```bash
# 检查配置文件是否存在
ls -l config.yaml

# 重新同步
btcquant train sync-config
```

**3. 数据缓存问题**
```bash
# 检查缓存文件
ls -lh storage/cache/data_cache.pkl

# 重新同步
btcquant train sync-data
```

## 📚 文档规范

### 代码文档

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

### README文档

每个模块都应有README：
- 功能说明
- 快速开始
- API文档
- 常见问题

### 文档更新

- 代码变更时同步更新文档
- 重要更新记录在CHANGELOG.md
- 保持文档简洁准确

## 🔄 环境管理

### GPU服务器

**使用venv（不使用conda）：**

```bash
# 初始化环境
btcquant gpu setup

# 手动创建
python3.11 -m venv venv
source venv/bin/activate
pip install -r predict/requirements.txt
```

### Python版本

- **最低要求**: Python 3.11+
- **推荐版本**: Python 3.11

### 依赖管理

```bash
# 安装依赖
pip install -r predict/requirements.txt

# 更新依赖
pip install --upgrade -r predict/requirements.txt

# 导出依赖
pip freeze > predict/requirements.txt
```

## 📦 备份规范

### 代码备份

- ✅ 使用Git版本控制
- ✅ 定期推送到远程仓库
- ✅ 重要版本打tag

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 数据备份

```bash
# 备份数据库
cp data/btc_data.db backups/btc_data_$(date +%Y%m%d).db

# 备份训练数据
cp storage/cache/data_cache.pkl backups/

# 备份模型
tar -czf models_backup_$(date +%Y%m%d).tar.gz storage/models/
```

### 配置备份

```bash
# 加密备份配置
tar -czf - config.yaml | openssl enc -aes-256-cbc -out config_$(date +%Y%m%d).tar.gz.enc
```

## 📋 检查清单

### 开发前

- [ ] 拉取最新代码
- [ ] 检查配置文件
- [ ] 激活虚拟环境

### 提交前

- [ ] 代码符合规范
- [ ] 测试通过
- [ ] 配置文件未提交
- [ ] 文档已更新

### 部署前

- [ ] 配置文件已同步
- [ ] 数据已准备
- [ ] 服务器环境正常

### 训练前

- [ ] GPU环境已初始化
- [ ] 配置文件已同步
- [ ] 训练数据已同步
- [ ] 邮件通知已配置

## 🎯 最佳实践

1. **使用btcquant命令** - 统一的命令行工具
2. **配置文件不提交** - 使用.gitignore
3. **日志统一管理** - storage/logs/
4. **多核并行处理** - 提升性能
5. **GPU训练** - 使用GPU服务器
6. **定期备份** - 代码、数据、配置
7. **监控训练** - 实时查看日志
8. **文档同步** - 代码变更时更新文档

---

**遵循规范，提高效率！** 🚀
