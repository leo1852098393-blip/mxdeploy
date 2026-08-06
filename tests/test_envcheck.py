"""envcheck 模块单元测试。"""

from __future__ import annotations

from unittest import mock

from mxdeploy.envcheck.detector import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_WARN,
    check_mx_smi,
    check_python,
    check_torch,
    check_vllm,
    run_all,
)


class TestCheckMxSmi:
    def test_no_mx_smi(self):
        with mock.patch("shutil.which", return_value=None):
            model, count, mem, detail = check_mx_smi()
            assert count == 0
            assert "未找到" in detail

    def test_mx_smi_detects_c500(self):
        fake_out = "GPU 0: MetaX 曦云 C500 | Usage: 42%\nGPU 1: MetaX 曦云 C500 | Usage: 10%\n"
        mem_out = "vram total: 67108864 KB\nvram used: 846384 KB\n"
        with mock.patch("shutil.which", return_value="/usr/bin/mx-smi"), mock.patch(
            "mxdeploy.envcheck.detector._run_cmd"
        ) as mock_run:
            mock_run.side_effect = [
                (0, fake_out),  # --show-usage
                (0, mem_out),  # --show-memory
            ]
            model, count, mem, detail = check_mx_smi()
            assert model == "曦云 C500"
            assert count == 2
            assert mem == 65536  # 67108864 KB // 1024

    def test_mx_smi_failure(self):
        with mock.patch("shutil.which", return_value="/usr/bin/mx-smi"), mock.patch(
            "mxdeploy.envcheck.detector._run_cmd", return_value=(1, "driver error")
        ):
            model, count, mem, detail = check_mx_smi()
            assert count == 0
            assert "执行失败" in detail


class TestCheckPython:
    def test_ok(self):
        result = check_python()
        assert result.status == STATUS_OK
        assert "Python" in result.detail


class TestCheckTorch:
    def test_metax_marker(self):
        # 本机装有 torch，只 patch 版本号，避免污染模块
        with mock.patch("torch.__version__", "2.6.0+metax"):
            result = check_torch()
            assert result.status == STATUS_OK
            assert "适配版" in result.hint

    def test_plain_torch_warns(self):
        with mock.patch("torch.__version__", "2.8.0+cpu"):
            result = check_torch()
            assert result.status == STATUS_WARN

    def test_no_torch(self):
        # sys.modules 置 None 使 import torch 抛 ImportError
        with mock.patch.dict("sys.modules", {"torch": None}):
            result = check_torch()
            assert result.status == STATUS_WARN
            assert "未安装" in result.detail


class TestCheckVllm:
    def test_maca_marker(self):
        # vllm 本机未装，patch 模块即可
        fake = mock.Mock()
        fake.__version__ = "0.8.5+maca"
        with mock.patch.dict("sys.modules", {"vllm": fake}):
            result = check_vllm()
            assert result.status == STATUS_OK

    def test_no_vllm_no_maca_path(self):
        # 无 vllm 且 MACA_PATH 未设置 → ERROR（可诊断的高频坑）
        with mock.patch.dict("sys.modules", {"vllm": None}), mock.patch(
            "os.getenv", return_value=None
        ):
            result = check_vllm()
            assert result.status == STATUS_ERROR
            assert "MACA_PATH" in result.hint


class TestRunAll:
    def test_no_gpu_report(self):
        with mock.patch("mxdeploy.envcheck.detector.check_mx_smi", return_value=("未知", 0, 0, "not found")):
            report = run_all()
            assert report.has_gpu is False
            assert any(c.name == "mx-smi" and c.status == STATUS_ERROR for c in report.checks)

    def test_gpu_report(self):
        with mock.patch(
            "mxdeploy.envcheck.detector.check_mx_smi",
            return_value=("曦云 C500", 1, 65536, "ok"),
        ):
            report = run_all()
            assert report.has_gpu is True
            assert report.is_metax_env is True
            summary = report.summary()
            assert summary["gpu_count"] == 1
            assert summary["is_metax_env"] is True
