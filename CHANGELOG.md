# Changelog

## 0.1.0 (2026-08-07) — 首个开源版本

- **init**：环境体检 — mx-smi / torch(+metax) / vLLM(+maca) / 系统信息检测，table/json 输出
- **deploy**：一键部署 — 精度检查（FP8 拦截）、vLLM 配置生成、服务拉起、健康检查、推理验证
- **bench**：性能测试 — 流式压测吞吐 / TTFT / P95 / TPOT / 显存，table/json/markdown 输出
- **doctor**：AI 排障 — 内置 8+ 条真实踩坑规则（NET-001 / ENV-001 / PIP-001 / FP8-001 / OOM-001 等），支持 LLM 分析
- 40 项单元测试全绿
- 实测：Qwen2.5-3B-Instruct @ 曦云 C500 16G vGPU，吞吐 160.99 tokens/s
