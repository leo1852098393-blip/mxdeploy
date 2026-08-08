#!/bin/bash
# 64G 实例流水线①：7B FP16 部署+压测 → 存档 → 并行下载 14B-INT4
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root
mkdir -p /root/bench64

echo "===== [1/4] 后台下载 14B-INT4（并行）====="
nohup huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 > /tmp/dl_14b64.log 2>&1 &
echo "14B 下载 PID: $!"

echo "===== [2/4] 部署 7B FP16（64G 卡 compile 模式）====="
mxdeploy deploy /root/models/Qwen2.5-7B-Instruct --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench64/deploy_7bfp16.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM" /root/bench64/deploy_7bfp16.log | head -3

echo "===== [3/4] 压测 7B FP16 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_7bfp16.md > /root/bench64/bench_7bfp16_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_7bfp16.md 2>/dev/null | head -15

echo "===== [4/4] 停止并清理 7B（释放磁盘给 14B）====="
pkill -f vllm.entrypoints; sleep 6
rm -rf /root/models/Qwen2.5-7B-Instruct
df -h / | tail -1

echo "===== DONE ====="
date
