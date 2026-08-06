#!/bin/bash
# 远程环境测试脚本
export MACA_PATH=/opt/maca
export LD_LIBRARY_PATH=/opt/maca/lib:/opt/maca/ompi/lib:/opt/maca/ucx/lib:/opt/mxdriver/lib:$LD_LIBRARY_PATH
export MACA_CLANG_PATH=/opt/maca/mxgpu_llvm/bin

echo "=== vllm import test ==="
/opt/conda/bin/python -c "import vllm; print('VLLM OK', vllm.__version__)" 2>&1 | tail -5

echo "=== torch test ==="
/opt/conda/bin/python -c "import torch; print('TORCH OK', torch.__version__); print('cuda avail:', torch.cuda.is_available())" 2>&1 | tail -5

echo "=== mxdeploy init ==="
cd /root/mxdeploy && /opt/conda/bin/mxdeploy init --format json 2>&1 | tail -40
