#!/bin/bash
# 27B 重试（trust-remote-code）+ 30B 手动调试
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== [1] 部署 27B-W8A8（+trust-remote-code）====="
pkill -f vllm.entrypoints; sleep 5
mxdeploy deploy /mnt/moark-models/Qwen3.5-27B-W8A8 --port 8000 --timeout 1800 --gpu-memory-utilization 0.8 --trust-remote-code > /root/bench64/deploy_27b_v2.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|启动命令" /root/bench64/deploy_27b_v2.log | head -4

if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "===== 压测 27B ====="
  mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_27b.md > /root/bench64/bench_27b_run.log 2>&1
  echo "rc=$?"
  cat /root/bench64/bench_27b.md 2>/dev/null | head -14
fi

echo "===== [2] 30B MoE 手动前台 90 秒看错误 ====="
pkill -f vllm.entrypoints; sleep 5
timeout 90 /opt/conda/bin/python -m vllm.entrypoints.openai.api_server \
  --model /mnt/moark-models/Qwen3-30B-A3B-Thinking-2507 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 8192 \
  --trust-remote-code 2>&1 | grep -iE 'error|fail|not support|architect|quant|ValueError|RuntimeError' | head -10
echo "=== 30B 前台结束 ==="
date
