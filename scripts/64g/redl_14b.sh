#!/bin/bash
# 放弃 32B，改测 14B-INT4 compile 模式（64G 卡）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 停止 32B 下载并清理 ==="
pkill -f "huggingface-cli download" 2>/dev/null; sleep 3
rm -rf /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4
df -h / | tail -1

echo "=== 下载 14B-INT4（9G）==="
nohup huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 > /tmp/dl_14b64.log 2>&1 &
echo "PID: $!"
sleep 3
tail -1 /tmp/dl_14b64.log 2>/dev/null || true

echo "=== 等下载完成（最多 15 分钟）==="
for i in $(seq 1 45); do
  n=$(ls /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4/*.safetensors 2>/dev/null | wc -l)
  if [ "$n" -ge 3 ]; then echo "14B 下载完成 (safetensors: $n)"; break; fi
  sleep 20
done
tail -2 /tmp/dl_14b64.log 2>/dev/null
df -h / | tail -1
