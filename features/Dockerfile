FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY features/requirements.txt ./features/
RUN pip install --no-cache-dir -r features/requirements.txt
RUN pip install pyyaml

# 复制 common 模块
COPY common/ ./common/

# 复制 features 模块
COPY features/ ./features/

# 复制配置文件
COPY config.yaml .

EXPOSE 8002

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config.yaml

CMD ["python", "-m", "uvicorn", "features.api:app", "--host", "0.0.0.0", "--port", "8002"]
