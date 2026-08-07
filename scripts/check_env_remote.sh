#!/bin/bash
# mxdeploy 补测环境检查脚本
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate

echo "=== 1. Python ==="
python --version

echo "=== 2. torch ==="
python -c "import torch; print('torch', torch.__version__)"

echo "=== 3. vllm_metax ==="
python -c "import vllm_metax; print('vllm_metax OK')" 2>&1 | tail -1

echo "=== 4. vllm cli ==="
which vllm

echo "=== 5. 磁盘 ==="
df -h /root /opt /tmp 2>/dev/null | tail -4

echo "=== 6. 内存 ==="
free -g | head -2

echo "=== 7. 模型缓存 ==="
ls -la /root/.cache/huggingface/hub 2>/dev/null | head -10

echo "=== 8. HF 镜像测试 ==="
timeout 8 curl -sI https://hf-mirror.com 2>&1 | head -2 || echo "hf-mirror 不通"
