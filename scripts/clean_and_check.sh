#!/bin/bash
# 清理已测模型 + 查询 GLM INT4 可用仓库
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
export HF_ENDPOINT=https://hf-mirror.com

echo "=== 清理前磁盘 ==="
df -h / | tail -1

echo "=== 删除已测模型 ==="
rm -rf /root/models/Qwen2.5-1.5B-Instruct
rm -rf /root/models/Qwen2.5-7B-Instruct-GPTQ-Int8
rm -rf /root/models/DeepSeek-R1-Distill-Qwen-1.5B
rm -rf /root/.cache/huggingface/hub/models--Qwen--Qwen2.5-3B-Instruct
rm -rf /root/models/Qwen2.5-3B-Instruct
echo "删除完成"

echo "=== 清理后磁盘 ==="
df -h / | tail -1
ls /root/models/ 2>/dev/null

echo "=== 查询 GLM INT4 仓库（hf-mirror API）==="
timeout 20 python - <<'EOF'
import urllib.request, json
for repo in ["THUDM/glm-4-9b-chat-int4", "THUDM/glm-4-9b-chat-0414-int4", "THUDM/glm-4-9b-chat-1m-int4"]:
    try:
        req = urllib.request.Request(f"https://hf-mirror.com/api/models/{repo}", headers={"User-Agent": "curl"})
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode())
            print("EXISTS:", repo, "| downloads:", d.get("downloads"))
    except Exception as e:
        print("MISS:", repo, type(e).__name__)
EOF
