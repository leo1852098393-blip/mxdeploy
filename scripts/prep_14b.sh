#!/bin/bash
# 查磁盘真实占用 + 启动 Qwen2.5-14B-GPTQ-Int4 下载
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 各挂载点磁盘 ==="
df -h | grep -vE "tmpfs|devpts|proc|sysfs|cgroup|mqueue|shm" | head -10

echo "=== /root/models 占用 ==="
du -sh /root/models 2>/dev/null || echo "目录不存在或已空"
ls /root/models 2>/dev/null

echo "=== 启动 14B-INT4 下载 ==="
mkdir -p /root/models
nohup huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 > /tmp/dl_14b.log 2>&1 &
echo "PID: $!"
sleep 5
tail -3 /tmp/dl_14b.log 2>/dev/null || true
