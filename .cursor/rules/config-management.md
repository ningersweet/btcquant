# 配置文件管理规则

## 📋 核心原则

**config.yaml 以本地环境为准，统一管理，单向同步到服务器。**

## 🎯 管理流程

### 1. 配置文件位置

```
本地开发环境（主配置）
    ↓ scp 同步
CPU服务器（副本）
    ↓ scp 同步
GPU服务器（副本）
```

### 2. 修改流程

```bash
# ✅ 正确流程
# 1. 在本地修改配置
vim config.yaml

# 2. 同步到GPU服务器（训练用）
btcquant train sync-config

# 3. 同步到CPU服务器（如需要）
scp config.yaml cpu_server:/root/workspace/btcquant/

# ❌ 错误做法
# 不要直接在服务器上修改 config.yaml
ssh gpu_server
vim ~/workspace/btcquant/config.yaml  # 禁止！
```

## 📝 详细规则

### 规则1：本地为主

- **本地环境**是 `config.yaml` 的唯一权威来源
- 所有配置修改必须在本地完成
- 本地配置文件应该被妥善备份

### 规则2：单向同步

- 配置文件只能从**本地 → 服务器**单向同步
- 禁止从服务器同步配置到本地
- 禁止直接在服务器上修改配置

### 规则3：同步命令

使用统一的同步命令：

```bash
# 同步到GPU服务器（推荐）
btcquant train sync-config

# 手动同步到CPU服务器
scp config.yaml cpu_server:/root/workspace/btcquant/

# 手动同步到GPU服务器
scp config.yaml gpu_server:~/workspace/btcquant/
```

### 规则4：修改后必须同步

配置修改后，必须同步到相关服务器：

```bash
# 修改配置
vim config.yaml

# 如果要在GPU训练，必须同步
btcquant train sync-config

# 如果要在CPU推理，必须同步
scp config.yaml cpu_server:/root/workspace/btcquant/
```

### 规则5：版本控制

- `config.yaml` 不提交到 Git（已在 .gitignore）
- `config.yaml.example` 提交到 Git 作为模板
- 重要配置变更应记录在文档中

## 🔄 常见场景

### 场景1：修改训练参数

```bash
# 1. 本地修改
vim config.yaml
# 修改 predict.training.batch_size 等参数

# 2. 同步到GPU服务器
btcquant train sync-config

# 3. 启动训练
btcquant train start --gpu
```

### 场景2：修改邮件配置

```bash
# 1. 本地修改
vim config.yaml
# 修改 notification.email 部分

# 2. 测试配置
python predict/scripts/test_email.py

# 3. 同步到GPU服务器
btcquant train sync-config
```

### 场景3：修改标签生成参数

```bash
# 1. 本地修改
vim config.yaml
# 修改 predict.label.alpha 等参数

# 2. 同步到CPU服务器（数据准备）
scp config.yaml cpu_server:/root/workspace/btcquant/

# 3. 重新准备数据
btcquant data prepare

# 4. 同步到GPU服务器
btcquant train sync-config
btcquant train sync-data
```

### 场景4：新增配置项

```bash
# 1. 本地修改 config.yaml.example（提交到Git）
vim config.yaml.example
# 添加新配置项和说明

# 2. 本地修改 config.yaml
vim config.yaml
# 添加实际配置值

# 3. 更新 config.py（如需要）
vim predict/config.py
# 添加配置属性

# 4. 提交代码
git add config.yaml.example predict/config.py
git commit -m "feat: 添加新配置项"
git push

# 5. 同步配置到服务器
btcquant train sync-config
```

## ⚠️ 注意事项

### 1. 配置文件安全

```bash
# ✅ 正确：config.yaml 在 .gitignore 中
cat .gitignore | grep config.yaml

# ✅ 正确：提交前检查
git status  # 确保 config.yaml 不在待提交列表

# ❌ 错误：不要提交 config.yaml
git add config.yaml  # 禁止！
```

### 2. 配置备份

```bash
# 定期备份本地配置
cp config.yaml config.yaml.backup.$(date +%Y%m%d)

# 或加密备份
tar -czf - config.yaml | openssl enc -aes-256-cbc -out config_backup_$(date +%Y%m%d).tar.gz.enc
```

### 3. 服务器配置检查

```bash
# 检查GPU服务器配置是否最新
ssh gpu_server "cd ~/workspace/btcquant && ls -lh config.yaml"

# 对比本地和服务器配置
diff config.yaml <(ssh gpu_server "cat ~/workspace/btcquant/config.yaml")
```

### 4. 配置冲突处理

如果服务器上的配置被意外修改：

```bash
# 1. 强制覆盖服务器配置
scp config.yaml gpu_server:~/workspace/btcquant/config.yaml

# 2. 或者先备份服务器配置，再覆盖
ssh gpu_server "cd ~/workspace/btcquant && cp config.yaml config.yaml.old"
scp config.yaml gpu_server:~/workspace/btcquant/config.yaml
```

## 📋 检查清单

### 修改配置前

- [ ] 确认在本地环境
- [ ] 备份当前配置
- [ ] 了解修改的影响范围

### 修改配置后

- [ ] 本地测试配置（如 test_email.py）
- [ ] 同步到相关服务器
- [ ] 验证服务器配置已更新
- [ ] 重启相关服务（如需要）

### 提交代码前

- [ ] config.yaml 未被添加到 Git
- [ ] config.yaml.example 已更新（如有新配置）
- [ ] 文档已更新（如有重要变更）

## 🎓 最佳实践

1. **集中管理**：所有配置修改在本地完成
2. **及时同步**：修改后立即同步到服务器
3. **定期备份**：重要配置定期备份
4. **文档记录**：重要配置变更记录在文档
5. **测试验证**：修改后测试配置是否生效

## 🚫 禁止操作

1. ❌ 直接在服务器上修改 config.yaml
2. ❌ 从服务器复制 config.yaml 到本地
3. ❌ 提交 config.yaml 到 Git
4. ❌ 在多个地方维护不同版本的配置
5. ❌ 不同步就启动训练或服务

---

**记住：本地是配置的唯一真实来源，服务器只是副本！** 🎯
