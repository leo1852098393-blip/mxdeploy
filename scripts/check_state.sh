#!/bin/bash
echo "=== 所有 python/vllm 进程 ==="
ps aux | grep -E "vllm|api_server" | grep -v grep
echo "=== 端口 8000 ==="
ss -tlnp 2>/dev/null | grep 8000
echo "=== deploy_test2.log 全文 ==="
cat /tmp/deploy_test2.log 2>/dev/null | tail -40
echo "=== vllm 日志最后 15 行 ==="
tail -15 /tmp/mxdeploy_vllm.log 2>/dev/null
