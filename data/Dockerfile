FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 8001

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DB_PATH=/app/data/btc_quant.db

CMD ["python", "-m", "uvicorn", "data.api:app", "--host", "0.0.0.0", "--port", "8001"]
