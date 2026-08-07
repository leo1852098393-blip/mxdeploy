#!/bin/bash
# DeepSeek-R1-Distill-Qwen-1.5B 部署 + 压测（util=0.8）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 停止 7B 服务 ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== 检查 DeepSeek 下载 ====="
ls /root/models/DeepSeek-R1-Distill-Qwen-1.5B/ 2>/dev/null | head -5
tail -2 /tmp/dl_ds15b.log 2>/dev/null

echo "===== deploy DeepSeek-R1-Distill-Qwen-1.5B ====="
mxdeploy deploy /root/models/DeepSeek-R1-Distill-Qwen-1.5B --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench_results/deploy_ds.log 2>&1
echo "rc=$?"

sleep 2
curl -s http://127.0.0.1:8000/health || echo "health check 失败"

echo "===== bench DeepSeek ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_ds.md > /root/bench_results/bench_ds_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
date
