#!/bin/bash
# mxdeploy 补测：Qwen2.5-1.5B + Qwen2.5-7B-GPTQ-Int8 全自动部署+压测
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
cd /root
mkdir -p /root/bench_results

echo "===== [1/4] deploy Qwen2.5-1.5B-Instruct ====="
mxdeploy deploy /root/models/Qwen2.5-1.5B-Instruct --port 8000 --timeout 900 > /root/bench_results/deploy_15b.log 2>&1
echo "deploy_15b rc=$?"

echo "===== [2/4] bench Qwen2.5-1.5B-Instruct ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_15b.md > /root/bench_results/bench_15b_run.log 2>&1
echo "bench_15b rc=$?"

echo "===== stop vllm (1.5B) ====="
pkill -f vllm.entrypoints; sleep 8

echo "===== [3/4] deploy Qwen2.5-7B-Instruct-GPTQ-Int8 ====="
mxdeploy deploy /root/models/Qwen2.5-7B-Instruct-GPTQ-Int8 --port 8000 --timeout 900 > /root/bench_results/deploy_7b.log 2>&1
echo "deploy_7b rc=$?"

echo "===== [4/4] bench Qwen2.5-7B-Instruct-GPTQ-Int8 ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_7b.md > /root/bench_results/bench_7b_run.log 2>&1
echo "bench_7b rc=$?"

echo "===== ALL DONE ====="
date
