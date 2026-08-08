# mxdeploy

[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/leo1852098393-blip/mxdeploy/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/mxdeploy?color=%2334D058&label=pypi%20package)](https://pypi.org/project/mxdeploy/)
[![Platform](https://img.shields.io/badge/platform-Linux-blue)]()

> 国产 GPU（MetaX 曦云 C500 / MXMACA 生态）一键部署 + 评测 + AI 排障 CLI。
> 一条命令把模型跑起来，出 benchmark 报告，报错自动诊断。

📖 **新手教程**：[docs/TUTORIAL.md](https://github.com/leo1852098393-blip/mxdeploy/blob/master/docs/TUTORIAL.md) — 从安装到实战，10 分钟上手。

## Features

- **一键部署**：精度检查 → vLLM 配置生成 → 服务拉起 → 健康检查，全程自动化，FP8 等不支持的模型自动拦截
- **环境体检**：自动检测 mx-smi / torch(+metax) / vLLM(+maca) 适配状态，部署前先排雷
- **性能评测**：流式压测吞吐 / 首token延迟 / P95 / TPOT / 显存，输出 table / JSON / Markdown 报告
- **AI 排障**：内置真实踩坑知识库（8+ 条规则），喂日志即出根因和修复方案，critical 级别自动失败退出

## 安装

```bash
pip install mxdeploy
```

要求 Python 3.10+，目标平台为 Linux（模力方舟曦云 C500 实测环境）。

## 快速开始

```bash
# 1. 环境体检 —— 检测 mx-smi / torch(+metax) / vLLM(+maca)
mxdeploy init

# 2. 一键部署模型
mxdeploy deploy Qwen/Qwen2.5-3B-Instruct

# 3. 性能测试，出报告
mxdeploy bench Qwen/Qwen2.5-3B-Instruct

# 4. AI 排障 —— 把报错日志喂给它
mxdeploy doctor deploy.log
```

## 命令一览

| 命令 | 功能 |
|------|------|
| `mxdeploy init` | 环境体检：mx-smi / torch / vLLM / 系统信息 |
| `mxdeploy deploy <model>` | 一键部署：精度检查、配置生成、服务拉起、健康检查 |
| `mxdeploy bench <model>` | 性能测试：吞吐 / TTFT / P95 / TPOT / 显存 |
| `mxdeploy doctor <log>` | AI 排障：规则引擎 + LLM 分析 |
| `mxdeploy version` | 版本信息 |

## 实测数据（模力方舟曦云 C500 16G vGPU，统一：并发8/请求50/max_tokens 256/util 0.8）

| 模型 | 精度 | 模式 | 吞吐 (t/s) | TTFT (ms) | TPOT (ms) | 成功率 |
|------|------|------|-----------|-----------|-----------|--------|
| Qwen2.5-1.5B | FP16 | compile | **204.75** | 38.15 | 4.77 | 100% |
| DeepSeek-R1-Distill-1.5B | FP16 | compile | **200.55** | 34.54 | 4.93 | 100% |
| Qwen2.5-3B | FP16 | compile | **153.65** | 48.21 | 6.40 | 100% |
| Qwen2.5-7B-GPTQ-Int8 | INT8 | compile | **159.21** | 41.67 | 6.15 | 100% |
| GLM-4-9B-GPTQ-Int4 | INT4 | eager | **90.51** | 45.97 | 10.79 | 100% |
| Qwen2.5-14B-GPTQ-Int4 | INT4 | eager | **46.58** | 1398.79 | 14.05 | 100% |

完整矩阵报告见 [docs/BENCHMARK_MATRIX_C500_16G.md](https://github.com/leo1852098393-blip/mxdeploy/blob/master/docs/BENCHMARK_MATRIX_C500_16G.md)。

### 64G 整卡（模力方舟曦云 C500 64G，PyTorch 可见 63.59 GiB，同参数）

| 模型 | 精度 | 模式 | 吞吐 (t/s) | TTFT (ms) | TPOT (ms) | 成功率 |
|------|------|------|-----------|-----------|-----------|--------|
| Qwen2.5-7B-Instruct | FP16 | compile | **101.78** | 478.56 | 8.17 | 100% |
| GLM-4-9B-chat | FP16 | compile | **79.84** | 54.23 | 12.22 | 100% |
| Qwen2.5-14B-Instruct-GPTQ-Int4 | INT4 | eager | **46.57** | 1408.63 | 14.15 | 100% |

> 关键洞察：14B-INT4 eager 在 64G 整卡 46.57 t/s ≈ 16G vGPU 的 46.58 t/s——同一物理卡计算力，vGPU 分片不影响 eager 吞吐；64G 的优势是能跑 compile 模式和更大模型。
> 完整报告见 [docs/BENCHMARK_64G_C500.md](https://github.com/leo1852098393-blip/mxdeploy/blob/master/docs/BENCHMARK_64G_C500.md)。

## 排障知识库

全部规则来自真实部署实测，命中即给出修复方案：

| 规则 | 场景 |
|------|------|
| NET-001 | huggingface.co 超时 → 自动提示 HF_ENDPOINT 镜像 |
| ENV-001 | 非交互 SSH 缺 MACA_PATH → vLLM import 崩溃 |
| DEP-001 | pip 覆盖官方 torch(+metax) 适配版 |
| PREC-001 | 曦云 C500 不支持 FP8 → 提示换 FP16/INT8 |
| MEM-001 | 显存不足 → 给出量化/换卡建议 |
| MEM-002 | util 0.9 + torch.compile autotune OOM → 降 0.8 |
| MEM-003 | KV cache 不足 → 降 max-model-len（实测 14B-INT4 8192→4096） |
| MISC-003 | 模型需 trust-remote-code → 加 `--trust-remote-code` |
| MISC-004 | 量化版缺 chat_template → 从官方仓库补齐 tokenizer |
| MISC-005 | GPTQ fused 层分片精度检查 bug（compile 模式）→ 加 `--enforce-eager` |
| ... | 更多规则见 `mxdeploy doctor --list` |

## 兼容性

- **平台**：Linux（模力方舟曦云 C500 实例实测）
- **Python**：3.10+
- **依赖**：沐曦适配版 `torch`（+metax）、`vllm`（+maca）——切勿用 pip 覆盖官方适配版
- **注意**：非交互 SSH 环境需显式 `export MACA_PATH=/opt/maca`

## 开发

```bash
git clone https://github.com/leo1852098393-blip/mxdeploy
cd mxdeploy
pip install -e ".[dev]"
pytest        # 53 tests
```

## License

[Apache-2.0](https://github.com/leo1852098393-blip/mxdeploy/blob/master/LICENSE)
