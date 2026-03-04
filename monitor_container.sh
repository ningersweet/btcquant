#!/bin/bash
# 监控数据服务容器状态

echo "=========================================="
echo "数据服务容器监控"
echo "=========================================="
echo ""

CONTAINER_NAME="btc_quant_data_service"

# 检查容器是否存在
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✗ 容器不存在: $CONTAINER_NAME"
    exit 1
fi

# 显示容器状态
echo "容器状态:"
docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 显示资源使用情况
echo "资源使用:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" $CONTAINER_NAME
echo ""

# 显示最近的日志
echo "最近日志 (最后20行):"
echo "----------------------------------------"
docker logs --tail 20 $CONTAINER_NAME
echo "----------------------------------------"
echo ""

# 检查容器重启次数
RESTART_COUNT=$(docker inspect --format='{{.RestartCount}}' $CONTAINER_NAME 2>/dev/null || echo "0")
echo "容器重启次数: $RESTART_COUNT"

if [ "$RESTART_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  容器已重启 $RESTART_COUNT 次，可能存在问题"
    echo ""
    echo "查看完整日志:"
    echo "  docker logs $CONTAINER_NAME"
    echo ""
    echo "实时监控日志:"
    echo "  docker logs -f $CONTAINER_NAME"
fi

echo ""
echo "持续监控 (按 Ctrl+C 退出):"
echo "  watch -n 2 docker stats --no-stream $CONTAINER_NAME"
