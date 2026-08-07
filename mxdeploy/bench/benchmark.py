"""性能压测：吞吐 / 延迟 / 显存采集。"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SampleResult:
    """单次请求测量结果。"""

    ttft_ms: float  # 首 token 延迟
    total_ms: float  # 总耗时
    tokens: int  # 生成 token 数
    ok: bool = True
    error: str = ""


@dataclass
class BenchReport:
    """压测报告。"""

    model: str
    base_url: str
    concurrency: int
    requests: int
    max_tokens: int
    samples: list[SampleResult] = field(default_factory=list)
    gpu_memory_mb: int = 0

    # ---- 汇总指标 ----
    @property
    def ok_samples(self) -> list[SampleResult]:
        return [s for s in self.samples if s.ok]

    @property
    def success_rate(self) -> float:
        if not self.samples:
            return 0.0
        return len(self.ok_samples) / len(self.samples)

    @property
    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.ok_samples)

    @property
    def total_time_s(self) -> float:
        return sum(s.total_ms for s in self.ok_samples) / 1000.0

    @property
    def throughput_tokens_s(self) -> float:
        """整体吞吐（所有并发请求累计 tokens / 总耗时）。"""
        if self.total_time_s <= 0:
            return 0.0
        return self.total_tokens / self.total_time_s

    @property
    def avg_ttft_ms(self) -> float:
        if not self.ok_samples:
            return 0.0
        return sum(s.ttft_ms for s in self.ok_samples) / len(self.ok_samples)

    @property
    def avg_tpot_ms(self) -> float:
        """平均每 token 延迟（不含首 token）。"""
        samples = [s for s in self.ok_samples if s.tokens > 1]
        if not samples:
            return 0.0
        return sum((s.total_ms - s.ttft_ms) / max(1, s.tokens - 1) for s in samples) / len(samples)

    @property
    def p95_ttft_ms(self) -> float:
        return self._percentile([s.ttft_ms for s in self.ok_samples], 0.95)

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        idx = min(len(ordered) - 1, int(len(ordered) * p))
        return ordered[idx]

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "base_url": self.base_url,
            "concurrency": self.concurrency,
            "requests": self.requests,
            "max_tokens": self.max_tokens,
            "success_rate": round(self.success_rate, 4),
            "throughput_tokens_s": round(self.throughput_tokens_s, 2),
            "avg_ttft_ms": round(self.avg_ttft_ms, 2),
            "p95_ttft_ms": round(self.p95_ttft_ms, 2),
            "avg_tpot_ms": round(self.avg_tpot_ms, 2),
            "total_tokens": self.total_tokens,
            "gpu_memory_mb": self.gpu_memory_mb,
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = [
            "## Benchmark 报告",
            "",
            f"- **模型**: {d['model']}",
            f"- **并发**: {d['concurrency']} / **请求数**: {d['requests']} / **max_tokens**: {d['max_tokens']}",
            f"- **成功率**: {d['success_rate'] * 100:.1f}%",
            "",
            "| 指标 | 值 |",
            "|------|-----|",
            f"| 吞吐 (tokens/s) | {d['throughput_tokens_s']} |",
            f"| 首 token 延迟均值 (ms) | {d['avg_ttft_ms']} |",
            f"| 首 token 延迟 P95 (ms) | {d['p95_ttft_ms']} |",
            f"| 每 token 延迟均值 (ms) | {d['avg_tpot_ms']} |",
            f"| 总生成 tokens | {d['total_tokens']} |",
            f"| GPU 显存占用 (MB) | {d['gpu_memory_mb']} |",
            "",
        ]
        return "\n".join(lines)


def stream_completions(
    base_url: str, model: str, prompt: str, max_tokens: int, timeout: float = 120
) -> tuple[float, int, str]:
    """非 chat 接口流式调用 /v1/completions（chat 接口不可用时的 fallback）。"""
    url = f"{base_url}/v1/completions"
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "stream": True,
        }
    ).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    ttft = 0.0
    tokens = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    choices = chunk.get("choices", [{}])
                    if not choices:
                        continue
                    delta = choices[0].get("text", "") or ""
                    if delta:
                        if ttft == 0:
                            ttft = (time.perf_counter() - start) * 1000
                        tokens += len(delta)
                except Exception:
                    continue
        total = (time.perf_counter() - start) * 1000
        return (ttft, tokens, "")
    except Exception as e:
        return (0.0, 0, str(e))


def stream_chat_completion(
    base_url: str, model: str, prompt: str, max_tokens: int, timeout: float = 120
) -> tuple[float, int, str]:
    """流式调用 chat/completions，返回 (ttft_ms, tokens, error)。

    chat 接口失败（如模型缺 chat_template）时自动 fallback 到 completions 接口。
    """
    url = f"{base_url}/v1/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": True,
        }
    ).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    ttft = 0.0
    tokens = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        if ttft == 0:
                            ttft = (time.perf_counter() - start) * 1000
                        tokens += len(content)
                except Exception:
                    continue
        total = (time.perf_counter() - start) * 1000
        return (ttft, tokens, "")
    except Exception as e:
        # chat 接口失败 → fallback 到 completions 接口
        return stream_completions(base_url, model, prompt, max_tokens, timeout)


def _sample_one(base_url: str, model: str, max_tokens: int) -> SampleResult:
    start = time.perf_counter()
    ttft, tokens, err = stream_chat_completion(base_url, model, "请用中文写一段关于人工智能的简短介绍。", max_tokens)
    total = (time.perf_counter() - start) * 1000
    if err:
        return SampleResult(ttft_ms=0, total_ms=total, tokens=0, ok=False, error=err)
    return SampleResult(ttft_ms=ttft, total_ms=total, tokens=tokens)


def _get_gpu_memory_mb() -> int:
    """通过 mx-smi 获取当前显存使用（MB）。"""
    if shutil.which("mx-smi") is None:
        return 0
    try:
        proc = subprocess.run(
            ["mx-smi", "--show-memory"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in (proc.stdout or "").splitlines():
            if "vram used" in line and "KB" in line:
                for tok in line.split():
                    if tok.isdigit():
                        return int(tok) // 1024
    except Exception:
        pass
    return 0


def run_benchmark(
    base_url: str,
    model: Optional[str],
    requests: int,
    concurrency: int,
    max_tokens: int,
) -> BenchReport:
    """执行压测。"""
    if model is None:
        # 自动探测已部署模型
        try:
            with urllib.request.urlopen(f"{base_url}/v1/models", timeout=10) as resp:
                data = json.loads(resp.read().decode())
                model = data["data"][0]["id"]
        except Exception:
            model = "unknown"

    report = BenchReport(
        model=model, base_url=base_url, concurrency=concurrency,
        requests=requests, max_tokens=max_tokens,
    )

    # 先确认服务在线
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"health check failed: {resp.status}")
    except Exception as e:
        raise RuntimeError(f"服务不可达 {base_url}: {e}")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(_sample_one, base_url, model, max_tokens)
            for _ in range(requests)
        ]
        for fut in as_completed(futures):
            report.samples.append(fut.result())

    report.gpu_memory_mb = _get_gpu_memory_mb()
    return report
