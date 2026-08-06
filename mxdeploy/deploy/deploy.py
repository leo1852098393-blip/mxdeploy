"""deploy 包（占位，M2 实现）。"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run(
    model: str = typer.Argument(..., help="模型名称或 HuggingFace 路径，如 Qwen/Qwen2.5-7B-Instruct"),
    precision: str = typer.Option("auto", "--precision", "-p", help="精度: auto / fp16 / bf16 / int8 / int4"),
) -> None:
    """一键部署模型到国产 GPU（M2 实现）。"""
    console.print(f"[yellow]deploy 命令开发中（M2）[/] — 目标模型: {model}, 精度: {precision}")
