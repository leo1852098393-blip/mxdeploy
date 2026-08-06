#!/bin/bash
# 清理并重新部署（修复 _health_interval bug 后）
pkill -f "vllm.entrypoints" 2>/dev/null
pkill -f "mxdeploy deploy" 2>/dev/null
sleep 2
export MACA_PATH=/opt/maca
export HF_ENDPOINT=https://hf-mirror.com
cd /root/mxdeploy
nohup /opt/conda/bin/mxdeploy deploy Qwen/Qwen2.5-3B-Instruct --port 8000 --timeout 900 > /tmp/deploy_test3.log 2>&1 &
echo "DEPLOY PID: $!"
sleep 8
echo "=== mxdeploy 输出 ==="
cat /tmp/deploy_test3.log
