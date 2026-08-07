#!/bin/bash
# 修复 GLM chat template + 重启 + 压测
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root

echo "===== 停止旧 GLM ====="
pkill -f vllm.entrypoints; sleep 6

echo "===== 下载官方 tokenizer_config.json（含 chat_template）====="
huggingface-cli download zai-org/glm-4-9b-chat-hf tokenizer_config.json --local-dir /tmp/glm_tok > /tmp/dl_tok.log 2>&1
echo "下载 rc=$?"
ls -la /tmp/glm_tok/tokenizer_config.json

echo "===== 检查 chat_template ====="
python -c "
import json
d = json.load(open('/tmp/glm_tok/tokenizer_config.json'))
print('chat_template 存在:', 'chat_template' in d)
"

echo "===== 覆盖模型仓库 tokenizer_config.json ====="
cp /tmp/glm_tok/tokenizer_config.json /root/models/glm-4-9b-chat-GPTQ-Int4/tokenizer_config.json
echo "覆盖完成"

echo "===== 重启 GLM ====="
VLLM="/opt/conda/bin/python -m vllm.entrypoints.openai.api_server"
nohup $VLLM --model /root/models/glm-4-9b-chat-GPTQ-Int4 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 8192 \
  --quantization gptq --enforce-eager --trust-remote-code > /tmp/vllm_glm.log 2>&1 &
echo "PID: $!"

for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "GLM 就绪 ($((i*10))s)"; break; fi
  sleep 10
done
curl -s http://127.0.0.1:8000/health || { echo "GLM 启动失败"; grep -iE 'error' /tmp/vllm_glm.log | tail -6; exit 1; }

echo "===== 测试一次推理 ====="
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"/root/models/glm-4-9b-chat-GPTQ-Int4","messages":[{"role":"user","content":"你好"}],"max_tokens":32}' | head -c 300
echo ""

echo "===== bench GLM ====="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output /root/bench_results/bench_glm.md > /root/bench_results/bench_glm_run.log 2>&1
echo "rc=$?"

echo "===== DONE ====="
date
