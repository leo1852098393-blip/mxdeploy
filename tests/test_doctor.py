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
        ids = [r.entry.id for r in results]
        assert "PREC-001" in ids

    def test_autotune_oom(self):
        log = (
            "torch._inductor.exc.InductorError: RuntimeError: Failed to run autotuning "
            "code block: CUDA out of memory. Tried to allocate 1.02 GiB. "
            "GPU 0 has a total capacity of 15.22 GiB of which 686.00 MiB is free."
        )
        results = diagnose(log)
        ids = [r.entry.id for r in results]
        assert "MEM-002" in ids

    def test_trust_remote_code(self):
        log = (
            "ValueError: The repository /models/glm-4-9b contains custom code which "
            "must be executed to correctly load the model. Please pass the argument "
            "trust_remote_code=True"
        )
        ids = [r.entry.id for r in diagnose(log)]
        assert "MISC-003" in ids

    def test_chat_template_missing(self):
        log = (
            "ChatTemplateResolutionError: As of transformers v4.44, default chat "
            "template is no longer allowed, so you must provide a chat template"
        )
        ids = [r.entry.id for r in diagnose(log)]
        assert "MISC-004" in ids

    def test_kv_cache_insufficient(self):
        log = (
            "ValueError: To serve at least one request with the models's max seq len "
            "(8192), (1.5 GiB KV cache is needed, which is larger than the available "
            "KV cache memory (1.08 GiB)."
        )
        ids = [r.entry.id for r in diagnose(log)]
        assert "MEM-003" in ids

    def test_pip_override(self):
        results = diagnose("user ran: pip install torch --upgrade")
        assert "DEP-001" in [r.entry.id for r in results]

    def test_oom(self):
        results = diagnose("torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 512 MiB")
        assert "MEM-001" in [r.entry.id for r in results]

    def test_no_match(self):
        results = diagnose("everything looks fine here, no known error patterns")
        assert results == []

    def test_gptq_fused_shards(self):
        log = (
            "ValueError: Detected some but not all shards of "
            "model.layers.44.mlp.gate_up_proj are quantized. "
            "All shards of fused layers to have the same precision."
        )
        ids = [r.entry.id for r in diagnose(log)]
        assert "MISC-005" in ids

    def test_port_conflict(self):
        results = diagnose("OSError: [Errno 98] Address already in use")
        assert "MISC-002" in [r.entry.id for r in results]


class TestGetById:
    def test_known(self):
        assert get_by_id("ENV-001") is not None

    def test_unknown(self):
        assert get_by_id("NOPE") is None
