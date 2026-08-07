#!/bin/bash
# 用 v0.2 新代码重新生成软著素材（干净文本：无公司名 + 新参数展示）
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /root
rm -rf /root/doc_material && mkdir -p /root/doc_material

echo "=== 1. help（无 MetaX）==="
mxdeploy --help > /root/doc_material/01_help.txt 2>&1

echo "=== 2. version ==="
mxdeploy version > /root/doc_material/02_version.txt 2>&1

echo "=== 3. init（显存 15584）==="
mxdeploy init > /root/doc_material/03_init.txt 2>&1

echo "=== 4. init json ==="
mxdeploy init --format json > /root/doc_material/04_init_json.txt 2>&1

echo "=== 5. doctor --list ==="
mxdeploy doctor --list > /root/doc_material/05_doctor_list.txt 2>&1

echo "=== 6. doctor 示例排障（无沐曦）==="
cat > /tmp/sample_error.log <<'EOF'
Traceback (most recent call last):
  File "/opt/conda/lib/python3.10/site-packages/triton/backends/metax/driver.py", line 30
TypeError: expected str, bytes or os.PathLike object, not NoneType
EOF
mxdeploy doctor /tmp/sample_error.log > /root/doc_material/06_doctor.txt 2>&1

echo "=== 7. deploy 配置生成（展示新参数）==="
mxdeploy deploy /root/models/Qwen2.5-14B-Instruct-GPTQ-Int4 --port 8000 --gpu-memory-utilization 0.8 --max-model-len 4096 --enforce-eager --no-launch > /root/doc_material/07_deploy_config.txt 2>&1

echo "=== 8-12. GLM 服务 + bench + 推理（GLM 已在跑）==="
curl -s http://127.0.0.1:8000/health | head -c 300 > /root/doc_material/08_health.txt 2>&1
curl -s http://127.0.0.1:8000/v1/models | head -c 500 > /root/doc_material/09_models.txt 2>&1
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 20 --concurrency 4 --max-tokens 128 --format table > /root/doc_material/10_bench.txt 2>&1
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"/root/models/glm-4-9b-chat-GPTQ-Int4","messages":[{"role":"user","content":"请用一句话介绍你自己"}],"max_tokens":64}' \
  | python -m json.tool > /root/doc_material/11_inference.txt 2>&1
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 20 --concurrency 4 --max-tokens 128 --format markdown --output /root/doc_material/12_bench_md.md > /root/doc_material/12_bench_md_out.txt 2>&1

echo "=== ALL DONE ==="
ls /root/doc_material/
