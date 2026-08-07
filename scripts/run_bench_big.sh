#!/bin/bash
# 14B-INT4 部署+压测 → 等 GLM 下载 → GLM 部署+压测
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== [1/4] deploy Qwen2.5-14B-GPTQ-Int4 (util=0.8) ====="
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_14b.log 2>&1
echo "rc=$?"
sleep 2
curl -s http://127.0.0.1:8000/health || echo "health 失败"

echo "===== [2/4] bench 14B ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_14b.md > /root/bench_results/bench_14b_run.log 2>&1
echo "rc=$?"

echo "===== stop 14B ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== 等待 GLM 下载完成 ====="
for i in $(seq 1 30); do
  n=$(ls /root/models/glm-4-9b-chat-GPTQ-Int4/*.safetensors 2>/dev/null | wc -l)
  if [ "$n" -ge 2 ]; then echo "GLM 下载完成 (safetensors: $n)"; break; fi
  sleep 20
done
tail -2 /tmp/dl_glm.log

echo "===== [3/4] deploy GLM-4-9B-GPTQ-Int4 (util=0.8) ====="
mxdeploy deploy /root/models/glm-4-9b-chat-GPTQ-Int4 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_glm.log 2>&1
echo "rc=$?"
sleep 2
curl -s http://127.0.0.1:8000/health || echo "health 失败"

echo "===== [4/4] bench GLM ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_glm.md > /root/bench_results/bench_glm_run.log 2>&1
echo "rc=$?"

echo "===== ALL DONE ====="
date
