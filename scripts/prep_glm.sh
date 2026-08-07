#!/bin/bash
# 下载 GLM-4-9B-GPTQ-Int4
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

nohup huggingface-cli download model-scope/glm-4-9b-chat-GPTQ-Int4 --local-dir /root/models/glm-4-9b-chat-GPTQ-Int4 > /tmp/dl_glm.log 2>&1 &
echo "GLM-INT4 下载 PID: $!"
sleep 5
tail -2 /tmp/dl_glm.log 2>/dev/null || true
echo "=== 磁盘 ==="
df -h / | tail -1
