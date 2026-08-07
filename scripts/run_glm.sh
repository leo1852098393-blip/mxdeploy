#!/bin/bash
# GLM-INT4 部署压测（trust-remote-code）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

VLLM="/opt/conda/bin/python -m vllm.entrypoints.openai.api_server"

echo "===== 启动 GLM-INT4 (enforce-eager, trust-remote-code) ====="
nohup $VLLM --model /root/models/glm-4-9b-chat-GPTQ-Int4 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 8192 \
  --quantization gptq --enforce-eager --trust-remote-code > /tmp/vllm_glm.log 2>&1 &
echo "PID: $!"

for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "GLM 就绪 ($((i*10))s)"; break; fi
  sleep 10
done
curl -s http://127.0.0.1:8000/health || { echo "GLM 启动失败"; grep -E 'Error|error' /tmp/vllm_glm.log | tail -6; exit 1; }

echo "===== bench GLM ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_glm.md > /root/bench_results/bench_glm_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
date
