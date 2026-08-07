#!/bin/bash
# 重试：1.5B 部署（降 gpu-memory-utilization）+ bench
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== deploy 1.5B (util=0.8) ====="
mxdeploy deploy /root/models/Qwen2.5-1.5B-Instruct --port 8000 --timeout 900 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_15b_v2.log 2>&1
echo "rc=$?"

# 检查服务是否真的起来了
sleep 2
curl -s http://127.0.0.1:8000/health || echo "health check 失败"

echo "===== bench 1.5B ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_15b_v2.md > /root/bench_results/bench_15b_v2_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
