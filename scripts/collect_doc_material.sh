#!/bin/bash
# 收集 mxdeploy 说明书素材：所有命令真实输出
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root
mkdir -p /root/doc_material

echo "=== 1. help ==="
mxdeploy --help > /root/doc_material/01_help.txt 2>&1

echo "=== 2. version ==="
mxdeploy version > /root/doc_material/02_version.txt 2>&1

echo "=== 3. init ==="
mxdeploy init > /root/doc_material/03_init.txt 2>&1

echo "=== 4. init json ==="
mxdeploy init --format json > /root/doc_material/04_init_json.txt 2>&1

echo "=== 5. doctor --list ==="
mxdeploy doctor --list > /root/doc_material/05_doctor_list.txt 2>&1

echo "=== 6. doctor 示例排障 ==="
cat > /tmp/sample_error.log <<'EOF'
Traceback (most recent call last):
  File "/opt/conda/lib/python3.10/site-packages/triton/backends/metax/driver.py", line 30
TypeError: expected str, bytes or os.PathLike object, not NoneType
EOF
mxdeploy doctor /tmp/sample_error.log > /root/doc_material/06_doctor.txt 2>&1

echo "=== 7. 启动 14B 部署（截部署过程）==="
pkill -f vllm.entrypoints; sleep 5
VLLM="/opt/conda/bin/python -m vllm.entrypoints.openai.api_server"
# 先用 --no-launch 截配置生成过程
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --gpu-memory-utilization 0.8 --max-model-len 4096 --no-launch > /root/doc_material/07_deploy_config.txt 2>&1

echo "=== 8. 实际部署 + 健康检查 ==="
nohup $VLLM --model /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 \
  --port 8000 --gpu-memory-utilization 0.8 --max-model-len 4096 \
  --quantization gptq --enforce-eager > /tmp/vllm_doc.log 2>&1 &
echo "vLLM PID: $!"
for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "14B 就绪 ($((i*10))s)"; break; fi
  sleep 10
done
curl -s http://127.0.0.1:8000/health | head -c 300 > /root/doc_material/08_health.txt 2>&1
curl -s http://127.0.0.1:8000/v1/models | head -c 500 > /root/doc_material/09_models.txt 2>&1

echo "=== 9. bench 压测 ==="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 20 --concurrency 4 --max-tokens 128 --format table > /root/doc_material/10_bench.txt 2>&1

echo "=== 10. 推理验证 ==="
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"/root/models/Qwen2.5-14B-Instruct-GPTQ-Int4","messages":[{"role":"user","content":"请用一句话介绍你自己"}],"max_tokens":64}' \
  | python -m json.tool > /root/doc_material/11_inference.txt 2>&1

echo "=== 11. bench markdown 报告 ==="
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 20 --concurrency 4 --max-tokens 128 --format markdown --output /root/doc_material/12_bench_md.md > /root/doc_material/12_bench_md_out.txt 2>&1

echo "=== ALL DONE ==="
ls -la /root/doc_material/
