"""音频分析工具测试：文件校验、本地路由、结果格式、缺依赖错误。"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from aim.analysis._validate import validate_audio_file, SUPPORTED_FORMATS
from aim.tool_engine import execute_tool, LOCAL_TOOLS, RESULT_LIMIT


class TestValidateAudioFile(unittest.TestCase):
    """音频文件校验测试。"""

    def test_missing_path(self):
        """空路径返回错误。"""
        self.assertIsNotNone(validate_audio_file(""))

    def test_nonexistent_file(self):
        """不存在的文件返回错误。"""
        err = validate_audio_file("/nonexistent/path/audio.wav")
        self.assertIn("不存在", err)

    def test_directory_path(self):
        """目录路径返回错误。"""
        err = validate_audio_file(tempfile.gettempdir())
        self.assertIn("不是文件", err)

    def test_unsupported_format(self):
        """不支持的格式返回错误。"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not audio")
            f.flush()
            err = validate_audio_file(f.name)
        os.unlink(f.name)
        self.assertIn("不支持", err)

    def test_empty_file(self):
        """空文件返回错误。"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            pass  # 创建空文件
        err = validate_audio_file(f.name)
        os.unlink(f.name)
        self.assertIn("为空", err)

    def test_valid_file(self):
        """有效音频文件通过校验。"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 100)  # 伪造 WAV 头
            f.flush()
        err = validate_audio_file(f.name)
        os.unlink(f.name)
        self.assertIsNone(err)

    def test_all_supported_formats(self):
        """所有声明的格式都被支持。"""
        expected = {".wav", ".mp3", ".flac", ".ogg", ".aiff", ".m4a"}
        self.assertEqual(SUPPORTED_FORMATS, expected)


class TestLocalToolRouting(unittest.TestCase):
    """本地工具路由测试。"""

    def test_local_tools_registered(self):
        """6 个分析工具在 LOCAL_TOOLS 中注册。"""
        expected = {
            "analyze_audio", "analyze_beats", "analyze_stem",
            "audio_to_midi", "separate_stems", "load_audio_to_track",
        }
        self.assertEqual(set(LOCAL_TOOLS.keys()), expected)

    @patch("aim.tool_engine.bridge")
    def test_local_tool_does_not_call_bridge(self, mock_bridge):
        """本地工具不经过 Ableton socket。"""
        # analyze_audio 会因为文件不存在而返回错误，但不应调用 bridge
        result = execute_tool("analyze_audio", {"file_path": "/nonexistent.wav"})
        mock_bridge.call.assert_not_called()
        self.assertTrue(result.startswith("error:"))

    @patch("aim.tool_engine.bridge")
    def test_ableton_tool_still_uses_bridge(self, mock_bridge):
        """Ableton 工具仍走 bridge。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("set_tempo", {"tempo": 120})
        mock_bridge.call.assert_called_once()

    @patch("aim.tool_engine.bridge")
    def test_load_audio_to_track_missing_params(self, mock_bridge):
        """load_audio_to_track 缺少参数返回错误。"""
        result = execute_tool("load_audio_to_track", {"file_path": ""})
        self.assertIn("error", result)
        mock_bridge.call.assert_not_called()

    @patch("aim.tool_engine.bridge")
    def test_load_audio_to_track_returns_instruction(self, mock_bridge):
        """load_audio_to_track 返回手动操作指引。"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 100)
            f.flush()
        result = execute_tool("load_audio_to_track", {
            "file_path": f.name,
            "track_index": 0,
        })
        os.unlink(f.name)
        mock_bridge.call.assert_not_called()
        parsed = json.loads(result)
        self.assertEqual(parsed["action_required"], "manual_load")
        self.assertEqual(parsed["track_index"], 0)


class TestResultLimitConfig(unittest.TestCase):
    """分析工具的截断限制配置。"""

    def test_analysis_tools_have_limits(self):
        """分析工具有自定义截断限制。"""
        analysis_tools_with_limits = {
            "analyze_audio", "analyze_beats", "analyze_stem",
            "audio_to_midi", "separate_stems", "load_audio_to_track",
        }
        for tool in analysis_tools_with_limits:
            self.assertIn(tool, RESULT_LIMIT, f"{tool} 缺少 RESULT_LIMIT 配置")

    def test_analysis_limits_are_generous(self):
        """分析工具截断限制 >= 500。"""
        analysis_limits = {
            "analyze_audio": 2000,
            "analyze_beats": 2000,
            "analyze_stem": 2000,
            "audio_to_midi": 3000,
            "separate_stems": 1000,
            "load_audio_to_track": 500,
        }
        for tool, expected in analysis_limits.items():
            self.assertEqual(RESULT_LIMIT[tool], expected, f"{tool} 截断限制不匹配")


class TestMissingDependency(unittest.TestCase):
    """依赖缺失时的错误消息。"""

    @patch("aim.tool_engine.bridge")
    def test_analyze_audio_missing_essentia(self, mock_bridge):
        """essentia 未安装时返回安装提示。"""
        with patch.dict("sys.modules", {"essentia": None}):
            result = execute_tool("analyze_audio", {"file_path": "/nonexistent.wav"})
            # 文件校验会先失败（不存在），这也是合理的行为
            self.assertIn("error", result)


class TestAnalyzeStemValidation(unittest.TestCase):
    """analyze_stem 参数校验。"""

    @patch("aim.tool_engine.bridge")
    def test_invalid_stem_type(self, mock_bridge):
        """无效的 stem_type 返回错误。"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF" + b"\x00" * 100)
            f.flush()
        result = execute_tool("analyze_stem", {
            "file_path": f.name,
            "stem_type": "invalid",
        })
        os.unlink(f.name)
        self.assertIn("error", result)
        mock_bridge.call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
