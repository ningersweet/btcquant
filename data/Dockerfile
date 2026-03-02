FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY data/requirements.txt ./data/
RUN pip install --no-cache-dir -r data/requirements.txt
RUN pip install pyyaml

# 复制 common 模块
COPY common/ ./common/

# 复制 data 模块
COPY data/ ./data/

# 复制配置文件
COPY config.yaml .

RUN mkdir -p /app/data /app/logs

EXPOSE 8001

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config.yaml
ENV DB_PATH=/app/data/btc_quant.db

CMD ["python", "-m", "uvicorn", "data.api:app", "--host", "0.0.0.0", "--port", "8001"]
