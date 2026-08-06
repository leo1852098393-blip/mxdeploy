"""mxdeploy bench — 性能测试命令。"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mxdeploy.bench.benchmark import run_benchmark

console = Console()


def run(
    base_url: str = typer.Option("http://127.0.0.1:8000", "--base-url", "-u", help="已部署服务地址"),
    model: str = typer.Option(None, "--model", "-m", help="模型名（默认自动探测）"),
    requests: int = typer.Option(50, "--requests", "-n", help="请求数"),
    concurrency: int = typer.Option(8, "--concurrency", "-c", help="并发数"),
    max_tokens: int = typer.Option(256, "--max-tokens", help="每次生成最大 token 数"),
    format: str = typer.Option("table", "--format", help="输出格式: table / json / markdown"),
    output: str = typer.Option(None, "--output", "-o", help="报告保存路径（.json / .md）"),
) -> None:
    """性能测试：对已部署的服务做压测，输出吞吐/延迟/显存报告。"""
    try:
        report = run_benchmark(
            base_url=base_url,
            model=model,
            requests=requests,
            concurrency=concurrency,
            max_tokens=max_tokens,
        )
    except RuntimeError as e:
        console.print(f"[bold red]✗ {e}[/]")
        raise typer.Exit(1)

    if format == "json":
        console.print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif format == "markdown":
        console.print(report.to_markdown())
    else:
        _render_table(report)

    # 保存报告
    if output:
        path = Path(output)
        if path.suffix == ".json":
            path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            path.write_text(report.to_markdown(), encoding="utf-8")
        console.print(f"[green]✓ 报告已保存: {path}[/]")


def _render_table(report) -> None:
    d = report.to_dict()
    table = Table(title=f"Benchmark — {d['model']}")
    table.add_column("指标", style="cyan")
    table.add_column("值", justify="right")
    rows = [
        ("成功率", f"{d['success_rate'] * 100:.1f}%"),
        ("吞吐 (tokens/s)", f"{d['throughput_tokens_s']}"),
        ("首 token 延迟均值 (ms)", f"{d['avg_ttft_ms']}"),
        ("首 token 延迟 P95 (ms)", f"{d['p95_ttft_ms']}"),
        ("每 token 延迟均值 (ms)", f"{d['avg_tpot_ms']}"),
        ("总生成 tokens", f"{d['total_tokens']}"),
        ("GPU 显存占用 (MB)", f"{d['gpu_memory_mb']}"),
    ]
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)
