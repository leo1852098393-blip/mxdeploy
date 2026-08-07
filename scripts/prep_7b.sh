#!/bin/bash
# 并行下载 7B-INT8（量化路径验证）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

nohup huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GPTQ-Int8 --local-dir /root/models/Qwen2.5-7B-Instruct-GPTQ-Int8 > /tmp/dl_7bint8.log 2>&1 &
echo "7B-INT8 下载 PID: $!"
sleep 3
tail -2 /tmp/dl_7bint8.log 2>/dev/null || true
echo "=== 磁盘 ==="
df -h / | tail -1
