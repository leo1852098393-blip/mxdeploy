"""排障知识库：国产 GPU（曦云 C500 / MXMACA）高频问题规则。

每条规则包含：匹配模式、问题定位、修复建议。
素材来源：模力方舟 16G C500 实例真实踩坑记录（2026-08-06）。
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
# 知识库：全部来自真实环境实测（模力方舟曦云 C500）
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
            "vllm/triton 的 metax 后端通过环境变量 MACA_PATH 定位沐曦 SDK，"
            "该变量未设置时 os.path.join 收到 None 直接崩溃。"
            "常见场景：非交互式 SSH 会话不加载 .bashrc，导致 export 未生效。"
        ),
        fix=(
            "export MACA_PATH=/opt/maca\n"
            "export LD_LIBRARY_PATH=/opt/maca/lib:/opt/maca/ompi/lib:/opt/maca/ucx/lib:/opt/mxdriver/lib:$LD_LIBRARY_PATH\n"
            "export MACA_CLANG_PATH=/opt/maca/mxgpu_llvm/bin\n"
            "# 或直接: source /root/.bashrc （交互式 shell）"
        ),
        evidence="模力方舟 16G C500 实测：非交互 SSH 执行 import vllm 崩溃于 triton/backends/metax/driver.py:30",
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
        evidence="模力方舟 16G C500 实测：huggingface.co 超时，设置 HF_ENDPOINT=hf-mirror.com 后正常下载",
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
        evidence="沐曦官方文档明确：C500 暂不支持 FP8；mxdeploy deploy 已内置 FP8 拦截",
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
            "在沐曦环境执行 pip install/upgrade torch 会从 PyPI 拉取社区公版，"
            "覆盖官方 +metax 适配版，导致无法调用 GPU。"
        ),
        fix=(
            "识别适配版本：pip list | grep -e torch -e metax -e maca（应含 +metax 标记）\n"
            "恢复方法：从沐曦官方软件中心重新安装适配版 torch（如 2.8.0+metax3.5.3.9）\n"
            "严禁随意 pip install/upgrade 核心库！"
        ),
        evidence="沐曦官方文档『严禁随意更新核心库』；模力方舟镜像预装 torch 2.8.0+metax",
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
            "1. 查询沐曦官方模型支持列表确认适配状态\n"
            "2. 升级 MACA/vllm_metax 到最新版\n"
            "3. 临时换用同参数量的已知适配架构模型（如 Qwen2.5 系列）"
        ),
        evidence="模力方舟文档：新模型适配可能需要等待官方 MACA 软件栈更新",
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
        evidence="模力方舟实测：重复部署时旧进程未清理导致端口冲突",
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
