#!/bin/bash
# 下载 DeepSeek-R1-Distill-Qwen-1.5B（后台）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

nohup huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --local-dir /root/models/DeepSeek-R1-Distill-Qwen-1.5B > /tmp/dl_ds15b.log 2>&1 &
echo "DeepSeek-1.5B 下载 PID: $!"
sleep 3
tail -2 /tmp/dl_ds15b.log 2>/dev/null || true
df -h / | tail -1
