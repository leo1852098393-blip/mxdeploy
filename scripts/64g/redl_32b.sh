#!/bin/bash
# 清理 32B 不完整下载 + 干净重下
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 停止旧下载进程 ==="
pkill -f "huggingface-cli download" 2>/dev/null; sleep 3
pkill -f "run_64g_14b_32b" 2>/dev/null; sleep 2

echo "=== 删除不完整 32B ==="
rm -rf /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4
df -h / | tail -1

echo "=== 干净重下 32B-INT4（~18G）==="
nohup huggingface-cli download Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4 > /tmp/dl_32b64.log 2>&1 &
echo "PID: $!"
sleep 5
tail -2 /tmp/dl_32b64.log 2>/dev/null || true
