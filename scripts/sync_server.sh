#!/bin/bash
# 覆盖安装服务器上的 mxdeploy 源码（v0.1.0 → v0.2 新代码）
set -e
SRC_DIR="/root/mxdeploy_new/mxdeploy"
PKG_DIR="/opt/conda/lib/python3.10/site-packages/mxdeploy"

echo "=== 清理旧包 ==="
rm -rf "$PKG_DIR"
echo "=== 拷贝新源码 ==="
cp -r "$SRC_DIR" "$PKG_DIR"
echo "=== 验证 ==="
export MACA_PATH=/opt/maca
source /opt/conda/etc/profile.d/conda.sh
conda activate
python -c "from mxdeploy.deploy.config import DeployConfig; c=DeployConfig(model='x', precision='auto', quantization=None); print('config OK')"
python -c "import mxdeploy.deploy.deploy; print('deploy module OK')"
python -c "import mxdeploy.bench.benchmark; print('bench module OK')"
echo "=== 完成 ==="
