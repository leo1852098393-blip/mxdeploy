"""环境检测器：mx-smi / Python / torch / vLLM / 系统信息。"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

# 国产 GPU 适配版依赖标识（版本号中应包含 +metax 或 +maca）
METAX_MARKERS = ("+metax", "+maca")

# 环境检查项状态
STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_ERROR = "error"


@dataclass
class CheckResult:
    """单项检查结果。"""

    name: str
    status: str
    detail: str = ""
    hint: str = ""


@dataclass
class EnvReport:
    """完整环境体检报告。"""

    gpu_model: str = "未知"
    gpu_count: int = 0
    gpu_memory_mb: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_gpu(self) -> bool:
        return self.gpu_count > 0

    @property
    def is_metax_env(self) -> bool:
        return "C500" in self.gpu_model or "曦云" in self.gpu_model or "MetaX" in self.gpu_model

    def summary(self) -> dict:
        return {
            "gpu_model": self.gpu_model,
            "gpu_count": self.gpu_count,
            "gpu_memory_mb": self.gpu_memory_mb,
            "has_gpu": self.has_gpu,
            "is_metax_env": self.is_metax_env,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail, "hint": c.hint}
                for c in self.checks
            ],
        }


def _run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    """运行命令并返回 (returncode, stdout+stderr)。"""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"command timed out: {cmd[0]}"


def _get_torch_visible_memory_mb() -> Optional[int]:
    """获取 PyTorch 实际可见显存（MB）。

    mx-smi 显示的是物理卡显存（如 C500 为 64G），但 vGPU 实例的实际配额
    以 PyTorch 可见显存为准（如 16G vGPU 实例 PyTorch 可见 15.22 GiB）。
    """
    try:
        import torch

        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return props.total_memory // (1024 * 1024)
    except Exception:
        pass
    return None


def check_mx_smi() -> tuple[str, int, int, str]:
    """检测 mx-smi：返回 (gpu_model, gpu_count, memory_mb, detail)。"""
    if shutil.which("mx-smi") is None:
        return "未知", 0, 0, "mx-smi 未找到（非国产 GPU 环境或驱动未安装）"
    code, out = _run_cmd(["mx-smi", "--show-usage"])
    if code != 0:
        return "未知", 0, 0, f"mx-smi 执行失败 (rc={code}): {out[:200]}"
    # 解析 GPU 型号与数量
    model = "MetaX GPU"
    count = 0
    for line in out.splitlines():
        if "C500" in line or "MXC500" in line or "曦云" in line:
            if "MetaX" in line or "C500" in line or "MXC500" in line:
                model = "曦云 C500"
            count += 1
    if count == 0:
        count = max(1, len([l for l in out.splitlines() if "GPU" in l and "%" in l]))
    # 显存：优先用 PyTorch 可见显存（vGPU 实例实际配额），失败则解析 mx-smi --show-memory
    memory_mb = _get_torch_visible_memory_mb() or 0
    if memory_mb == 0:
        _, mem_out = _run_cmd(["mx-smi", "--show-memory"])
        for line in mem_out.splitlines():
            if "vram total" in line and "KB" in line:
                for tok in line.split():
                    if tok.isdigit():
                        memory_mb = max(memory_mb, int(tok) // 1024)
    return model, count, memory_mb, f"mx-smi OK (detected {count} GPU)"



def check_python() -> CheckResult:
    v = sys.version_info
    detail = f"Python {v.major}.{v.minor}.{v.micro} ({platform.python_implementation()})"
    if (v.major, v.minor) >= (3, 10):
        return CheckResult("python", STATUS_OK, detail)
    return CheckResult("python", STATUS_ERROR, detail, "需要 Python 3.10+")


def check_torch() -> CheckResult:
    try:
        import torch

        ver = torch.__version__
        detail = f"torch {ver}"
        # 国产 GPU 环境必须带 +metax 标记
        if any(m in ver for m in METAX_MARKERS):
            return CheckResult("torch", STATUS_OK, detail, "国产适配版")
        # torch 装了但没 metax 标记 → 可能是公版覆盖了官方适配
        if torch.cuda.is_available() and "meta" in str(torch.cuda.get_device_name(0)).lower():
            return CheckResult("torch", STATUS_WARN, detail, "检测到国产设备但版本无 +metax 标记，请确认是否为官方适配版")
        return CheckResult(
            "torch", STATUS_WARN, detail,
            "未检测到 +metax/+maca 标记，若在国产 GPU 环境请使用官方适配版（pip install torch 会覆盖！）",
        )
    except ImportError:
        return CheckResult(
            "torch", STATUS_WARN, "torch 未安装",
            "部署需要国产 GPU 适配版 PyTorch（版本含 +metax）",
        )


def check_vllm() -> CheckResult:
    # 国产 GPU 适配包是 vllm_metax（主 vllm 包版本号不带 +maca 标记）
    try:
        import importlib.util

        if importlib.util.find_spec("vllm_metax") is not None:
            return CheckResult("vllm", STATUS_OK, "vllm_metax 已安装（国产适配版）", "MACA-vLLM 适配包")
    except Exception:
        pass
    try:
        import vllm

        ver = getattr(vllm, "__version__", "unknown")
        detail = f"vllm {ver}"
        if any(m in ver for m in METAX_MARKERS):
            return CheckResult("vllm", STATUS_OK, detail, "国产适配版")
        return CheckResult(
            "vllm", STATUS_WARN, detail,
            "未检测到 vllm_metax/+maca，若在国产 GPU 环境请安装适配版",
        )
    except ImportError:
        # vllm 导入失败：优先提示 MACA_PATH 环境变量问题（国产 GPU 高频坑）
        import os

        if os.getenv("MACA_PATH") is None:
            return CheckResult(
                "vllm", STATUS_ERROR, "vllm 导入失败且 MACA_PATH 未设置",
                "export MACA_PATH=/opt/maca（triton metax 后端依赖此变量）",
            )
        return CheckResult(
            "vllm", STATUS_WARN, "vllm 未安装或导入失败",
            "部署大模型需要 MACA-vLLM（vllm_metax）",
        )


def check_system() -> CheckResult:
    detail = f"{platform.system()} {platform.release()} ({platform.machine()})"
    mem_mb = 0
    try:
        import psutil

        mem_mb = psutil.virtual_memory().total // (1024 * 1024)
        detail += f" | RAM {mem_mb} MB"
    except ImportError:
        pass
    return CheckResult("system", STATUS_OK, detail)


def run_all() -> EnvReport:
    """执行全部环境检查，返回报告。"""
    report = EnvReport()
    model, count, mem_mb, mx_detail = check_mx_smi()
    report.gpu_model = model
    report.gpu_count = count
    report.gpu_memory_mb = mem_mb

    if count == 0:
        report.checks.append(CheckResult("mx-smi", STATUS_ERROR, mx_detail, "未检测到国产 GPU，检查驱动或确认运行在国产算力实例上"))
    else:
        report.checks.append(CheckResult("mx-smi", STATUS_OK, mx_detail))
        report.checks.append(CheckResult("gpu", STATUS_OK, f"{model} × {count}, 显存上限 {mem_mb or '未知'} MB"))

    report.checks.append(check_python())
    report.checks.append(check_torch())
    report.checks.append(check_vllm())
    report.checks.append(check_system())
    return report
