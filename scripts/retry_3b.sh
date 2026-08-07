#!/bin/bash
# 重测 3B（50 请求，util=0.8，与矩阵统一）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 停止 DeepSeek 服务 ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== deploy 3B (util=0.8) ====="
mxdeploy deploy Qwen/Qwen2.5-3B-Instruct --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_3b_v2.log 2>&1
echo "rc=$?"

sleep 2
curl -s http://127.0.0.1:8000/health || echo "health check 失败"

echo "===== bench 3B (50 请求) ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_3b_v2.md > /root/bench_results/bench_3b_v2_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
date
