#!/bin/bash
# 64G 卡 14B-INT4 compile 模式部署 + 压测
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 部署 14B-INT4（compile 模式，不传 enforce-eager）====="
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench64/deploy_14b64v2.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM|降" /root/bench64/deploy_14b64v2.log | head -4

echo "===== 压测 14B-INT4 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_14b64.md > /root/bench64/bench_14b64_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_14b64.md 2>/dev/null | head -15

echo "===== 停止并清理 ====="
pkill -f vllm.entrypoints; sleep 5
rm -rf /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4
df -h / | tail -1
echo "===== DONE ====="
date
