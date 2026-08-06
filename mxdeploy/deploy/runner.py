"""部署执行：拉起 vLLM 服务并做健康检查。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console

console = Console()


@dataclass
class DeployResult:
    """部署结果。"""

    success: bool
    model: str
    port: int
    pid: Optional[int] = None
    logfile: Optional[str] = None
    health: Optional[dict] = None
    message: str = ""


class VLLMDeployer:
    """vLLM 服务部署器。"""

    def __init__(
        self,
        cmd: list[str],
        port: int,
        logfile: str = "/tmp/mxdeploy_vllm.log",
        health_timeout: int = 600,
        health_interval: int = 5,
    ):
        self.cmd = cmd
        self.port = port
        self.logfile = logfile
        self.health_timeout = health_timeout
        self.health_interval = health_interval
        self.proc: Optional[subprocess.Popen] = None

    def _health_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/health"

    def _models_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1/models"

    def start(self) -> None:
        """后台启动 vLLM 服务。"""
        logf = open(self.logfile, "w")
        self.proc = subprocess.Popen(
            self.cmd,
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=os.environ.copy(),
        )
        console.print(f"[cyan]✓ 服务已启动[/] PID={self.proc.pid}，日志: {self.logfile}")

    def wait_healthy(self) -> dict:
        """轮询 /health 直到就绪，返回模型列表信息。"""
        deadline = time.time() + self.health_timeout
        while time.time() < deadline:
            if self.proc and self.proc.poll() is not None:
                # 进程提前退出 = 启动失败
                tail = self._tail_log(30)
                raise RuntimeError(
                    f"vLLM 进程异常退出 (rc={self.proc.returncode})\n"
                    f"日志尾部:\n{tail}"
                )
            try:
                with urllib.request.urlopen(self._health_url(), timeout=5) as resp:
                    if resp.status == 200:
                        body = resp.read().decode()
                        return {"health": body.strip()}
            except Exception:
                pass
            time.sleep(self.health_interval)
        tail = self._tail_log(30)
        raise TimeoutError(
            f"等待服务就绪超时（{self.health_timeout}s），日志尾部:\n{tail}"
        )

    def fetch_models(self) -> list[dict]:
        """查询已加载模型列表。"""
        try:
            with urllib.request.urlopen(self._models_url(), timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return data.get("data", [])
        except Exception as e:
            return [{"error": str(e)}]

    def _tail_log(self, n: int = 30) -> str:
        try:
            with open(self.logfile, "r", errors="replace") as f:
                lines = f.readlines()
            return "".join(lines[-n:])
        except Exception:
            return "(无法读取日志)"


def deploy(
    model: str,
    precision: str,
    port: int,
    gpu_memory_utilization: float,
    max_model_len: int,
    no_launch: bool,
    timeout: int,
    python_bin: Optional[str] = None,
    extra_args: list[str] | None = None,
) -> DeployResult:
    """执行部署流程：预检 → 生成配置 → 启动 → 健康检查。"""
    from mxdeploy.deploy.config import build_config

    console.print(f"[bold]部署模型:[/] {model}")
    config = build_config(
        model=model,
        precision=precision,
        port=port,
        gpu_memory_utilization=gpu_memory_utilization,
        max_model_len=max_model_len,
        extra_args=extra_args,
    )

    # 打印预检警告
    if config.warnings:
        for w in config.warnings:
            console.print(f"[yellow]⚠ {w}[/]")

    pc = config.warnings and any("FP8" in w for w in config.warnings)
    if pc:
        console.print("[bold red]✗ 模型精度不被支持，部署中止[/]")
        return DeployResult(success=False, model=model, port=port, message="FP8 模型不受支持")

    # 打印将要执行的命令
    if python_bin is None:
        python_bin = sys.executable
    cmd = config.to_command(python_bin=python_bin)
    console.print("[bold cyan]启动命令:[/]")
    console.print("  " + " ".join(cmd))

    if no_launch:
        console.print("[yellow]--no-launch 模式，仅生成配置，不实际启动[/]")
        return DeployResult(
            success=True, model=model, port=port, message="配置已生成（未启动）"
        )

    deployer = VLLMDeployer(cmd=cmd, port=port, health_timeout=timeout)
    deployer.start()
    try:
        health = deployer.wait_healthy()
    except (RuntimeError, TimeoutError) as e:
        console.print(f"[bold red]✗ 部署失败[/]\n{e}")
        return DeployResult(
            success=False, model=model, port=port, logfile=deployer.logfile, message=str(e)
        )

    models = deployer.fetch_models()
    console.print(f"[bold green]✓ 服务就绪[/] http://127.0.0.1:{port}")
    if models and "error" not in models[0]:
        for m in models:
            console.print(f"  [cyan]模型:[/] {m.get('id', '?')}")
    else:
        console.print(f"  [yellow]模型列表:[/] {models}")

    return DeployResult(
        success=True,
        model=model,
        port=port,
        pid=deployer.proc.pid if deployer.proc else None,
        logfile=deployer.logfile,
        health=health,
        message="部署成功",
    )
