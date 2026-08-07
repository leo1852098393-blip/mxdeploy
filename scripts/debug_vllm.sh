#!/bin/bash
# 手动前台启动 vLLM 看完整错误
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
cd /root

echo "=== GPU 状态 ==="
mx-smi --show-usage 2>/dev/null | head -6

echo "=== 残留 vLLM 进程 ==="
ps aux | grep -c vllm || true

echo "=== 前台启动 vLLM (1.5B) 60 秒超时 ==="
timeout 60 python -m vllm.entrypoints.openai.api_server \
  --model /root/models/Qwen2.5-1.5B-Instruct \
  --port 8000 --gpu-memory-utilization 0.9 --max-model-len 8192 2>&1 | head -50
echo "=== rc=$? ==="
