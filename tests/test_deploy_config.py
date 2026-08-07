"""deploy 配置生成模块单元测试。"""

from __future__ import annotations

from mxdeploy.deploy.config import (
    build_config,
    check_precision,
    estimate_params,
)


class TestEstimateParams:
    def test_7b(self):
        assert estimate_params("Qwen/Qwen2.5-7B-Instruct") == 7.0

    def test_3b(self):
        assert estimate_params("Qwen/Qwen2.5-3B-Instruct") == 3.0

    def test_no_match(self):
        assert estimate_params("my-model") is None


class TestCheckPrecision:
    def test_fp8_rejected(self):
        pc = check_precision("deepseek-ai/DeepSeek-V2-FP8")
        assert pc.is_fp8 is True
        assert pc.is_supported is False

    def test_fp8_in_middle(self):
        pc = check_precision("Qwen2.5-72B-Instruct-FP8")
        assert pc.is_fp8 is True
        assert pc.is_supported is False

    def test_plain_model_ok(self):
        pc = check_precision("Qwen/Qwen2.5-7B-Instruct")
        assert pc.is_supported is True
        assert pc.is_fp8 is False

    def test_quantized_detected(self):
        pc = check_precision("Qwen/Qwen2.5-7B-Instruct-GPTQ-Int8")
        assert pc.is_supported is True
        assert pc.detected_precision == "quantized"


class TestBuildConfig:
    def test_7b_fp16_warns_on_16g(self):
        cfg = build_config("Qwen/Qwen2.5-7B-Instruct", precision="fp16")
        # 7B FP16 ≈ 14GB 接近 16G 上限 → 有警告
        assert any("超出" in w for w in cfg.warnings)

    def test_3b_fp16_no_warn(self):
        cfg = build_config("Qwen/Qwen2.5-3B-Instruct", precision="fp16")
        assert not any("超出" in w for w in cfg.warnings)

    def test_command_contains_expected(self):
        cfg = build_config("Qwen/Qwen2.5-3B-Instruct")
        cmd = cfg.to_command(python_bin="/opt/conda/bin/python")
        assert cmd[0] == "/opt/conda/bin/python"
        assert "-m" in cmd and "vllm.entrypoints.openai.api_server" in cmd
        assert "--port" in cmd and "8000" in cmd
        assert "--model" in cmd and "Qwen/Qwen2.5-3B-Instruct" in cmd

    def test_fp8_config_includes_warning(self):
        cfg = build_config("Qwen2.5-72B-Instruct-FP8")
        assert any("FP8" in w for w in cfg.warnings)

    def test_int8_sets_quantization(self):
        cfg = build_config("Qwen/Qwen2.5-7B-Instruct", precision="int8")
        assert cfg.quantization == "gptq"


class TestV02Features:
    """v0.2 新功能测试：参数透传 / 默认 util / GPTQ-Int4 自动识别。"""

    def test_gptq_int4_auto_detected(self):
        cfg = build_config("Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4")
        assert cfg.quantization == "gptq"

    def test_glm_gptq_int4_auto_detected(self):
        cfg = build_config("glm-4-9b-chat-GPTQ-Int4")
        assert cfg.quantization == "gptq"

    def test_default_util_is_08(self):
        cfg = build_config("Qwen/Qwen2.5-3B-Instruct")
        assert cfg.gpu_memory_utilization == 0.8

    def test_enforce_eager_in_command(self):
        cfg = build_config("Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4", enforce_eager=True)
        cmd = cfg.to_command()
        assert "--enforce-eager" in cmd

    def test_trust_remote_code_in_command(self):
        cfg = build_config("glm-4-9b-chat", trust_remote_code=True)
        cmd = cfg.to_command()
        assert "--trust-remote-code" in cmd

    def test_extra_args_passthrough(self):
        cfg = build_config("Qwen/Qwen2.5-3B-Instruct", extra_args=["--max-num-seqs", "4"])
        cmd = cfg.to_command()
        assert "--max-num-seqs" in cmd and "4" in cmd
