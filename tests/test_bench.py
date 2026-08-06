"""bench 模块单元测试（mock 流式响应）。"""

from __future__ import annotations

import json
from unittest import mock

from mxdeploy.bench.benchmark import (
    BenchReport,
    SampleResult,
    _get_gpu_memory_mb,
    run_benchmark,
    stream_chat_completion,
)


def _fake_stream_response(chunks: list[str]):
    """构造模拟的流式响应迭代器。"""
    for c in chunks:
        yield c.encode()


class TestStreamChatCompletion:
    def test_measures_ttft_and_tokens(self):
        chunks = [
            'data: {"choices":[{"delta":{"content":"你"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":"好"}}]}\n\n',
            'data: {"choices":[{"delta":{"content":"！"}}]}\n\n',
            "data: [DONE]\n\n",
        ]
        with mock.patch("urllib.request.urlopen", return_value=mock.Mock(
            __enter__=lambda s: s, __exit__=lambda *a: False,
            __iter__=lambda s: iter(_fake_stream_response(chunks)),
        )):
            ttft, tokens, err = stream_chat_completion(
                "http://x:8000", "test/model", "hi", 100
            )
            assert err == ""
            assert tokens == 3
            assert ttft > 0

    def test_error_path(self):
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("boom")):
            ttft, tokens, err = stream_chat_completion("http://x:8000", "m", "hi", 100)
            assert err != ""
            assert tokens == 0


class TestBenchReport:
    def test_metrics(self):
        report = BenchReport(
            model="m", base_url="http://x", concurrency=2, requests=2, max_tokens=256,
            samples=[
                SampleResult(ttft_ms=100, total_ms=1000, tokens=100),
                SampleResult(ttft_ms=200, total_ms=2000, tokens=200),
            ],
        )
        d = report.to_dict()
        assert d["success_rate"] == 1.0
        assert d["avg_ttft_ms"] == 150.0
        assert d["p95_ttft_ms"] == 200.0
        assert d["total_tokens"] == 300
        assert d["throughput_tokens_s"] > 0
        assert "| 吞吐" in report.to_markdown()

    def test_failed_samples_excluded(self):
        report = BenchReport(
            model="m", base_url="http://x", concurrency=1, requests=2, max_tokens=256,
            samples=[
                SampleResult(ttft_ms=100, total_ms=1000, tokens=100, ok=True),
                SampleResult(ttft_ms=0, total_ms=500, tokens=0, ok=False, error="err"),
            ],
        )
        assert report.success_rate == 0.5
        assert report.total_tokens == 100


class TestRunBenchmark:
    def test_full_flow(self):
        with mock.patch("urllib.request.urlopen") as mock_open, mock.patch(
            "mxdeploy.bench.benchmark._sample_one"
        ) as mock_sample:
            # health check OK
            mock_open.return_value.__enter__.return_value.status = 200
            mock_open.return_value.__enter__.return_value.read.return_value = b'{"data":[{"id":"qwen"}]}'
            mock_sample.return_value = SampleResult(ttft_ms=50, total_ms=500, tokens=64)
            report = run_benchmark("http://127.0.0.1:8000", None, requests=3, concurrency=2, max_tokens=64)
            assert report.model == "qwen"
            assert len(report.samples) == 3
            assert report.success_rate == 1.0

    def test_service_down(self):
        with mock.patch("urllib.request.urlopen", side_effect=ConnectionError("down")):
            try:
                run_benchmark("http://127.0.0.1:9999", None, requests=1, concurrency=1, max_tokens=64)
                assert False, "should raise"
            except RuntimeError as e:
                assert "不可达" in str(e)


class TestGetGpuMemory:
    def test_no_mx_smi(self):
        with mock.patch("shutil.which", return_value=None):
            assert _get_gpu_memory_mb() == 0

    def test_parse_kb(self):
        with mock.patch("shutil.which", return_value="/usr/bin/mx-smi"), mock.patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value.stdout = "vram used: 15703184 KB\n"
            assert _get_gpu_memory_mb() == 15335  # 15703184 // 1024
