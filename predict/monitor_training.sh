#!/bin/bash
# 训练监控脚本

LOG_FILE="/Users/lemonshwang/project/btc_quant/predict/training_full.log"

echo "=========================================="
echo "TCN模型训练监控"
echo "=========================================="
echo ""

# 检查进程
if ps aux | grep -v grep | grep "python train.py" > /dev/null; then
    echo "✓ 训练进程正在运行"
    PID=$(ps aux | grep -v grep | grep "python train.py" | awk '{print $2}')
    echo "  PID: $PID"
else
    echo "✗ 训练进程未运行"
fi

echo ""
echo "最新日志 (最后30行):"
echo "------------------------------------------"
tail -30 "$LOG_FILE"
echo "------------------------------------------"

echo ""
echo "训练统计:"
echo "------------------------------------------"
grep "Epoch" "$LOG_FILE" | tail -5
echo ""
grep "Best model saved" "$LOG_FILE" | tail -3
echo "------------------------------------------"

echo ""
echo "提示:"
echo "  实时查看日志: tail -f $LOG_FILE"
echo "  停止训练: pkill -f 'python train.py'"
echo "  查看完整日志: cat $LOG_FILE"
