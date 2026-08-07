# mxdeploy 上手教程（从零到会用）

> 面向第一次使用 mxdeploy 的同学。跟着做一遍，你就能独立完成：**环境体检 → 一键部署 → 性能压测 → 报错排障** 全流程。

---

## 0. mxdeploy 是干嘛的？（30 秒版）

mxdeploy 是**国产 GPU（沐曦曦云）的一键部署 + 评测 + 排障工具**。

以前你部署一个大模型到国产卡上，要手动配环境、手动装依赖、踩一堆没人回答过的坑；现在：

```bash
mxdeploy init     # 体检：环境行不行？
mxdeploy deploy   # 部署：把模型跑起来
mxdeploy bench    # 压测：跑多快？卡不卡？
mxdeploy doctor   # 排障：报错了？自动诊断
```

四条命令，从"想跑模型"到"模型跑起来且知道性能"。

---

## 1. 环境要求（先确认你的机器）

| 项 | 要求 | 说明 |
|---|---|---|
| 系统 | Linux | 实测环境：模力方舟曦云 C500 实例 |
| Python | 3.10+ | `python3 --version` 确认 |
| GPU | 沐曦曦云 C500（MXMACA 生态） | 有 `mx-smi` 命令即可 |
| 依赖 | torch(+metax)、vllm(+maca) | 沐曦官方适配版，**千万别用 pip 覆盖** |

> 💡 没有国产 GPU 也能学：`init` 和 `doctor` 可以在普通机器上跑（会提示检测不到 mx-smi），`deploy`/`bench` 需要真机。

---

## 2. 安装

```bash
# 方式一：pip 安装（推荐）
pip install mxdeploy

# 如果报"No matching distribution"（镜像同步延迟），用官方源：
pip install mxdeploy -i https://pypi.org/simple

# 方式二：源码安装（开发用）
git clone https://github.com/leo1852098393-blip/mxdeploy
cd mxdeploy
pip install -e ".[dev]"
```

验证安装：

```bash
mxdeploy version
# mxdeploy 0.1.1
```

---

## 3. 第一步：环境体检 `mxdeploy init`

部署前先体检，看看这台机器能不能跑模型、缺什么：

```bash
mxdeploy init
```

输出会告诉你：

| 检测项 | 正常情况 | 异常情况 |
|---|---|---|
| mx-smi | 显示 GPU 型号、显存总量 | 未找到 → 没装 MACA 驱动 |
| torch | 显示 `2.8.0+metax`（带 metax 后缀） | 不带 `+metax` → 装错了版本！ |
| vLLM | 显示 `0.17.0+maca` | 不带 `+maca` → 装错了版本！ |
| 系统信息 | CPU / 内存 / 磁盘 | — |

**关键点：`+metax` 和 `+maca` 后缀**。这两个后缀代表"沐曦适配版"。如果 torch 显示 `2.8.0`（没后缀），说明有人用 pip 覆盖了适配版，GPU 会用不了——这时候先跑 `mxdeploy doctor` 看怎么修。

```bash
# 也可以输出 JSON（脚本用）
mxdeploy init --output json
```

---

## 4. 第二步：一键部署 `mxdeploy deploy`

体检没问题，开始部署模型（以 Qwen2.5-3B 为例）：

```bash
mxdeploy deploy Qwen/Qwen2.5-3B-Instruct
```

**一条命令内部自动完成 5 步：**

```
① 精度检查   → 检查模型格式（FP8？FP16？）是否被 C500 支持
② 配置生成   → 根据模型和显存自动生成 vLLM 启动配置
③ 服务拉起   → 启动 vLLM 服务（等待就绪）
④ 健康检查   → 确认服务活着
⑤ 推理验证   → 发一条测试请求，确认真的能回答
```

看到 `✅ 部署成功` 就说明模型已经跑起来了。

**常见情况：**

```bash
# FP8 模型（72B 那种）→ 会被自动拦截
mxdeploy deploy Qwen/Qwen2.5-72B-Instruct-FP8
# 输出：⚠️ 曦云 C500 不支持 FP8，请使用 FP16 或 INT8 版本

# 部署后不想要了
mxdeploy deploy Qwen/Qwen2.5-3B-Instruct --stop
```

> 💡 如果下载模型很慢或超时（huggingface 连不上），先设置镜像：
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> ```

---

## 5. 第三步：性能压测 `mxdeploy bench`

模型部署好了，测测它到底多快：

```bash
mxdeploy bench Qwen/Qwen2.5-3B-Instruct
```

会输出这样一份报告：

```
吞吐 (Throughput)     160.99 tokens/s   ← 每秒生成多少个字，越高越好
首token延迟 (TTFT)    40.85 ms          ← 问完到第一个字出来的时间，越低越跟手
P95 延迟              72.32 ms          ← 95% 的请求都在这时间内，反映稳定性
每token延迟 (TPOT)    6.11 ms           ← 生成每个字的平均耗时
成功率                100%              ← 压测请求的成功比例
显存占用              15361 MB / 16G    ← 部署后占了多少显存
```

**这些指标怎么读？**

| 指标 | 大白话 | 什么时候该关注 |
|---|---|---|
| 吞吐 | 这卡每秒能吐多少字 | 批量任务（离线生成） |
| TTFT | 打字聊天时"卡不卡" | 对话应用（在线交互） |
| P95 | 最慢的 5% 请求有多慢 | 服务稳定性 / SLA |
| TPOT | 每个字的生成速度 | 流式输出的流畅度 |
| 成功率 | 有没有请求挂掉 | 服务健康度 |

**换格式输出：**

```bash
mxdeploy bench Qwen/Qwen2.5-3B-Instruct --output json    # 机器可读
mxdeploy bench Qwen/Qwen2.5-3B-Instruct --output markdown # 存报告
```

实测完整报告见 [BENCHMARK_3B_C500_16G.md](https://github.com/leo1852098393-blip/mxdeploy/blob/master/docs/BENCHMARK_3B_C500_16G.md)。

---

## 6. 第四步：AI 排障 `mxdeploy doctor`

部署或运行出错了？把日志喂给 doctor：

```bash
# 部署日志 / 运行日志都行
mxdeploy doctor deploy.log
```

**内置知识库会自动命中已知坑：**

```
命中规则 NET-001
问题：连接 huggingface.co 超时
原因：国内网络无法直连 HF
修复：export HF_ENDPOINT=https://hf-mirror.com 后重试
```

```
命中规则 ENV-001
问题：vLLM import 崩溃（非交互 SSH 环境）
原因：MACA_PATH 未加载（SSH 不执行 .bashrc）
修复：export MACA_PATH=/opt/maca 后重试
```

**规则没命中？** 可以加 LLM 分析（可选，需配 LLM API）：

```bash
mxdeploy doctor deploy.log --llm-api-key sk-xxx
```

查看全部内置规则：

```bash
mxdeploy doctor --list
```

> 💡 遇到新坑并解决了？欢迎提 Issue 告诉我们，知识库会越来越全（下一步会支持知识库自动沉淀）。

---

## 7. 完整实战：从零到报告（10 分钟版）

```bash
# ① 安装
pip install mxdeploy -i https://pypi.org/simple

# ② 体检（确认 torch 带 +metax，vLLM 带 +maca）
mxdeploy init

# ③ 部署
mxdeploy deploy Qwen/Qwen2.5-3B-Instruct

# ④ 压测出报告
mxdeploy bench Qwen/Qwen2.5-3B-Instruct --output markdown > report.md

# ⑤ 模拟一个错误日志（比如 HF 超时），交给 doctor
echo "raise ConnectionError: Failed to connect to huggingface.co" > deploy.log
mxdeploy doctor deploy.log
```

一套流程走完，你就能回答这三个问题：
1. 环境能不能跑？（init）
2. 模型跑起来没？（deploy）
3. 跑多快、出问题怎么办？（bench + doctor）

---

## 8. 常见问题 FAQ

**Q1：pip install 报错 "No matching distribution"？**
镜像同步延迟，用官方源：`pip install mxdeploy -i https://pypi.org/simple`

**Q2：init 显示 torch 没有 +metax 后缀？**
适配版被覆盖了。检查 `pip list | grep torch`，重新安装沐曦官方适配版（conda 环境 /opt/conda）。

**Q3：部署时报 HF 超时？**
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

**Q4：非交互 SSH 里 vLLM 起不来？**
```bash
export MACA_PATH=/opt/maca
```

**Q5：FP8 模型部署被拦？**
C500 不支持 FP8，换 FP16/INT8 版本模型。

**Q6：OOM 显存不足？**
换小模型 / 用量化版 / 减少并发（后续版本会自动推荐参数）。

**Q7：Windows 上能跑吗？**
CLI 能跑（init/doctor 可体验），deploy/bench 需要 Linux + 曦云真机。

---

## 9. 想参与开发？

```bash
git clone https://github.com/leo1852098393-blip/mxdeploy
cd mxdeploy
pip install -e ".[dev]"
pytest          # 40 个测试全绿
```

- 提 Bug / 建议：GitHub Issues
- 加规则：看 `mxdeploy/knowledge/` 目录，格式照着写就行
- 路线图：[ROADMAP.md](https://github.com/leo1852098393-blip/mxdeploy/blob/master/docs/ROADMAP.md)

---

## 10. 学习路线（接下来学什么）

1. ✅ 今天：跟着教程跑完 7 节，你已经是"会用"级别
2. 📖 想深入：看 `docs/BENCHMARK_3B_C500_16G.md`，理解指标背后的意义
3. 🔧 想动手：跑 `mxdeploy doctor --list` 看知识库，试着给知识库加一条你自己的踩坑规则
4. 🚀 想进阶：关注 v0.2（Provider 架构 + Agent 化），把 mxdeploy 变成 Agent 工具

---

*有问题随时开 Issue，或者直接找我（Leo77）。教程会跟着版本持续更新。*
