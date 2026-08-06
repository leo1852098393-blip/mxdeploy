"""doctor 包（占位，M4 实现）。"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run(
    logfile: str = typer.Argument(None, help="日志文件路径；不填则从 stdin 读取"),
) -> None:
    """AI 排障：分析部署/运行日志，定位根因（M4 实现）。"""
    console.print(f"[yellow]doctor 命令开发中（M4）[/] — 日志: {logfile or '(stdin)'}")
