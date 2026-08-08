# Changelog

## 0.2.1 (2026-08-08) — 64G 整卡实测 + MISC-005

- **新规则 MISC-005**：GPTQ fused 层分片精度检查 bug（vllm_metax 0.17 compile 模式），提示 `--enforce-eager` 绕过（16G/64G 均验证）
- **64G 整卡实测报告**：docs/BENCHMARK_64G_C500.md（7B FP16 101.78 t/s / GLM-9B FP16 79.84 t/s / 14B-INT4 46.57 t/s）
- **README 更新**：新增 64G 实测小节 + 知识库表补齐/修正规则 ID
- **脚本归档**：64G 测试脚本归入 scripts/64g/
- 53 项测试全绿

## 0.2.0 (2026-08-07) — v0.2 里程碑

- **deploy 参数透传**：新增 --enforce-eager / --trust-remote-code / --quantization / --extra-args（14B/GLM 等特殊模型一键部署）
- **init 显存检测修正**：改用 PyTorch 可见显存（vGPU 实例实际配额，16G 实例不再误报物理 64G）
- **默认显存利用率 0.9 → 0.8**：规避 torch.compile autotune OOM（MEM-002）
- **OOM 自动降级重试**：部署遇显存不足自动降 util 重试（最多 3 次）
- **量化自动识别完善**：GPTQ-Int4 模型自动加 --quantization gptq
- **bench fallback**：chat 接口失败自动切换 completions 接口
- **文本去公司名**：MetaX/沐曦/模力方舟 → 中性表述（软著合规）
- 52 项测试全绿

## 0.1.3 (2026-08-07)

- 新增知识库规则：MISC-003（trust-remote-code）、MISC-004（chat_template 缺失）、MEM-003（KV cache 不足）
- 实测矩阵扩展至 6 模型：新增 GLM-4-9B-GPTQ-Int4（90.51 t/s）、Qwen2.5-14B-GPTQ-Int4（46.58 t/s）
- 44 项测试全绿

## 0.1.2 (2026-08-07)

- 新增知识库规则 MEM-002：vLLM 启动 OOM（torch.compile autotune 显存不足）→ 降 gpu-memory-utilization 至 0.8
- 多模型实测矩阵：Qwen2.5-1.5B / DeepSeek-R1-Distill-1.5B / Qwen2.5-3B / Qwen2.5-7B-GPTQ-Int8（docs/BENCHMARK_MATRIX_C500_16G.md）
- 41 项测试全绿

## 0.1.1 (2026-08-07)

- 修复 README 相对链接（PyPI 渲染失效）→ 改为 GitHub 绝对链接

## 0.1.0 (2026-08-07) — 首个开源版本

- **init**：环境体检 — mx-smi / torch(+metax) / vLLM(+maca) / 系统信息检测，table/json 输出
- **deploy**：一键部署 — 精度检查（FP8 拦截）、vLLM 配置生成、服务拉起、健康检查、推理验证
- **bench**：性能测试 — 流式压测吞吐 / TTFT / P95 / TPOT / 显存，table/json/markdown 输出
- **doctor**：AI 排障 — 内置 8+ 条真实踩坑规则（NET-001 / ENV-001 / PIP-001 / FP8-001 / OOM-001 等），支持 LLM 分析
- 40 项单元测试全绿
- 实测：Qwen2.5-3B-Instruct @ 曦云 C500 16G vGPU，吞吐 160.99 tokens/s
