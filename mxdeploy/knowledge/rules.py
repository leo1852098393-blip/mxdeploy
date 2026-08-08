"""排障知识库：国产 GPU（曦云 C500 / MXMACA）高频问题规则。

每条规则包含：匹配模式、问题定位、修复建议。
素材来源：国产算力平台 16G C500 实例真实踩坑记录（2026-08-06）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


@dataclass
class KnowledgeEntry:
    """一条排障知识。"""

    id: str
    title: str
    patterns: list[str]  # 正则模式，命中任一即触发
    severity: str = SEVERITY_WARNING
    diagnosis: str = ""
    fix: str = ""
    evidence: str = ""

    def match(self, text: str) -> Optional[re.Match]:
        for pat in self.patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m
        return None


@dataclass
class Diagnosis:
    """排障结论。"""

    entry: KnowledgeEntry
    matched_line: str = ""

    @property
    def title(self) -> str:
        return self.entry.title

    def to_dict(self) -> dict:
        return {
            "id": self.entry.id,
            "title": self.entry.title,
            "severity": self.entry.severity,
            "diagnosis": self.entry.diagnosis,
            "fix": self.entry.fix,
            "matched_line": self.matched_line[:200],
        }


# ============================================================
# 知识库：全部来自真实环境实测（国产算力平台曦云 C500）
# ============================================================

KNOWLEDGE_BASE: list[KnowledgeEntry] = [
    # ---- 环境变量类 ----
    KnowledgeEntry(
        id="ENV-001",
        title="MACA_PATH 未设置导致 vllm/triton 导入崩溃",
        severity=SEVERITY_CRITICAL,
        patterns=[
            r"expected str, bytes or os\.PathLike object, not NoneType",
            r"maca_home_dirs\(\).*None",
            r"libmaca_dirs\(\).*None",
            r"MACA_PATH",
        ],
        diagnosis=(
            "vllm/triton 的 metax 后端通过环境变量 MACA_PATH 定位国产 GPU SDK，"
            "该变量未设置时 os.path.join 收到 None 直接崩溃。"
            "常见场景：非交互式 SSH 会话不加载 .bashrc，导致 export 未生效。"
        ),
        fix=(
            "export MACA_PATH=/opt/maca\n"
            "export LD_LIBRARY_PATH=/opt/maca/lib:/opt/maca/ompi/lib:/opt/maca/ucx/lib:/opt/mxdriver/lib:$LD_LIBRARY_PATH\n"
            "export MACA_CLANG_PATH=/opt/maca/mxgpu_llvm/bin\n"
            "# 或直接: source /root/.bashrc （交互式 shell）"
        ),
        evidence="国产算力平台 16G C500 实测：非交互 SSH 执行 import vllm 崩溃于 triton/backends/metax/driver.py:30",
    ),
    # ---- 网络类 ----
    KnowledgeEntry(
        id="NET-001",
        title="HuggingFace 连接超时（国内网络无法直连）",
        severity=SEVERITY_CRITICAL,
        patterns=[
            r"Connection to huggingface\.co timed out",
            r"Max retries exceeded.*huggingface\.co",
            r"ConnectTimeoutError.*huggingface",
            r"Couldn't reach huggingface\.co",
        ],
        diagnosis=(
            "国内实例无法直连 huggingface.co 下载模型，vLLM 加载模型时反复重试后失败。"
        ),
        fix=(
            "export HF_ENDPOINT=https://hf-mirror.com\n"
            "# 或使用 ModelScope 镜像: export VLLM_USE_MODELSCOPE=True"
        ),
        evidence="国产算力平台 16G C500 实测：huggingface.co 超时，设置 HF_ENDPOINT=hf-mirror.com 后正常下载",
    ),
    # ---- 精度类 ----
    KnowledgeEntry(
        id="PREC-001",
        title="FP8 模型不被支持（曦云 C500 不支持 FP8）",
        severity=SEVERITY_CRITICAL,
        patterns=[
            r"fp8.*not supported|not supported.*fp8",
            r"unsupported.*fp8",
            r"e4m3|e5m2",
            r"load.*fail.*fp8|fp8.*load.*fail",
        ],
        diagnosis=(
            "曦云 C500 硬件及软件栈尚未支持 FP8 量化格式，"
            "加载 FP8 模型（如 DeepSeek-V2-FP8、Qwen2-72B-FP8）会失败。"
        ),
        fix=(
            "改用 FP16/BF16/INT8 版本模型：\n"
            "  Qwen/Qwen2.5-7B-Instruct (BF16)\n"
            "  Qwen/Qwen2.5-7B-Instruct-GPTQ-Int8 (INT8)"
        ),
        evidence="官方文档明确：C500 暂不支持 FP8；mxdeploy deploy 已内置 FP8 拦截",
    ),
    # ---- 依赖类 ----
    KnowledgeEntry(
        id="DEP-001",
        title="pip 覆盖了官方适配库（torch 变公版）",
        severity=SEVERITY_CRITICAL,
        patterns=[
            r"pip install torch",
            r"pip (install|upgrade).*torch",
            r"no module named.*torch.*metax",
            r"torch\.cuda\.is_available\(\).*False",
            r"AssertionError.*CUDA|CUDA.*not available",
        ],
        diagnosis=(
            "在国产 GPU 环境执行 pip install/upgrade torch 会从 PyPI 拉取社区公版，"
            "覆盖官方 +metax 适配版，导致无法调用 GPU。"
        ),
        fix=(
            "识别适配版本：pip list | grep -e torch -e metax -e maca（应含 +metax 标记）\n"
            "恢复方法：从官方软件中心重新安装适配版 torch（如 2.8.0+metax3.5.3.9）\n"
            "严禁随意 pip install/upgrade 核心库！"
        ),
        evidence="官方文档『严禁随意更新核心库』；国产算力平台镜像预装 torch 2.8.0+metax",
    ),
    # ---- 显存类 ----
    KnowledgeEntry(
        id="MEM-001",
        title="显存不足 OOM（模型过大或并发过高）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"out of memory|OOM|CUDA out of memory",
            r"insufficient.*memory",
            r"cannot allocate.*memory",
            r"torch\.OutOfMemoryError",
        ],
        diagnosis=(
            "模型权重 + KV cache 超出 GPU 显存配额。"
            "16G vGPU 实例 FP16 全精度约可承载 6B 参数模型。"
        ),
        fix=(
            "1. 降低 --gpu-memory-utilization（默认 0.9）\n"
            "2. 减小 --max-model-len（KV cache 占用随序列长度增长）\n"
            "3. 改用 INT8/INT4 量化模型\n"
            "4. 检查是否误用 FP8 大模型（应先换精度）"
        ),
        evidence="实测：Qwen2.5-3B FP16 占 15361MB/16G；7B FP16 约 14GB 已接近上限",
    ),
    KnowledgeEntry(
        id="MEM-002",
        title="vLLM 启动 OOM（torch.compile autotune 显存不足）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"Failed to run autotuning code block",
            r"CUDA out of memory.*autotun",
            r"InductorError.*out of memory",
            r"Tried to allocate.*GiB",
        ],
        diagnosis=(
            "vLLM 初始化 KV cache 时的 torch.compile autotune 阶段需要额外约 1G 显存，"
            "gpu-memory-utilization=0.9 时模型权重+显存探测已接近 vGPU 配额上限，导致 OOM。"
            "实测：16G vGPU 上 util 0.9 部署 1.5B 失败，util 0.8 成功。"
        ),
        fix=(
            "1. 降低 --gpu-memory-utilization（0.9 → 0.8，16G vGPU 实测安全）\n"
            "2. 设置 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True 减少显存碎片\n"
            "3. 或加 --enforce-eager 跳过 torch.compile（性能略降但更稳）"
        ),
        evidence="国产算力平台 16G vGPU 实测（2026-08-07）：1.5B util 0.9 启动 OOM（Tried to allocate 1.02 GiB, 686 MiB free），util 0.8 成功；7B-INT8 / 3B 同参数验证",
    ),
    KnowledgeEntry(
        id="MISC-003",
        title="模型仓库含自定义代码需 trust-remote-code（如 GLM 系）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"contains custom code which must be executed",
            r"trust_remote_code.*True",
            r"Please pass the argument.*trust_remote_code",
        ],
        diagnosis=(
            "模型仓库（如 GLM 系）带自定义建模代码，transformers/vLLM 需要显式信任执行才能加载。"
        ),
        fix=(
            "vLLM 启动参数加 --trust-remote-code；\n"
            "或设置环境变量 HF_HUB_DISABLE_TRUST_REMOTE_CODE=0"
        ),
        evidence="国产算力平台实测（2026-08-07）：GLM-4-9B-GPTQ-Int4 加载报 ValueError，加 --trust-remote-code 后正常",
    ),
    KnowledgeEntry(
        id="MISC-005",
        title="GPTQ fused 层分片精度不一致（vllm_metax 0.17 compile 模式检查 bug）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"Detected some but not all shards of .* are quantized",
            r"All shards of fused layers to have the same precision",
            r"not all shards.*quantized",
            r"fused layers.*same precision",
        ],
        diagnosis=(
            "GPTQ 量化模型（如 Qwen2.5-14B-GPTQ-Int4）在 torch.compile 模式下加载时，"
            "vllm_metax 0.17.0 的 fused layer 分片精度检查过严，"
            "把部分量化的 gate_up_proj 分片误判为精度不一致。"
            "干净重新下载模型后依然复现，确认非下载损坏，是框架检查 bug。"
        ),
        fix=(
            "启动参数加 --enforce-eager 绕过 compile 模式即可（16G/64G 卡均验证成功）：\n"
            "mxdeploy deploy --model <模型> --enforce-eager\n"
            "注意：eager 模式吞吐与整卡/分片无关（同一物理卡计算力），性能损失主要在长序列场景"
        ),
        evidence="国产算力平台 64G 整卡实测（2026-08-07）：Qwen2.5-14B-GPTQ-Int4 compile 报 ValueError，--enforce-eager 后 46.57 t/s 正常（16G vGPU 46.58 t/s 一致）",
    ),
    KnowledgeEntry(
        id="MISC-004",
        title="量化版模型缺 chat_template（transformers 4.44+ 报错）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"default chat template is no longer allowed",
            r"must provide a chat template",
            r"ChatTemplateResolutionError",
        ],
        diagnosis=(
            "社区量化版模型（如 model-scope 的 GLM-GPTQ-Int4）tokenizer 未定义 chat_template，"
            "transformers 4.44+ 禁止使用默认模板导致 chat 请求失败。"
        ),
        fix=(
            "从官方仓库下载 tokenizer_config.json 覆盖本地模型目录同名文件：\n"
            "huggingface-cli download zai-org/glm-4-9b-chat-hf tokenizer_config.json --local-dir /tmp/glm_tok\n"
            "cp /tmp/glm_tok/tokenizer_config.json <模型目录>/"
        ),
        evidence="国产算力平台实测（2026-08-07）：GLM-4-9B-GPTQ-Int4 bench 全部失败（ChatTemplateResolutionError），覆盖官方 tokenizer_config.json 后 100% 成功",
    ),
    KnowledgeEntry(
        id="MEM-003",
        title="KV cache 不足（大模型 max_model_len 过长）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"KV cache is needed.*larger than the available",
            r"estimated maximum model length",
            r"_check_enough_kv_cache_memory",
        ],
        diagnosis=(
            "模型权重占用大部分显存后，剩余显存不足以支撑 max_model_len 对应的 KV cache。"
            "实测：14B-INT4 权重约 11G，KV cache 仅剩 1.08G（需 1.5G@8192）。"
        ),
        fix=(
            "1. 降低 --max-model-len（8192 → 4096，实测 14B-INT4 可行）\n"
            "2. 或降低 --gpu-memory-utilization 反而更糟（留给 KV 的空间更少）→ 应适度提高或改小模型\n"
            "3. 或换量化程度更高的模型（INT4 → INT2/GGUF）"
        ),
        evidence="国产算力平台实测（2026-08-07）：14B-INT4 @ max_len 8192 报 KV cache 不足，降至 4096 成功部署",
    ),
    # ---- 其他 ----
    KnowledgeEntry(
        id="MISC-001",
        title="模型架构未适配（新模型等待 MACA 软件栈更新）",
        severity=SEVERITY_WARNING,
        patterns=[
            r"model architecture.*not registered",
            r"unsupported model architecture",
            r"architecture.*not supported",
        ],
        diagnosis=(
            "刚发布的全新架构模型可能尚未被 MACA 软件栈适配，"
            "vllm_metax 无法识别其架构。"
        ),
        fix=(
            "1. 查询官方模型支持列表确认适配状态\n"
            "2. 升级 MACA/vllm_metax 到最新版\n"
            "3. 临时换用同参数量的已知适配架构模型（如 Qwen2.5 系列）"
        ),
        evidence="国产算力平台文档：新模型适配可能需要等待官方 MACA 软件栈更新",
    ),
    KnowledgeEntry(
        id="MISC-002",
        title="vLLM 端口占用或服务启动冲突",
        severity=SEVERITY_WARNING,
        patterns=[
            r"address already in use",
            r"port.*already in use|bind.*failed.*address",
            r"\[Errno 98\]",
        ],
        diagnosis="目标端口已被其他进程占用（可能上一次部署未清理）。",
        fix=(
            "1. 查占用：ss -tlnp | grep <port>\n"
            "2. 杀旧进程：pkill -f vllm.entrypoints\n"
            "3. 或换端口：mxdeploy deploy --port 8001"
        ),
        evidence="国产算力平台实测：重复部署时旧进程未清理导致端口冲突",
    ),
]


def diagnose(text: str) -> list[Diagnosis]:
    """对日志/文本执行规则匹配，返回命中的诊断列表。"""
    results = []
    for entry in KNOWLEDGE_BASE:
        m = entry.match(text)
        if m:
            # 提取命中行上下文
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            context = text[start:end].replace("\n", " ")
            results.append(Diagnosis(entry=entry, matched_line=context))
    return results


def get_by_id(entry_id: str) -> Optional[KnowledgeEntry]:
    for entry in KNOWLEDGE_BASE:
        if entry.id == entry_id:
            return entry
    return None
