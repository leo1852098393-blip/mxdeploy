"""mxdeploy — 国产 GPU 一键部署助手 CLI 入口。"""

import sys

# Windows 终端默认 GBK，强制 UTF-8 避免 rich 输出符号报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from rich.console import Console

from mxdeploy.envcheck import envcheck
from mxdeploy.deploy import deploy
from mxdeploy.bench import bench
from mxdeploy.doctor import doctor

app = typer.Typer(
    name="mxdeploy",
    help="国产 GPU (MetaX 曦云 C500 / MXMACA) 一键部署 + 评测 + AI 排障工具",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

app.command(name="init")(envcheck.run)
app.command(name="deploy")(deploy.run)
app.command(name="bench")(bench.run)
app.command(name="doctor")(doctor.run)


@app.command("version")
def version() -> None:
    """显示版本信息。"""
    from importlib.metadata import version as pkg_version

    try:
        v = pkg_version("mxdeploy")
    except Exception:
        v = "0.1.0 (dev)"
    console.print(f"[bold cyan]mxdeploy[/] v{v} — 国产 GPU 一键部署助手")


if __name__ == "__main__":
    app()
