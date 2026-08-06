#!/bin/bash
# 测试 2: MACA_PATH 崩溃日志（今天的真实报错）
export MACA_PATH=/opt/maca
cd /root/mxdeploy

cat > /tmp/maca_error.log << 'EOF'
Traceback (most recent call last):
  File "/opt/conda/lib/python3.10/site-packages/vllm/env_override.py", line 106, in <module>
  File "/opt/conda/lib/python3.10/site-packages/triton/backends/metax/driver.py", line 30, in <module>
    maca_include_dir = [os.path.join(maca_home_dirs(), "include")]
TypeError: expected str, bytes or os.PathLike object, not NoneType
EOF

echo "=== 测试 2: MACA_PATH 崩溃 ==="
/opt/conda/bin/mxdeploy doctor /tmp/maca_error.log 2>&1 | head -25
