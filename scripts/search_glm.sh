#!/bin/bash
# 搜索 GLM INT4 模型仓库
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate

python - <<'EOF'
import urllib.request, json, urllib.parse

def search(q, limit=10):
    url = "https://hf-mirror.com/api/models?" + urllib.parse.urlencode({
        "search": q, "limit": limit, "sort": "downloads", "direction": -1
    })
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

for q in ["glm-4-9b int4", "glm-4-9b gptq", "glm-4-9b chat"]:
    print(f"=== search: {q} ===")
    try:
        items = search(q)
        for m in items[:8]:
            print(" -", m.get("modelId"), "| downloads:", m.get("downloads"), "| likes:", m.get("likes"))
    except Exception as e:
        print("ERR:", e)
EOF
