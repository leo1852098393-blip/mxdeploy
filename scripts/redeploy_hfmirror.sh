#!/bin/bash
# 清理残留 vllm 进程，用 HF 镜像重新部署
pkill -f "vllm.entrypoints" 2>/dev/null
pkill -f "mxdeploy deploy" 2>/dev/null
sleep 2
echo "=== 清理完成 ==="
ps aux | grep -E "vllm|mxdeploy" | grep -v grep | head -3
echo "=== 开始部署（HF 镜像） ==="
export MACA_PATH=/opt/maca
export HF_ENDPOINT=https://hf-mirror.com
cd /root/mxdeploy
nohup /opt/conda/bin/mxdeploy deploy Qwen/Qwen2.5-3B-Instruct --port 8000 --timeout 900 > /tmp/deploy_test2.log 2>&1 &
echo "DEPLOY PID: $!"
sleep 5
echo "=== 初始日志 ==="
head -20 /tmp/deploy_test2.log
