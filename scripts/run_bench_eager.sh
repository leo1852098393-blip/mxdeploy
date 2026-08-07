#!/bin/bash
# 手动部署 14B + GLM（enforce-eager 跳过 torch.compile）→ mxdeploy bench
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

VLLM="/opt/conda/bin/python -m vllm.entrypoints.openai.api_server"

echo "===== [1/4] 启动 14B-INT4 (enforce-eager, util=0.8) ====="
nohup $VLLM --model /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 8192 \
  --quantization gptq --enforce-eager > /tmp/vllm_14b.log 2>&1 &
echo "PID: $!"

# 等待健康（最多 600s）
for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "14B 就绪 ($((i*10))s)"; break; fi
  sleep 10
done
curl -s http://127.0.0.1:8000/health || { echo "14B 启动失败"; tail -20 /tmp/vllm_14b.log; exit 1; }

echo "===== [2/4] bench 14B ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_14b.md > /root/bench_results/bench_14b_run.log 2>&1
echo "rc=$?"

echo "===== stop 14B ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== [3/4] 启动 GLM-INT4 (enforce-eager, util=0.8) ====="
nohup $VLLM --model /root/models/glm-4-9b-chat-GPTQ-Int4 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 8192 \
  --quantization gptq --enforce-eager > /tmp/vllm_glm.log 2>&1 &
echo "PID: $!"

for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "GLM 就绪 ($((i*10))s)"; break; fi
  sleep 10
done
curl -s http://127.0.0.1:8000/health || { echo "GLM 启动失败"; tail -20 /tmp/vllm_glm.log; exit 1; }

echo "===== [4/4] bench GLM ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_glm.md > /root/bench_results/bench_glm_run.log 2>&1
echo "rc=$?"

echo "===== ALL DONE ====="
date
