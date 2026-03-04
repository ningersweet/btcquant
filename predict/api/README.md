# API服务目录

此目录包含预测服务的API接口。

## 文件说明

- `api.py` - FastAPI服务，提供模型推理接口

## 启动服务

```bash
cd api
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API端点

### 健康检查
```bash
GET /health
```

### 预测
```bash
POST /predict
Content-Type: application/json

{
  "klines": [...],  # K线数据
  "symbol": "BTCUSDT"
}
```

## Docker部署

```bash
docker-compose up -d predict-service
```

## 配置

API配置在根目录的 `config.yaml` 中：

```yaml
predict:
  host: "0.0.0.0"
  port: 8000
  model_path: "/app/models"
```
