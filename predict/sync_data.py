"""
数据预同步脚本

在训练前预先同步历史数据到数据库
"""

import requests
import time
import sys

def sync_historical_data(start_date="2019-01-01", end_date=None):
    """
    同步历史数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期（None则到当前）
    """
    url = "http://localhost:8001/api/v1/sync"
    
    data = {
        "symbol": "BTCUSDT",
        "start_date": start_date
    }
    
    if end_date:
        data["end_date"] = end_date
    
    print(f"开始同步数据: {start_date} 到 {end_date or '现在'}")
    print("这可能需要几分钟时间，请耐心等待...")
    print("-" * 60)
    
    try:
        # 发送同步请求（可能需要较长时间）
        response = requests.post(
            url,
            json=data,
            timeout=600  # 10分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                sync_data = result['data']
                print(f"✓ 同步成功!")
                print(f"  同步数量: {sync_data['synced_count']} 条")
                print(f"  开始时间: {sync_data['start_time']}")
                print(f"  结束时间: {sync_data['end_time']}")
                return True
            else:
                print(f"✗ 同步失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        print("提示: 数据量太大，建议分批同步或增加超时时间")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def check_data_status():
    """检查数据状态"""
    url = "http://localhost:8001/api/v1/status"
    params = {
        "symbol": "BTCUSDT",
        "interval": "5m"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 0:
                status = result['data']
                print("\n当前数据状态:")
                print("-" * 60)
                print(f"  交易对: {status['symbol']}")
                print(f"  周期: {status['interval']}")
                print(f"  数据量: {status['count']} 条")
                print(f"  完整度: {status['completeness']*100:.2f}%")
                if status['start_time']:
                    from datetime import datetime
                    start = datetime.fromtimestamp(status['start_time']/1000)
                    end = datetime.fromtimestamp(status['end_time']/1000)
                    print(f"  时间范围: {start} 到 {end}")
                return True
        return False
    except Exception as e:
        print(f"无法获取数据状态: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("BTC量化交易系统 - 数据预同步工具")
    print("="*60)
    
    # 检查当前数据状态
    print("\n[1/3] 检查当前数据状态...")
    check_data_status()
    
    # 同步数据
    print("\n[2/3] 开始同步历史数据...")
    
    # 可以根据需要调整日期范围
    # 建议先同步最近1年的数据
    start_date = "2024-01-01"  # 从2024年开始
    
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    
    success = sync_historical_data(start_date)
    
    # 再次检查数据状态
    if success:
        print("\n[3/3] 同步完成，检查最新状态...")
        time.sleep(2)
        check_data_status()
        
        print("\n" + "="*60)
        print("数据同步完成！现在可以运行训练脚本了:")
        print("  python train.py")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("数据同步失败，请检查:")
        print("1. 数据服务是否正常运行: docker-compose ps")
        print("2. 网络连接是否正常")
        print("3. Binance API是否可访问")
        print("="*60)
