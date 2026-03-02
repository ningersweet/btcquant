FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY predict/requirements.txt ./predict/
RUN pip install --no-cache-dir -r predict/requirements.txt
RUN pip install pyyaml

# 复制 common 模块
COPY common/ ./common/

# 复制 predict 模块
COPY predict/ ./predict/

# 复制配置文件
COPY config.yaml .

RUN mkdir -p /app/models /app/logs

EXPOSE 8003

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config.yaml
ENV MODEL_PATH=/app/models

CMD ["python", "-m", "uvicorn", "predict.api:app", "--host", "0.0.0.0", "--port", "8003"]
