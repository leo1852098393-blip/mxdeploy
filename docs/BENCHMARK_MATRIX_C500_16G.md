# Benchmark 矩阵：曦云 C500 16G vGPU 多模型实测

> 实测环境：模力方舟（moark.com）曦云 C500 16G vGPU
> MACA 3.5.3.20 · torch 2.8.0+metax3.5.3.9 · vllm_metax 0.17.0+maca · Python 3.10.10
> 统一压测参数：并发 8 / 请求 50 / max_tokens 256 / gpu-memory-utilization 0.8 / 流式输出

## 结果矩阵

| 模型 | 精度 | 吞吐 (tokens/s) | TTFT 均值 (ms) | TTFT P95 (ms) | TPOT (ms) | 显存 (MB) | 成功率 |
|------|------|-----------------|-----------------|---------------|-----------|-----------|--------|
| Qwen2.5-1.5B-Instruct | FP16 | **204.75** | 38.15 | 108.70 | 4.77 | 13573 | 100% |
| DeepSeek-R1-Distill-Qwen-1.5B | FP16 | **200.55** | 34.54 | 71.81 | 4.93 | 13561 | 100% |
| Qwen2.5-3B-Instruct | FP16 | **153.65** | 48.21 | 134.90 | 6.40 | 13599 | 100% |
| Qwen2.5-7B-Instruct-GPTQ-Int8 | INT8 | **159.21** | 41.67 | 108.31 | 6.15 | 13827 | 100% |

## 洞察

1. **量化 7B ≈ 全精度 3B 的吞吐**（159 vs 154 tokens/s）：INT8 量化在 C500 上效率极高，16G 卡跑 7B 不吃亏。这是"小卡跑大模型"的可行路径。
2. **1.5B 档位最快**（~200 tokens/s），适合高并发低延迟场景；DeepSeek-R1-Distill 与 Qwen2.5 同尺寸性能基本持平，说明 C500 对主流架构适配稳定。
3. **显存均落在 13.5~13.8G**：util 0.8 下 KV cache 按配额分配，4 模型显存占用曲线平滑，无异常波动。
4. **成功率全部 100%**：稳定复现，无偶发失败。

## 注意

- 0.9 显存利用率在 torch.compile autotune 阶段会 OOM（见知识库 MEM-002），统一采用 0.8。
- 实测日期 2026-08-07，vllm_metax 版本 0.17.0；新版本可能改变数据。

## 各模型原始报告

- [Qwen2.5-1.5B-Instruct](bench_15b.md)
- [DeepSeek-R1-Distill-Qwen-1.5B](bench_ds.md)
- [Qwen2.5-3B-Instruct](bench_3b.md)（旧版 30 请求数据见 [BENCHMARK_3B_C500_16G.md](BENCHMARK_3B_C500_16G.md)）
- [Qwen2.5-7B-Instruct-GPTQ-Int8](bench_7b.md)

## 复现

```bash
pip install mxdeploy
mxdeploy deploy <model> --gpu-memory-utilization 0.8
mxdeploy bench --base-url http://127.0.0.1:8000 --requests 50 --concurrency 8 --max-tokens 256 --format markdown --output report.md
```
