# 文档整理方案

## 🎯 整理目标
- 消除重复内容
- 建立清晰的文档层次
- 保持简洁准确

## 📋 文档分类

### 一级文档（项目根目录）- 保留4个

1. **README.md** ✅ 保留
   - 项目总览
   - 快速开始
   - 核心特性
   - 技术栈

2. **COMMANDS.md** ✅ 保留
   - 所有btcquant命令详解
   - 使用场景
   - 常见问题

3. **PROJECT.md** 🔄 合并 (PROJECT_RULES.md + PROJECT_STANDARDS.md)
   - 项目规范
   - 开发流程
   - 配置管理
   - 代码规范

4. **CONTRIBUTING.md** 🆕 新建
   - 贡献指南
   - 提交规范
   - 代码审查

### 二级文档（docs/）- 保留5个

1. **docs/INDEX.md** ✅ 保留
   - 文档导航

2. **docs/系统设计.md** ✅ 保留
   - 系统架构
   - 模块设计

3. **docs/部署指南.md** ✅ 保留
   - 详细部署步骤
   - 服务器配置
   - 故障排查

4. **docs/特征工程详细文档.md** ✅ 保留
   - 特征设计
   - 特征计算

5. **docs/模型训练与评估详细文档.md** ✅ 保留
   - 训练流程
   - 评估指标

6. **docs/超参数优化指南.md** ✅ 保留
   - 超参数调优
   - 优化方法

### 三级文档（模块README）- 保留5个

1. **predict/README.md** ✅ 保留（简化）
   - 模块介绍
   - 目录结构
   - 快速使用

2. **data/README.md** ✅ 保留
3. **strategy/README.md** ✅ 保留
4. **features/README.md** ✅ 保留
5. **evaluation/README.md** ✅ 保留

### 四级文档（子目录）- 保留3个

1. **predict/training/README.md** ✅ 保留
2. **predict/api/README.md** ✅ 保留
3. **predict/scripts/README.md** ✅ 保留

## 🗑️ 删除文件列表

### 根目录
- ❌ **QUICKSTART.md** - 内容过时，已被README.md和COMMANDS.md覆盖
- ❌ **PROJECT_RULES.md** - 合并到PROJECT.md
- ❌ **PROJECT_STANDARDS.md** - 合并到PROJECT.md
- ❌ **项目设计.md** - 与docs/系统设计.md重复

### predict/docs/
- ❌ **predict/docs/QUICKSTART.md** - 与根目录README重复
- ❌ **predict/docs/README.md** - 内容已整合到predict/README.md
- ❌ **predict/docs/模型设计.md** - 合并到docs/模型训练与评估详细文档.md
- ❌ **predict/docs/特征工程.md** - 与docs/特征工程详细文档.md重复
- ❌ **predict/docs/TRAINING_AUTOMATION.md** - 内容已整合到COMMANDS.md
- ❌ **predict/docs/TRAINING_REPORT.md** - 训练报告，可以移到storage/reports/

### storage/
- ❌ **storage/README.md** - 简单的目录说明，不需要单独文档

## 🔄 合并操作

### 1. 合并 PROJECT_RULES.md + PROJECT_STANDARDS.md → PROJECT.md

**保留内容：**
- 目录结构规范
- 代码规范
- 配置管理规范
- Git提交规范
- 工作流程
- 安全规范

**删除重复：**
- 重复的配置说明
- 重复的目录结构

### 2. 简化 predict/README.md

**保留：**
- 模块介绍
- 目录结构
- 核心功能API

**删除：**
- 详细的快速开始（链接到根目录README）
- 详细的配置说明（链接到PROJECT.md）

### 3. 更新 README.md

**添加：**
- 文档导航链接
- 清晰的快速开始步骤

**删除：**
- 过于详细的配置说明（移到PROJECT.md）

## 📁 最终文档结构

```
btc_quant/
├── README.md                          # 项目总览和快速开始
├── COMMANDS.md                        # 命令使用指南
├── PROJECT.md                         # 项目规范（合并）
├── CONTRIBUTING.md                    # 贡献指南（新建）
│
├── docs/                              # 详细文档
│   ├── INDEX.md                      # 文档导航
│   ├── 系统设计.md                    # 系统架构
│   ├── 部署指南.md                    # 部署详解
│   ├── 特征工程详细文档.md            # 特征详解
│   ├── 模型训练与评估详细文档.md      # 训练详解
│   └── 超参数优化指南.md              # 优化指南
│
├── predict/
│   ├── README.md                     # 模块介绍（简化）
│   ├── training/README.md            # 训练脚本说明
│   ├── api/README.md                 # API说明
│   └── scripts/README.md             # 脚本说明
│
├── data/README.md                    # 数据模块
├── strategy/README.md                # 策略模块
├── features/README.md                # 特征模块
└── evaluation/README.md              # 评估模块
```

## 📊 统计

- **删除文件**: 11个
- **合并文件**: 2个 → 1个
- **新建文件**: 1个
- **保留文件**: 17个
- **总计**: 从27个减少到18个（减少33%）

## ✅ 执行步骤

1. 创建 PROJECT.md（合并 PROJECT_RULES.md + PROJECT_STANDARDS.md）
2. 创建 CONTRIBUTING.md
3. 更新 README.md（添加文档导航）
4. 简化 predict/README.md
5. 删除重复文件
6. 更新 docs/INDEX.md
7. 提交更改

## 🎯 预期效果

- ✅ 文档层次清晰
- ✅ 无重复内容
- ✅ 易于查找
- ✅ 易于维护
- ✅ 新手友好
