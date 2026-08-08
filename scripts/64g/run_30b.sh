#!/bin/bash
# 30B MoE 部署（+trust-remote-code）+ 压测
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 部署 Qwen3-30B-A3B-Thinking（+trust-remote-code）====="
pkill -f vllm.entrypoints; sleep 5
mxdeploy deploy /mnt/moark-models/Qwen3-30B-A3B-Thinking-2507 --port 8000 --timeout 1800 --gpu-memory-utilization 0.8 --trust-remote-code > /root/bench64/deploy_30bmoe_v2.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|启动命令" /root/bench64/deploy_30bmoe_v2.log | head -4

echo "===== 压测 30B MoE ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_30bmoe.md > /root/bench64/bench_30bmoe_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_30bmoe.md 2>/dev/null | head -14

echo "===== DONE ====="
date
