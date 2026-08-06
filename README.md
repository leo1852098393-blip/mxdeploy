# mxdeploy

国产 GPU（MetaX 曦云 C500 / MXMACA 生态）**一键部署 + 评测 + AI 排障** CLI 工具。

一条命令把模型跑起来，出 benchmark 报告，报错自动诊断——降低国产算力迁移门槛。

## 为什么需要

国产 GPU 生态最大的痛点不是算力，而是**部署踩坑**：

- ❌ 下载了 FP8 模型 → 加载失败（曦云 C500 不支持 FP8）
- ❌ `pip install torch` → 覆盖官方 `+metax` 适配版 → GPU 全废
- ❌ 模型未适配 → 报错看不懂，社区没人问

mxdeploy 把这些高频坑变成自动化工具。

## 快速开始

```bash
# 安装（Python 3.10+）
pip install mxdeploy

# 1. 环境体检 —— 检测 mx-smi / torch(+metax) / vLLM(+maca)
mxdeploy init

# 2. 一键部署模型
mxdeploy deploy Qwen/Qwen2.5-7B-Instruct

# 3. 性能测试，出报告
mxdeploy bench Qwen/Qwen2.5-7B-Instruct

# 4. AI 排障 —— 把报错日志喂给它
mxdeploy doctor deploy.log
```

## 命令一览

| 命令 | 功能 | 状态 |
|------|------|------|
| `mxdeploy init` | 环境体检：mx-smi / torch / vLLM / 系统信息 | ✅ M1 |
| `mxdeploy deploy <model>` | 一键部署：精度检查、vLLM 配置生成、服务拉起 | 🚧 M2 |
| `mxdeploy bench <model>` | 性能测试：吞吐 / 延迟 / 显存，JSON+MD 报告 | 🚧 M3 |
| `mxdeploy doctor <log>` | AI 排障：规则引擎 + LLM 分析 | 🚧 M4 |

## 环境要求

- **目标平台**：模力方舟（moark.com）曦云 C500 实例（Linux）
- Python 3.10+
- 沐曦适配版依赖：`torch`（含 `+metax`）、`vllm`（含 `+maca`）—— **切勿用 pip 覆盖官方适配版**

## 开发

```bash
pip install -e ".[dev]"
pytest
```

## 路线图

- M1 (8月)：CLI 骨架 + `init` 环境体检 ✅
- M2 (8月)：`deploy` 一键部署 + Qwen2.5 实测
- M3 (9月)：`bench` 性能测试 + 实测 benchmark 报告
- M4 (9月)：`doctor` 排障知识库
- M5 (10月)：开源发布 + demo 视频

## License

Apache-2.0
