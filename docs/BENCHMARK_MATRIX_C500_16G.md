# Benchmark 矩阵：曦云 C500 16G vGPU 多模型实测

> 实测环境：模力方舟（moark.com）曦云 C500 16G vGPU
> MACA 3.5.3.20 · torch 2.8.0+metax3.5.3.9 · vllm_metax 0.17.0+maca · Python 3.10.10
> 统一压测参数：并发 8 / 请求 50 / max_tokens 256 / gpu-memory-utilization 0.8 / 流式输出
> 实测日期：2026-08-07

## 结果矩阵

| 模型 | 精度 | 模式 | max_len | 吞吐 (t/s) | TTFT (ms) | TTFT P95 (ms) | TPOT (ms) | 显存 (MB) | 成功率 |
|------|------|------|---------|-----------|-----------|---------------|-----------|-----------|--------|
| Qwen2.5-1.5B-Instruct | FP16 | compile | 8192 | **204.75** | 38.15 | 108.70 | 4.77 | 13573 | 100% |
| DeepSeek-R1-Distill-Qwen-1.5B | FP16 | compile | 8192 | **200.55** | 34.54 | 71.81 | 4.93 | 13561 | 100% |
| Qwen2.5-3B-Instruct | FP16 | compile | 8192 | **153.65** | 48.21 | 134.90 | 6.40 | 13599 | 100% |
| Qwen2.5-7B-Instruct-GPTQ-Int8 | INT8 | compile | 8192 | **159.21** | 41.67 | 108.31 | 6.15 | 13827 | 100% |
| GLM-4-9B-chat-GPTQ-Int4 | INT4 | eager | 8192 | **90.51** | 45.97 | 72.44 | 10.79 | 13367 | 100% |
| Qwen2.5-14B-Instruct-GPTQ-Int4 | INT4 | eager | 4096 | **46.58** | 1398.79 | 8445.27 | 14.05 | 13381 | 100% |

> 模式说明：compile = vLLM 默认 torch.compile；eager = --enforce-eager（14B 因显存限制需跳过编译；GLM 因量化层兼容性）。
> 14B 因显存限制 max_model_len 降至 4096（KV cache 不足）。

## 洞察

1. **量化路径完整验证**：INT8（7B）与 INT4（9B GLM / 14B Qwen）均部署成功。16G 卡可跑 7B-INT8（159 t/s）、9B-INT4（90 t/s）、14B-INT4（46 t/s）。
2. **量化 7B ≈ 全精度 3B**（159 vs 154 t/s）：INT8 量化效率极高，"小卡跑大模型"可行。
3. **1.5B 档位最快**（~200 t/s），适合高并发低延迟场景；Qwen / DeepSeek 同尺寸性能持平，架构适配稳定。
4. **14B 的 eager 模式 TTFT 高**（均值 1.4s / P95 8.4s）：跳过 torch.compile 后 prefill 无优化，适合离线批量场景；若需实时对话应使用更大显存实例开启编译。
5. **GLM 架构验证**：需 `--trust-remote-code`；社区量化版可能缺 chat_template，需从官方仓库补齐 tokenizer_config.json（详见知识库规则）。
6. 显存均落在 13.3~13.8G（util 0.8 下按配额分配），6 模型显存曲线平滑。

## 各模型原始报告

- [Qwen2.5-1.5B-Instruct](bench_15b.md)
- [DeepSeek-R1-Distill-Qwen-1.5B](bench_ds.md)
- [Qwen2.5-3B-Instruct](bench_3b.md)（旧版 30 请求数据见 [BENCHMARK_3B_C500_16G.md](BENCHMARK_3B_C500_16G.md)）
- [Qwen2.5-7B-Instruct-GPTQ-Int8](bench_7b.md)
- [GLM-4-9B-chat-GPTQ-Int4](bench_glm.md)
- [Qwen2.5-14B-Instruct-GPTQ-Int4](bench_14b.md)

## 复现

```bash
pip install mxdeploy
mxdeploy deploy <model> --gpu-memory-utilization 0.8
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output report.md
```

注意：14B 及更大模型建议 `--enforce-eager --max-model-len 4096`（v0.2 起 mxdeploy deploy 将支持透传这些参数）。
