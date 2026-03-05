# 贡献指南

感谢你考虑为 BTC Quant 项目做出贡献！

## 🚀 快速开始

### 1. Fork 项目

点击右上角的 Fork 按钮，将项目 fork 到你的账号下。

### 2. 克隆代码

```bash
git clone https://github.com/YOUR_USERNAME/btcquant.git
cd btcquant
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 4. 开发和测试

```bash
# 安装依赖
cd predict
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 本地训练测试
python training/train.py --mode cache --epochs 1
```

### 5. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

### 6. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述你的更改。

## 📝 提交规范

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
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
git commit -m "feat: 添加LSTM模型支持

- 实现LSTM模型架构
- 添加LSTM训练器
- 更新配置文件支持LSTM参数

Closes #42"
```

## 💻 代码规范

### Python代码

遵循 PEP 8 规范：

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

# 文档字符串
def train_model(data, config):
    """
    训练模型
    
    Args:
        data: 训练数据
        config: 配置对象
        
    Returns:
        训练历史
    """
    pass
```

### 代码检查

提交前运行代码检查：

```bash
# 格式检查
flake8 predict/

# 类型检查
mypy predict/

# 代码格式化
black predict/
```

## 🧪 测试规范

### 单元测试

为新功能添加单元测试：

```python
import pytest
from predict.models import TCNModel

def test_tcn_model_forward():
    """测试TCN模型前向传播"""
    model = TCNModel(input_dim=5, num_channels=32)
    x = torch.randn(16, 288, 5)  # (batch, seq, features)
    output = model(x)
    
    assert output.shape == (16, 4)  # (batch, outputs)
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_model.py

# 查看覆盖率
pytest --cov=predict tests/
```

## 📚 文档规范

### 代码文档

所有公共函数、类都应有文档字符串：

```python
def generate_labels(df, alpha=0.0015, gamma=0.0040):
    """
    生成交易标签
    
    Args:
        df: K线数据DataFrame
        alpha: 入场缓冲系数
        gamma: 止盈缓冲系数
        
    Returns:
        带标签的DataFrame
        
    Raises:
        ValueError: 如果数据为空
        
    Example:
        >>> df = load_klines()
        >>> df_labeled = generate_labels(df)
    """
    pass
```

### README更新

如果添加了新功能，更新相关README：

- 根目录 README.md - 项目总览
- 模块 README.md - 模块说明
- docs/ - 详细文档

## 🔍 代码审查

### 审查清单

提交 PR 前自查：

- [ ] 代码符合PEP 8规范
- [ ] 添加了必要的注释和文档
- [ ] 添加了单元测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 没有提交敏感信息（密码、密钥）
- [ ] 没有提交配置文件（config.yaml）
- [ ] 提交信息清晰明确

### PR描述模板

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 变更描述
简要描述你的更改...

## 测试
描述如何测试你的更改...

## 相关Issue
Closes #123

## 截图（如适用）
```

## 🐛 报告Bug

### Bug报告模板

```markdown
## Bug描述
清晰简洁地描述bug...

## 复现步骤
1. 执行 '...'
2. 点击 '...'
3. 看到错误 '...'

## 预期行为
描述你期望发生什么...

## 实际行为
描述实际发生了什么...

## 环境信息
- OS: [e.g. Ubuntu 20.04]
- Python版本: [e.g. 3.11]
- PyTorch版本: [e.g. 2.0.0]

## 日志
```
粘贴相关日志...
```

## 截图
如果适用，添加截图...
```

## 💡 功能建议

### 功能建议模板

```markdown
## 功能描述
清晰简洁地描述你想要的功能...

## 动机
为什么需要这个功能？它解决什么问题？

## 建议方案
描述你建议的实现方案...

## 替代方案
描述你考虑过的其他方案...

## 额外信息
其他相关信息...
```

## 🎯 贡献领域

我们欢迎以下方面的贡献：

### 核心功能
- 新的模型架构（LSTM、Transformer等）
- 新的特征工程方法
- 新的标签生成策略
- 性能优化

### 工具和基础设施
- CI/CD改进
- 测试覆盖率提升
- 文档改进
- 部署脚本优化

### 文档
- 教程和示例
- API文档
- 最佳实践
- 翻译

### Bug修复
- 修复已知问题
- 提高代码质量
- 改进错误处理

## 📞 联系方式

- GitHub Issues: https://github.com/ningersweet/btcquant/issues
- Email: your_email@example.com

## 📄 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

---

**感谢你的贡献！** 🎉
