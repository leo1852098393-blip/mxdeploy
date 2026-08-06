"""mxdeploy init — 环境体检命令。"""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

from mxdeploy.envcheck.detector import STATUS_ERROR, STATUS_WARN, EnvReport, run_all

console = Console()

_STATUS_STYLE = {
    "ok": "green",
    "warn": "yellow",
    "error": "red",
}


def run(
    format: str = typer.Option("table", "--format", help="输出格式: table / json"),
    exit_code: bool = typer.Option(False, "--exit-code", help="存在 error 项时以非零码退出（便于 CI）"),
) -> None:
    """环境体检：检测 mx-smi / torch / vLLM / 系统信息。"""
    report = run_all()

    if format == "json":
        console.print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    else:
        _render_table(report)

    # 汇总判定
    errors = [c for c in report.checks if c.status == STATUS_ERROR]
    warns = [c for c in report.checks if c.status == STATUS_WARN]
    if errors:
        console.print(f"\n[bold red]✗ {len(errors)} 项异常[/] — 环境不可用，先处理后再继续")
    elif warns:
        console.print(f"\n[bold yellow]! {len(warns)} 项警告[/] — 可以继续，但建议核对")
    else:
        console.print("\n[bold green]✓ 环境正常[/] — 可以开始部署")

    if exit_code and errors:
        raise typer.Exit(1)


def _render_table(report: EnvReport) -> None:
    table = Table(title="mxdeploy 环境体检报告")
    table.add_column("检查项", style="cyan", no_wrap=True)
    table.add_column("状态", no_wrap=True)
    table.add_column("详情")
    table.add_column("提示")

    for c in report.checks:
        style = _STATUS_STYLE.get(c.status, "white")
        icon = {"ok": "✓", "warn": "!", "error": "✗"}.get(c.status, "?")
        table.add_row(c.name, f"[{style}]{icon} {c.status.upper()}[/]", c.detail, c.hint or "-")

    console.print(table)
