#!/bin/bash
# 64G 实例：安装 mxdeploy + 下载第一批模型
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 安装 mxdeploy 0.2.0 ==="
pip install mxdeploy -i https://pypi.org/simple -q 2>&1 | tail -1
mxdeploy version 2>&1 | head -1

echo "=== 下载 Qwen2.5-7B-Instruct FP16（~15G）==="
mkdir -p /root/models
nohup huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir /root/models/Qwen2.5-7B-Instruct > /tmp/dl_7b_fp16.log 2>&1 &
echo "PID: $!"
sleep 5
tail -2 /tmp/dl_7b_fp16.log 2>/dev/null || true
df -h / | tail -1
