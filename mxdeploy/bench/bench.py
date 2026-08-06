"""bench 包（占位，M3 实现）。"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run(
    model: str = typer.Argument(..., help="已部署的模型标识"),
    requests: int = typer.Option(100, "--requests", "-n", help="压测请求数"),
) -> None:
    """性能测试：吞吐/延迟/显存（M3 实现）。"""
    console.print(f"[yellow]bench 命令开发中（M3）[/] — 模型: {model}, 请求数: {requests}")
