#!/bin/bash
# 64G 卡 14B-INT4 enforce-eager 模式（绕过 GPTQ shard 检查 bug）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

# 模型已被上次清理，重新下载
if [ ! -d /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 ]; then
  echo "=== 重新下载 14B-INT4 ==="
  huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 > /tmp/dl_14b64v2.log 2>&1
  echo "下载 rc=$?"
fi

echo "===== 部署 14B-INT4（enforce-eager 绕过 GPTQ 检查）====="
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 --enforce-eager > /root/bench64/deploy_14b64v3.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM" /root/bench64/deploy_14b64v3.log | head -3

echo "===== 压测 14B-INT4 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_14b64_eager.md > /root/bench64/bench_14b64_eager_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_14b64_eager.md 2>/dev/null | head -14

echo "===== DONE ====="
date
