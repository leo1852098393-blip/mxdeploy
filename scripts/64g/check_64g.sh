#!/bin/bash
# 64G 实例环境检查
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate

echo "=== Python ==="
python --version

echo "=== torch（含 PyTorch 可见显存）==="
python -c "import torch; print('torch', torch.__version__); print('cuda available:', torch.cuda.is_available()); p = torch.cuda.get_device_properties(0); print('PyTorch 可见显存: %.2f GiB' % (p.total_memory/1024**3))" 2>&1 | tail -3

echo "=== vllm_metax ==="
python -c "import vllm_metax; print('vllm_metax OK')" 2>&1 | tail -1

echo "=== mxdeploy ==="
which mxdeploy && mxdeploy version 2>&1 | head -2 || echo "mxdeploy 未安装"

echo "=== 磁盘 ==="
df -h / | tail -1
