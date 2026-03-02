FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 8001

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/btc_quant.db

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
