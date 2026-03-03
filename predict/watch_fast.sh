#!/bin/bash
# 快速训练实时监控

LOG_FILE="/Users/lemonshwang/project/btc_quant/predict/training_fast.log"

while true; do
    clear
    echo "=========================================="
    echo "TCN快速训练实时监控"
    echo "=========================================="
    echo ""
    
    # 检查进程
    if ps aux | grep -v grep | grep "python train_fast.py" > /dev/null; then
        echo "✓ 训练进程正在运行"
        echo ""
    else
        echo "✗ 训练已完成或停止"
        echo ""
        break
    fi
    
    # 显示最新进度
    echo "最新进度:"
    echo "------------------------------------------"
    tail -20 "$LOG_FILE" | grep -E "Epoch|Loss|Best model|Backtest"
    echo "------------------------------------------"
    
    echo ""
    echo "按Ctrl+C退出监控"
    sleep 5
done

echo ""
echo "训练完成！查看完整日志:"
echo "  cat $LOG_FILE"
