#!/bin/bash
echo "=== 部署状态检查 ==="
cat /tmp/deploy_test3.log 2>/dev/null
echo ""
echo "=== 端口 ==="
ss -tlnp 2>/dev/null | grep 8000
echo "=== 进程 ==="
ps aux | grep "api_server" | grep -v grep | awk '{print $2, $3"%", $11, $12, $13}'
echo "=== 日志尾部 ==="
tail -8 /tmp/mxdeploy_vllm.log 2>/dev/null
echo "=== 健康检查 ==="
timeout 5 curl -s http://127.0.0.1:8000/health 2>&1 || echo "(未就绪)"
