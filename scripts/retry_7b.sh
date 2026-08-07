#!/bin/bash
# 7B-INT8 部署 + 压测（util=0.8）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 停止 1.5B 服务 ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== deploy 7B-INT8 (util=0.8) ====="
mxdeploy deploy /root/models/Qwen2.5-7B-Instruct-GPTQ-Int8 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_7b_v2.log 2>&1
echo "rc=$?"

sleep 2
curl -s http://127.0.0.1:8000/health || echo "health check 失败"

echo "===== bench 7B-INT8 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_7b_v2.md > /root/bench_results/bench_7b_v2_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
date
