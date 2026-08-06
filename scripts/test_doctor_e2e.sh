#!/bin/bash
# 端到端测试 doctor：用真实踩坑日志验证
export MACA_PATH=/opt/maca
cd /root/mxdeploy

echo "=== 测试 1: HF 超时日志 ==="
cat > /tmp/hf_error.log << 'EOF'
(APIServer pid=1760) INFO [utils.py:302] 
(MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): Max retries exceeded with url: /Qwen/Qwen2.5-3B-Instruct/resolve/main/config.json (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x7f5c7caade10>, 'Connection to huggingface.co timed out. (connect timeout=10)'))"), '(Request ID: f0f5d8d4-07d1-4fca-9fb0-33a6db7ccbac)')' thrown while requesting HEAD https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/resolve/main/config.json
EOF
/opt/conda/bin/mxdeploy doctor /tmp/hf_error.log --format json 2>&1 | head -30
