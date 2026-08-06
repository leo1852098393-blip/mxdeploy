#!/bin/bash
echo "=== 推理测试（chat completion） ==="
timeout 60 curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-3B-Instruct","messages":[{"role":"user","content":"用一句话介绍国产GPU"}],"max_tokens":100}' 2>&1 | head -c 800
echo ""
echo "=== 显存占用 ==="
mx-smi --show-memory 2>/dev/null | grep -E "vram (total|used)" | head -4
