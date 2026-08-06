#!/bin/bash
echo "=== 进程检查 ==="
ps aux | grep -E "vllm|mxdeploy" | grep -v grep | head -5
echo "=== 日志行数 ==="
wc -l /tmp/mxdeploy_vllm.log 2>/dev/null
echo "=== 日志全文 ==="
cat /tmp/mxdeploy_vllm.log 2>/dev/null
echo "=== 端口检查 ==="
ss -tlnp 2>/dev/null | grep -E "8000|32222" | head -5
echo "=== HF 连接测试 ==="
timeout 10 curl -sI https://huggingface.co 2>&1 | head -3
echo "=== HF_ENDPOINT ==="
env | grep -iE "hf_|hugging" 
echo "=== 磁盘 ==="
df -h /root | tail -1
