#!/bin/bash
# 检查工具 + 预下载模型（后台并行）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 工具检查 ==="
which mxdeploy && mxdeploy version || echo "mxdeploy 未安装"
which huggingface-cli || echo "huggingface-cli 未安装"
which hf || echo "hf 未安装"

echo "=== 磁盘 ==="
df -h / | tail -1

echo "=== 启动后台下载 Qwen2.5-1.5B-Instruct ==="
mkdir -p /root/models
nohup huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir /root/models/Qwen2.5-1.5B-Instruct > /tmp/dl_15b.log 2>&1 &
echo "下载 PID: $!"
sleep 2
tail -3 /tmp/dl_15b.log 2>/dev/null || true
