# mxdeploy

国产 GPU（MetaX 曦云 C500 / MXMACA 生态）**一键部署 + 评测 + AI 排障** CLI 工具。

一条命令把模型跑起来，出 benchmark 报告，报错自动诊断——降低国产算力迁移门槛。

## 为什么需要

国产 GPU 生态最大的痛点不是算力，而是**部署踩坑**：

- ❌ 下载了 FP8 模型 → 加载失败（曦云 C500 不支持 FP8）
- ❌ `pip install torch` → 覆盖官方 `+metax` 适配版 → GPU 全废
- ❌ 模型未适配 → 报错看不懂，社区没人问

mxdeploy 把这些高频坑变成自动化工具：体检 → 部署 → 评测 → 排障，全流程一条命令。

## 快速开始

```bash
# 安装（Python 3.10+，目标平台为 Linux + 沐曦适配环境）
pip install mxdeploy

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

| 命令 | 功能 | 状态 |
|------|------|------|
| `mxdeploy init` | 环境体检：mx-smi / torch / vLLM / 系统信息 | ✅ |
| `mxdeploy deploy <model>` | 一键部署：精度检查、vLLM 配置生成、服务拉起、健康检查 | ✅ |
| `mxdeploy bench <model>` | 性能测试：吞吐 / 首token延迟 / P95 / TPOT / 显存 | ✅ |
| `mxdeploy doctor <log>` | AI 排障：规则引擎 + LLM 分析 | ✅ |
| `mxdeploy version` | 版本信息 | ✅ |

## 实测数据（模力方舟曦云 C500 16G vGPU）

Qwen2.5-3B-Instruct 全精度 FP16：

| 指标 | 数值 |
|------|------|
| 吞吐 | 160.99 tokens/s |
| 首token延迟 (TTFT) | 40.85 ms |
| P95 延迟 | 72.32 ms |
| 每token延迟 (TPOT) | 6.11 ms |
| 成功率 | 100% |
| 显存占用 | 15361 MB / 16G |

完整报告见 [docs/BENCHMARK_3B_C500_16G.md](docs/BENCHMARK_3B_C500_16G.md)。

## 踩坑知识库（doctor 内置规则）

全部来自真实部署实测，规则引擎命中即给出修复方案：

| 规则 | 场景 |
|------|------|
| NET-001 | huggingface.co 超时 → 自动提示 HF_ENDPOINT 镜像 |
| ENV-001 | 非交互 SSH 缺 MACA_PATH → vLLM import 崩溃 |
| PIP-001 | pip 覆盖官方 torch(+metax) 适配版 |
| FP8-001 | 曦云 C500 不支持 FP8 → 提示换 FP16/INT8 |
| OOM-001 | 显存不足 → 给出量化/换卡建议 |
| ... | 更多规则见 `mxdeploy doctor --list` |

## 环境要求

- **目标平台**：模力方舟（moark.com）曦云 C500 实例（Linux）
- Python 3.10+
- 沐曦适配版依赖：`torch`（含 `+metax`）、`vllm`（含 `+maca`）—— **切勿用 pip 覆盖官方适配版**
- 非交互 SSH 环境需显式 `export MACA_PATH=/opt/maca`

## 开发

```bash
git clone <repo-url>
cd mxdeploy
pip install -e ".[dev]"
pytest        # 40 tests
```

## 路线图

- M1：CLI 骨架 + `init` 环境体检 ✅
- M2：`deploy` 一键部署 + Qwen2.5 实测 ✅
- M3：`bench` 性能测试 + 首份 benchmark 报告 ✅
- M4：`doctor` 排障知识库（规则引擎）✅
- M5：开源发布 + demo 视频（进行中）

## License

[Apache-2.0](LICENSE)
