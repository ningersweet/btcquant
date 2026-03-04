#!/bin/bash
# 在服务器上准备训练数据
# 运行环境：数据服务所在的服务器

set -e

echo "=========================================="
echo "准备训练数据"
echo "=========================================="

# 配置
DATA_START_DATE="2019-01-01"
DATA_END_DATE=""
CACHE_FILE="training_data_cache.pkl"
DATA_SERVICE_URL="http://localhost:8001"

echo ""
echo "配置信息："
echo "  数据起始日期: $DATA_START_DATE"
echo "  数据结束日期: ${DATA_END_DATE:-当前}"
echo "  缓存文件: $CACHE_FILE"
echo "  数据服务: $DATA_SERVICE_URL"
echo ""

# 1. 检查数据服务
echo "[1/4] 检查数据服务状态..."
if curl -s "$DATA_SERVICE_URL/health" > /dev/null; then
    echo "✓ 数据服务运行正常"
else
    echo "✗ 数据服务未运行，尝试启动..."
    docker-compose up -d data-service
    sleep 5
    if curl -s "$DATA_SERVICE_URL/health" > /dev/null; then
        echo "✓ 数据服务已启动"
    else
        echo "✗ 数据服务启动失败"
        exit 1
    fi
fi

# 2. 检查数据库状态
echo ""
echo "[2/4] 检查数据库状态..."
curl -s "$DATA_SERVICE_URL/api/v1/status?symbol=BTCUSDT&interval=5m" | python3 -m json.tool

# 3. 创建Python脚本来获取和缓存数据
echo ""
echo "[3/4] 创建数据获取脚本..."

cat > fetch_training_data.py << 'PYTHON_SCRIPT'
"""
从数据服务获取训练数据并缓存
"""

import requests
import pandas as pd
import pickle
import sys
import time
from datetime import datetime

def fetch_data(start_date, end_date=None, cache_file="training_data_cache.pkl"):
    """获取并缓存训练数据"""
    
    print(f"开始获取数据: {start_date} 到 {end_date or '现在'}")
    
    # 转换日期为时间戳
    start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
    if end_date:
        end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
    else:
        end_ts = int(pd.Timestamp.now().timestamp() * 1000)
    
    url = "http://localhost:8001/api/v1/klines"
    
    all_data = []
    batch_size = 2000  # 增加批次大小，减少请求次数
    current_start = start_ts
    batch_count = 0
    retry_count = 0
    max_retries = 3
    
    print("开始分批获取数据...")
    
    while current_start < end_ts:
        params = {
            'symbol': 'BTCUSDT',
            'interval': '5m',
            'start_time': current_start,
            'end_time': end_ts,
            'limit': batch_size
        }
        
        batch_count += 1
        if batch_count % 10 == 0:
            print(f"  已获取 {batch_count} 批，共 {len(all_data)} 条记录")
        
        try:
            # 减少超时时间，避免长时间占用内存
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            if result['code'] != 0:
                print(f"API错误: {result.get('message', 'Unknown error')}")
                break
            
            batch_data = result['data']
            if not batch_data:
                break
            
            all_data.extend(batch_data)
            
            last_timestamp = batch_data[-1]['timestamp']
            current_start = last_timestamp + 1
            
            # 重置重试计数
            retry_count = 0
            
            if len(batch_data) < batch_size:
                break
            
            # 添加短暂延迟，避免过快请求导致服务压力过大
            time.sleep(0.1)
                
        except requests.exceptions.Timeout:
            print(f"请求超时，重试 {retry_count + 1}/{max_retries}...")
            retry_count += 1
            if retry_count >= max_retries:
                print(f"✗ 超过最大重试次数，停止获取")
                break
            time.sleep(2)
            continue
            
        except Exception as e:
            print(f"获取数据出错: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                print(f"✗ 超过最大重试次数，停止获取")
                break
            time.sleep(2)
            continue
    
    if not all_data:
        print("✗ 未获取到任何数据")
        return False
    
    # 转换为DataFrame
    print(f"\n处理数据...")
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df = df[~df.index.duplicated(keep='first')].sort_index()
    
    print(f"✓ 共获取 {len(df)} 条K线数据")
    print(f"  时间范围: {df.index[0]} 到 {df.index[-1]}")
    
    # 保存缓存
    print(f"\n保存缓存到: {cache_file}")
    with open(cache_file, 'wb') as f:
        pickle.dump(df, f)
    
    # 显示文件大小
    import os
    file_size = os.path.getsize(cache_file) / (1024 * 1024)
    print(f"✓ 缓存文件大小: {file_size:.2f} MB")
    
    return True

if __name__ == "__main__":
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2019-01-01"
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    cache_file = sys.argv[3] if len(sys.argv) > 3 else "training_data_cache.pkl"
    
    success = fetch_data(start_date, end_date, cache_file)
    sys.exit(0 if success else 1)
PYTHON_SCRIPT

# 4. 运行数据获取脚本
echo ""
echo "[4/4] 获取训练数据..."
python3 fetch_training_data.py "$DATA_START_DATE" "$DATA_END_DATE" "$CACHE_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 训练数据准备完成！"
    echo "=========================================="
    echo ""
    echo "缓存文件: $(pwd)/$CACHE_FILE"
    echo "文件大小: $(du -h $CACHE_FILE | cut -f1)"
    echo ""
    echo "下一步："
    echo "1. 将缓存文件传输到GPU服务器："
    echo "   scp $CACHE_FILE root@GPU_SERVER:~/btc_quant/predict/data_cache.pkl"
    echo ""
    echo "2. 或者在GPU服务器上直接运行此脚本"
    echo ""
else
    echo ""
    echo "✗ 数据准备失败"
    exit 1
fi
