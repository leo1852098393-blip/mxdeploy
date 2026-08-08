# Benchmark 矩阵：曦云 C500 64G 整卡实测（2026-08-07 晚）

> 实例：模力方舟曦云 C500 **64G 整卡**（PyTorch 可见 63.59 GiB，128 核 CPU，128G 内存）
> MACA 3.5.3.20 · torch 2.8.0+metax3.5.3.9 · vllm_metax 0.17.0+maca · mxdeploy 0.2.0
> 统一压测参数：并发 8 / 请求 50 / max_tokens 256 / gpu-memory-utilization 0.8
> 状态：**数据已存档，未发布**（等待统一发版节奏）

## 结果

| 模型 | 精度 | 模式 | 吞吐 (t/s) | TTFT (ms) | TTFT P95 (ms) | TPOT (ms) | 显存 (MB) | 成功率 |
|------|------|------|-----------|-----------|---------------|-----------|-----------|--------|
| Qwen2.5-7B-Instruct | FP16 | compile | **101.78** | 478.56 | 2807.31 | 8.17 | 53249 | 100% |
| GLM-4-9B-chat | FP16 | compile | **79.84** | 54.23 | 101.05 | 12.22 | 53247 | 100% |
| Qwen2.5-14B-Instruct-GPTQ-Int4 | INT4 | eager | **46.57** | 1408.63 | 8498.54 | 14.15 | 53043 | 100% |

## 洞察

1. **eager 模式性能与显存无关**：14B-INT4 eager 在 64G 整卡 46.57 t/s ≈ 16G vGPU 的 46.58 t/s——同一物理卡计算力，vGPU 分片不影响 eager 吞吐。64G 的优势是能跑 compile 模式和更大模型。
2. **GLM-9B FP16（compile）79.84 < GLM-9B-INT4（eager）90.51**：量化版反而更快（显存带宽压力小）。
3. **7B FP16 compile 101.78 < 7B-INT8 159.21**：量化 7B 比 FP16 7B 快 56%，FP16 换来精度。
4. **显存占用规律**：FP16 7B/9B 占 ~53G（util 0.8 配额内），INT4 14B 占 ~53G（权重小但 KV cache 按配额分配）。

## 新坑记录（MISC-005 候选，未入库）

**Qwen2.5-14B-GPTQ-Int4 在 compile 模式加载失败：**
```
ValueError: Detected some but not all shards of model.layers.44.mlp.gate_up_proj are quantized.
All shards of fused layers to have the same precision.
```
- 干净下载后依然复现 → 非下载问题，是 **vllm_metax 0.17.0 的 GPTQ fused layer 分片检查 bug**（compile 模式检查过严）
- **解法：--enforce-eager 绕过**（16G 和 64G 卡均验证成功）
- 建议规则：MISC-005，patterns 含 "not all shards" / "fused layers to have the same precision"

## 原报告文件

- [7B FP16](bench_7bfp16.md)
- [14B-INT4 eager](bench_14b64_eager.md)
- [GLM-9B FP16](bench_glm64.md)
