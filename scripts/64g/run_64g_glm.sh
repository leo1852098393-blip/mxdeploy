#!/bin/bash
# 64G 卡：GLM-4-9B-chat FP16 测试（清理 14B 后）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "=== 停止 14B 服务 + 清理模型 ==="
pkill -f vllm.entrypoints; sleep 5
rm -rf /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4
df -h / | tail -1

echo "=== 下载 GLM-4-9B-chat FP16（zai-org 官方，~18G）==="
nohup huggingface-cli download zai-org/glm-4-9b-chat --local-dir /root/models/glm-4-9b-chat > /tmp/dl_glm64.log 2>&1 &
echo "PID: $!"
for i in $(seq 1 60); do
  n=$(ls /root/models/glm-4-9b-chat/*.safetensors 2>/dev/null | wc -l)
  if [ "$n" -ge 10 ]; then echo "GLM 下载完成 (safetensors: $n)"; break; fi
  sleep 20
done
tail -2 /tmp/dl_glm64.log 2>/dev/null
df -h / | tail -1

echo "=== 部署 GLM-4-9B FP16（compile + trust-remote-code）==="
mxdeploy deploy /root/models/glm-4-9b-chat --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 --trust-remote-code > /root/bench64/deploy_glm64.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM" /root/bench64/deploy_glm64.log | head -3

echo "=== 压测 GLM-4-9B FP16 ==="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_glm64.md > /root/bench64/bench_glm64_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_glm64.md 2>/dev/null | head -14

echo "===== DONE ====="
date
