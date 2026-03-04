# 存储目录说明

此目录用于统一存放项目的运行时数据。

## 目录结构

```
storage/
├── logs/           # 所有日志文件
│   ├── training.log
│   ├── inference.log
│   ├── backtest.log
│   └── api.log
├── cache/          # 数据缓存文件
│   ├── data_cache.pkl
│   └── training_data_cache.pkl
└── models/         # 训练好的模型（可选，也可以放在predict/models/）
    └── tcn_*/
```

## 说明

- **logs/** - 所有服务的日志文件统一存放
- **cache/** - 数据缓存文件统一存放
- **models/** - 可选，模型文件也可以放在predict/models/

## .gitignore

这些目录下的文件不会被提交到Git：
- `storage/logs/*.log`
- `storage/cache/*.pkl`
- `storage/models/tcn_*/`
