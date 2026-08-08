#!/bin/bash
# 64G 卡：预置模型测试（Qwen3-30B-A3B MoE + Qwen3.5-27B-W8A8）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== [1/4] 部署 Qwen3-30B-A3B-Thinking（30B MoE，compile）====="
pkill -f vllm.entrypoints; sleep 5
mxdeploy deploy /mnt/moark-models/Qwen3-30B-A3B-Thinking-2507 --port 8000 --timeout 1800 --gpu-memory-utilization 0.8 > /root/bench64/deploy_30bmoe.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM|降|启动命令" /root/bench64/deploy_30bmoe.log | head -5

echo "===== [2/4] 压测 30B MoE ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_30bmoe.md > /root/bench64/bench_30bmoe_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_30bmoe.md 2>/dev/null | head -14

echo "===== [3/4] 部署 Qwen3.5-27B-W8A8（27B INT8）====="
pkill -f vllm.entrypoints; sleep 5
mxdeploy deploy /mnt/moark-models/Qwen3.5-27B-W8A8 --port 8000 --timeout 1800 --gpu-memory-utilization 0.8 > /root/bench64/deploy_27b.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM|降|启动命令" /root/bench64/deploy_27b.log | head -5

echo "===== [4/4] 压测 27B-W8A8 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_27b.md > /root/bench64/bench_27b_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_27b.md 2>/dev/null | head -14

echo "===== ALL DONE ====="
date
