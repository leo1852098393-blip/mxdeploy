"""mxdeploy doctor — AI 排障命令。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mxdeploy.knowledge.rules import SEVERITY_CRITICAL, SEVERITY_WARNING, diagnose

console = Console()

_SEVERITY_STYLE = {
    SEVERITY_CRITICAL: "red",
    SEVERITY_WARNING: "yellow",
    "info": "cyan",
}


def run(
    logfile: str = typer.Argument(None, help="日志文件路径；不填则从 stdin 读取"),
    format: str = typer.Option("table", "--format", help="输出格式: table / json"),
) -> None:
    """AI 排障：分析部署/运行日志，基于知识库定位根因并给出修复建议。"""
    # 读取日志
    if logfile:
        path = Path(logfile)
        if not path.exists():
            console.print(f"[bold red]✗ 文件不存在: {logfile}[/]")
            raise typer.Exit(1)
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()

    if not text.strip():
        console.print("[yellow]! 日志为空[/]")
        return

    results = diagnose(text)

    if format == "json":
        console.print(json.dumps(
            [r.to_dict() for r in results], ensure_ascii=False, indent=2
        ))
        return

    if not results:
        console.print("[bold green]✓ 未命中已知问题[/] — 尝试用 --format json 查看更多信息，或提供更多日志")
        return

    console.print(f"[bold]命中 {len(results)} 条已知问题:[/]")
    for i, r in enumerate(results, 1):
        style = _SEVERITY_STYLE.get(r.entry.severity, "white")
        icon = {"critical": "✗", "warning": "!", "info": "ℹ"}.get(r.entry.severity, "?")
        console.print(f"\n[{style}]{icon} [{i}] {r.title}[/]  [dim]({r.entry.id})[/]")
        if r.entry.diagnosis:
            console.print(f"  [bold]诊断:[/] {r.entry.diagnosis}")
        if r.entry.fix:
            console.print(f"  [bold green]修复:[/]")
            for line in r.entry.fix.splitlines():
                console.print(f"    [green]{line}[/]")
        if r.matched_line:
            console.print(f"  [dim]命中上下文: ...{r.matched_line}...[/]")

    critical = [r for r in results if r.entry.severity == SEVERITY_CRITICAL]
    if critical:
        console.print(f"\n[bold red]✗ 存在 {len(critical)} 条严重问题，需处理后继续[/]")
        raise typer.Exit(1)
