"""mxdeploy deploy — 一键部署命令。"""

from __future__ import annotations

import typer
from rich.console import Console

from mxdeploy.deploy.runner import deploy

console = Console()


def run(
    model: str = typer.Argument(..., help="模型名称或 HuggingFace 路径，如 Qwen/Qwen2.5-7B-Instruct"),
    precision: str = typer.Option("auto", "--precision", "-p", help="精度: auto / fp16 / bf16 / int8 / int4"),
    port: int = typer.Option(8000, "--port", help="服务端口"),
    gpu_memory_utilization: float = typer.Option(0.9, "--gpu-memory-utilization", "-g", help="GPU 显存利用率 (0~1)"),
    max_model_len: int = typer.Option(8192, "--max-model-len", "-m", help="最大序列长度"),
    no_launch: bool = typer.Option(False, "--no-launch", help="只生成配置不启动（CI/预览）"),
    timeout: int = typer.Option(600, "--timeout", help="健康检查超时（秒）"),
    python_bin: str = typer.Option(None, "--python-bin", help="指定 python 解释器（默认用当前环境）"),
) -> None:
    """一键部署模型到国产 GPU：精度检查 → vLLM 配置生成 → 服务拉起 → 健康检查。"""
    extra = None
    result = deploy(
        model=model,
        precision=precision,
        port=port,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        no_launch=no_launch,
        timeout=timeout,
        python_bin=python_bin,
        extra_args=extra,
    )
    if not result.success:
        raise typer.Exit(1)
