#!/bin/bash
# v0.2 真机验证：init 显存 + 14B/GLM 一键部署
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root
mkdir -p /root/bench_results

echo "===== [1/5] init 显存检测（应显示 16G 而非 65536）====="
mxdeploy init 2>&1 | grep -E "显存|gpu|GPU" | head -3

echo "===== [2/5] 一键部署 14B（--enforce-eager 透传验证）====="
pkill -f vllm.entrypoints; sleep 5
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --gpu-memory-utilization 0.8 --max-model-len 4096 --enforce-eager > /root/bench_results/v02_deploy_14b.log 2>&1
echo "rc=$?"
grep -E "启动命令|enforce|就绪|失败" /root/bench_results/v02_deploy_14b.log | head -5

echo "===== [3/5] bench 14B（快速验证）====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 10 --concurrency 2 --max-tokens 64 --format table 2>&1 | tail -10

echo "===== [4/5] 切 GLM 一键部署（--trust-remote-code 透传验证）====="
pkill -f vllm.entrypoints; sleep 6
mxdeploy deploy /root/models/glm-4-9b-chat-GPTQ-Int4 --port 8000 --gpu-memory-utilization 0.8 --enforce-eager --trust-remote-code > /root/bench_results/v02_deploy_glm.log 2>&1
echo "rc=$?"
grep -E "启动命令|trust|就绪|失败" /root/bench_results/v02_deploy_glm.log | head -5

echo "===== [5/5] bench GLM（快速验证，含 fallback 场景）====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 10 --concurrency 2 --max-tokens 64 --format table 2>&1 | tail -10

echo "===== 验证完成 ====="
date
