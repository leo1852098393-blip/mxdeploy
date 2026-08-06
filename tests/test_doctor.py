"""doctor 排障模块单元测试。"""

from __future__ import annotations

from mxdeploy.knowledge.rules import (
    SEVERITY_CRITICAL,
    diagnose,
    get_by_id,
)


class TestDiagnose:
    def test_maca_path_crash(self):
        log = (
            "Traceback (most recent call last):\n"
            "  File \"/opt/conda/lib/python3.10/site-packages/triton/backends/metax/driver.py\", line 30\n"
            "TypeError: expected str, bytes or os.PathLike object, not NoneType"
        )
        results = diagnose(log)
        ids = [r.entry.id for r in results]
        assert "ENV-001" in ids
        critical = [r for r in results if r.entry.severity == SEVERITY_CRITICAL]
        assert len(critical) >= 1

    def test_hf_timeout(self):
        log = (
            "MaxRetryError(\"HTTPSConnectionPool(host='huggingface.co', port=443): "
            "Max retries exceeded... Connection to huggingface.co timed out.\")"
        )
        results = diagnose(log)
        ids = [r.entry.id for r in results]
        assert "NET-001" in ids

    def test_fp8_error(self):
        results = diagnose("FP8 format not supported on this device")
        assert "PREC-001" in [r.entry.id for r in results]

    def test_pip_override(self):
        results = diagnose("user ran: pip install torch --upgrade")
        assert "DEP-001" in [r.entry.id for r in results]

    def test_oom(self):
        results = diagnose("torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 512 MiB")
        assert "MEM-001" in [r.entry.id for r in results]

    def test_no_match(self):
        results = diagnose("everything looks fine here, no known error patterns")
        assert results == []

    def test_port_conflict(self):
        results = diagnose("OSError: [Errno 98] Address already in use")
        assert "MISC-002" in [r.entry.id for r in results]


class TestGetById:
    def test_known(self):
        assert get_by_id("ENV-001") is not None

    def test_unknown(self):
        assert get_by_id("NOPE") is None
