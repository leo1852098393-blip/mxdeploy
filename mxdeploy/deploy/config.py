"""模型精度检查与 vLLM 配置生成。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# 曦云 C500 不支持的精度
FP8_MARKERS = ("fp8", "e4m3", "e5m2")

# 模型名 → 推荐配置（参数规模 → 显存占用经验值）
# 16G vGPU 实例下可安全部署的模型规模（FP16/BF16 全精度）
# 经验值：FP16 权重 ≈ 参数量 × 2 bytes
_SAFE_FP16_B = 6  # 16G 实例下 FP16 全精度安全上限（B 参数）


@dataclass
class PrecisionCheck:
    """精度检查结果。"""

    model: str
    detected_precision: str = "unknown"
    is_fp8: bool = False
    is_supported: bool = True
    warnings: list[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class DeployConfig:
    """生成的 vLLM 部署配置。"""

    model: str
    precision: str
    quantization: Optional[str]
    port: int = 8000
    gpu_memory_utilization: float = 0.9
    max_model_len: int = 8192
    tensor_parallel: int = 1
    extra_args: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_command(self, python_bin: str = "python") -> list[str]:
        """生成 vLLM 启动命令。"""
        cmd = [
            python_bin,
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            self.model,
            "--port",
            str(self.port),
            "--gpu-memory-utilization",
            str(self.gpu_memory_utilization),
            "--max-model-len",
            str(self.max_model_len),
            "--tensor-parallel-size",
            str(self.tensor_parallel),
        ]
        if self.quantization:
            cmd += ["--quantization", self.quantization]
        cmd += self.extra_args
        return cmd


def estimate_params(model: str) -> Optional[float]:
    """从模型名估算参数量（B）。如 Qwen2.5-7B-Instruct → 7.0。"""
    m = re.search(r"(\d+(?:\.\d+)?)B", model)
    if m:
        return float(m.group(1))
    return None


def check_precision(model: str) -> PrecisionCheck:
    """检查模型精度是否被曦云 C500 支持。

    C500 不支持 FP8。模型名含 fp8/e4m3/e5m2 或量化后缀时提示。
    """
    result = PrecisionCheck(model=model)
    lowered = model.lower()

    if any(mark in lowered for mark in FP8_MARKERS):
        result.is_fp8 = True
        result.is_supported = False
        result.detected_precision = "fp8"
        result.warnings.append("曦云 C500 不支持 FP8 格式，加载会失败")
        result.suggestion = (
            "请改用 FP16/BF16/INT8 版本模型，例如：\n"
            "  Qwen/Qwen2.5-7B-Instruct (BF16)\n"
            "  Qwen/Qwen2.5-7B-Instruct-GPTQ-Int8 (INT8)"
        )
        return result

    if "int8" in lowered or "int4" in lowered or "awq" in lowered or "gptq" in lowered:
        result.detected_precision = "quantized"
    elif "bf16" in lowered or "fp16" in lowered:
        result.detected_precision = "fp16/bf16"
    else:
        result.detected_precision = "auto (fp16/bf16)"

    return result


def build_config(
    model: str,
    precision: str = "auto",
    port: int = 8000,
    gpu_memory_utilization: float = 0.9,
    max_model_len: int = 8192,
    extra_args: list[str] | None = None,
) -> DeployConfig:
    """根据模型与显存生成部署配置，含显存预检。"""
    pc = check_precision(model)
    warnings = list(pc.warnings)

    config = DeployConfig(
        model=model,
        precision=precision,
        quantization=None,
        port=port,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        extra_args=extra_args or [],
        warnings=warnings,
    )

    params_b = estimate_params(model)

    # 精度参数 → quantization
    if precision == "auto":
        if pc.is_fp8:
            config.quantization = None  # 反正部署会失败，留给用户换模型
        elif "int8" in model.lower():
            config.quantization = "gptq"
        elif "awq" in model.lower():
            config.quantization = "awq"
    elif precision in ("int8", "int4"):
        config.quantization = "gptq"
    else:
        config.quantization = None

    # 显存预检：FP16 全精度下参数规模是否超出实例承载
    if params_b is not None and config.quantization is None and precision != "int8":
        est_gb = params_b * 2  # FP16 权重
        if est_gb > 13.5:  # 16G 实例约 14.4G 可用，留余量
            warnings.append(
                f"模型约 {params_b:.0f}B 参数，FP16 权重约 {est_gb:.0f}GB，"
                f"超出 16G 实例承载（建议 INT8/INT4 量化或换小模型）"
            )
    return config
