#!/bin/bash
# 64G 流水线②：14B-INT4 compile 模式 → 32B-INT4
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== [1/5] 后台下载 32B-INT4（并行）====="
nohup huggingface-cli download Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4 --local-dir /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4 > /tmp/dl_32b64.log 2>&1 &
echo "32B 下载 PID: $!"
sleep 3
tail -1 /tmp/dl_32b64.log 2>/dev/null || true

echo "===== [2/5] 部署 14B-INT4（64G compile 模式，不传 enforce-eager）====="
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --timeout 1200 --gpu-memory-utilization 0.8 > /root/bench64/deploy_14b64.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM|降" /root/bench64/deploy_14b64.log | head -4

echo "===== [3/5] 压测 14B-INT4 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_14b64.md > /root/bench64/bench_14b64_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_14b64.md 2>/dev/null | head -15

echo "===== [4/5] 停止并清理 14B ====="
pkill -f vllm.entrypoints; sleep 6
rm -rf /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4
df -h / | tail -1

echo "===== 等 32B 下载完成 ====="
for i in $(seq 1 60); do
  n=$(ls /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4/*.safetensors 2>/dev/null | wc -l)
  if [ "$n" -ge 4 ]; then echo "32B 下载完成 (safetensors: $n)"; break; fi
  sleep 20
done
tail -2 /tmp/dl_32b64.log 2>/dev/null

echo "===== [5/5] 部署 32B-INT4（compile 模式，OOM 自动降级验证）====="
mxdeploy deploy /root/models/Qwen2.5-32B-Instruct-GPTQ-Int4 --port 8000 --timeout 1800 --gpu-memory-utilization 0.8 > /root/bench64/deploy_32b.log 2>&1
echo "rc=$?"
grep -E "就绪|失败|OOM|降|enforce" /root/bench64/deploy_32b.log | head -5

echo "===== 压测 32B-INT4 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench64/bench_32b.md > /root/bench64/bench_32b_run.log 2>&1
echo "rc=$?"
cat /root/bench64/bench_32b.md 2>/dev/null | head -15

echo "===== ALL DONE ====="
date
