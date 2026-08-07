# Roadmap

> mxdeploy 的演进路线：从「沐曦专属部署工具」走向「国产 GPU 零接触运维平台」。
> 里程碑与版本规划会随社区反馈和实测数据动态调整。

## 现状（v0.1.1，2026-08）

- ✅ init / deploy / bench / doctor 四命令闭环
- ✅ 沐曦曦云 C500 真实环境验证（Qwen2.5-3B，160.99 tokens/s）
- ✅ Apache-2.0 开源，GitHub + PyPI 双渠道分发
- ⚠️ 局限：仅支持沐曦 + vLLM，单机单卡，知识库靠手工积累

## 升级方向

### 1. 多平台适配（Provider 架构）— 最高优先

从「沐曦硬编码」重构为 Provider 插件化：一套 CLI，通吃国产 GPU。

- [ ] 定义 Provider 接口（环境检测 / 精度检查 / 引擎拉起 / 显存查询）
- [ ] 沐曦重构为首个 Provider（回归验证）
- [ ] 昇腾 CANN Provider（Atlas 实测）
- [ ] 寒武纪 MLU / 海光 DCU Provider（社区共建）

### 2. Agent 化（零接触运维闭环）

mxdeploy 命令作为 Agent 工具被编排：部署 → 评测 → 排障 → 自动修复的全自动闭环。

- [ ] deploy / bench / doctor 输出标准化（稳定 JSON schema + 退出码语义）
- [ ] 作为 AgentTeams / MCP 工具接入
- [ ] Manager 编排：异常自动触发 doctor → 自动修复 → 重新部署

### 3. doctor 进化（排障智能）

- [ ] 规则库 → RAG 知识库（自动沉淀社区报错与修复方案）
- [ ] 自动修复（诊断后直接执行修复命令，支持 dry-run）
- [ ] 参数自动推荐（按模型 + 显存自动推荐 TP / 量化 / 并发数）

### 4. 引擎与模型扩展

- [ ] SGLang 引擎支持
- [ ] INT8 / INT4 / AWQ 量化支持
- [ ] 实测矩阵扩展：DeepSeek / GLM / Qwen 全系
- [ ] 多卡张量并行（TP）/ 流水线并行（PP）

### 5. 企业化

- [ ] YAML 配置驱动部署（可复现、可审计）
- [ ] 定时巡检 + 告警（cron + webhook）
- [ ] 部署审计日志

## 版本规划

| 版本 | 内容 | 目标时间 |
|------|------|----------|
| v0.2.0 | Provider 架构抽象 + Agent 化基础（稳定输出/退出码） | 2026-08 |
| v0.3.0 | 昇腾 CANN Provider + SGLang 引擎 | 2026-09 |
| v0.4.0 | doctor RAG 知识库 + 自动修复 | 2026-09/10 |
| v0.5.0 | 实测矩阵扩展 + 量化支持 | 2026-10 |
| v1.0.0 | 企业特性（配置驱动 / 巡检告警） | 2026-11+ |

## 参与

欢迎任何形式的贡献：Provider 适配、知识库规则、实测数据、文档。

- 提 Issue / PR：[GitHub](https://github.com/leo1852098393-blip/mxdeploy)
- 讨论方向：在 Issue 中带 `[roadmap]` 标签
