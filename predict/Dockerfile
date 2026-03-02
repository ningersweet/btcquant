FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./predict

RUN mkdir -p /app/models /app/logs

EXPOSE 8003

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models

CMD ["python", "-m", "uvicorn", "predict.api:app", "--host", "0.0.0.0", "--port", "8003"]
