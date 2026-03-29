"""tool_engine 单元测试：路由、值域钳制、截断。"""

import json
import unittest
from unittest.mock import patch, MagicMock

from aim.tool_engine import execute_tool, RESULT_LIMIT, DEFAULT_RESULT_LIMIT, COMMAND_MAP


class TestExecuteTool(unittest.TestCase):
    """execute_tool 行为测试。"""

    @patch("aim.tool_engine.bridge")
    def test_passthrough_routing(self, mock_bridge):
        """无 COMMAND_MAP 条目的工具直接透传。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("set_track_volume", {"track_index": 0, "volume": 0.8})
        mock_bridge.call.assert_called_once_with("set_track_volume", {"track_index": 0, "volume": 0.8})

    @patch("aim.tool_engine.bridge")
    def test_command_map_routing(self, mock_bridge):
        """load_instrument_or_effect 走 COMMAND_MAP 映射。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("load_instrument_or_effect", {"track_index": 0, "uri": "query:Synths#Operator"})
        mock_bridge.call.assert_called_once_with("load_browser_item", {"track_index": 0, "item_uri": "query:Synths#Operator"})

    @patch("aim.tool_engine.bridge")
    def test_volume_clamping_high(self, mock_bridge):
        """set_track_volume 超过 1.0 钳制为 1.0。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("set_track_volume", {"track_index": 0, "volume": 1.5})
        args = mock_bridge.call.call_args[0]
        self.assertEqual(args[1]["volume"], 1.0)

    @patch("aim.tool_engine.bridge")
    def test_volume_clamping_low(self, mock_bridge):
        """set_track_volume 低于 0.0 钳制为 0.0。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("set_track_volume", {"track_index": 0, "volume": -0.5})
        args = mock_bridge.call.call_args[0]
        self.assertEqual(args[1]["volume"], 0.0)

    @patch("aim.tool_engine.bridge")
    def test_panning_clamping(self, mock_bridge):
        """set_track_panning 超过范围钳制到 -1.0~1.0。"""
        mock_bridge.call.return_value = {"status": "ok"}
        execute_tool("set_track_panning", {"track_index": 0, "panning": 3.0})
        args = mock_bridge.call.call_args[0]
        self.assertEqual(args[1]["panning"], 1.0)

    @patch("aim.tool_engine.bridge")
    def test_notes_empty_validation(self, mock_bridge):
        """add_notes_to_clip notes 为空时返回错误。"""
        result = execute_tool("add_notes_to_clip", {"track_index": 0, "clip_index": 0, "notes": []})
        self.assertTrue(result.startswith("error:"))
        mock_bridge.call.assert_not_called()

    @patch("aim.tool_engine.bridge")
    def test_error_propagation(self, mock_bridge):
        """bridge 返回 error 时格式化为 'error: ...'。"""
        mock_bridge.call.return_value = {"error": "connection refused"}
        result = execute_tool("start_playback", {})
        self.assertEqual(result, "error: connection refused")

    @patch("aim.tool_engine.bridge")
    def test_default_truncation(self, mock_bridge):
        """默认截断为 200 字符。"""
        mock_bridge.call.return_value = {"data": "x" * 500}
        result = execute_tool("set_tempo", {"tempo": 120})
        self.assertLessEqual(len(result), DEFAULT_RESULT_LIMIT)

    @patch("aim.tool_engine.bridge")
    def test_per_tool_truncation(self, mock_bridge):
        """get_device_parameters 使用更高的截断限制。"""
        mock_bridge.call.return_value = {"device": "Operator", "parameters": [{"name": f"param_{i}", "value": i} for i in range(50)]}
        result = execute_tool("get_device_parameters", {"track_index": 0, "device_index": 0})
        self.assertGreater(len(result), DEFAULT_RESULT_LIMIT)
        self.assertLessEqual(len(result), RESULT_LIMIT["get_device_parameters"])


class TestResultLimitConfig(unittest.TestCase):
    """RESULT_LIMIT 配置校验。"""

    def test_large_response_tools_have_limits(self):
        """返回大量数据的工具必须有自定义截断限制。"""
        expected_ableton = {"get_device_parameters", "get_track_info", "get_clip_notes", "get_session_info"}
        expected_analysis = {"analyze_audio", "analyze_beats", "analyze_stem", "audio_to_midi", "separate_stems", "load_audio_to_track"}
        self.assertEqual(set(RESULT_LIMIT.keys()), expected_ableton | expected_analysis)

    def test_default_limit(self):
        """默认截断限制为 200。"""
        self.assertEqual(DEFAULT_RESULT_LIMIT, 200)

    def test_command_map_still_has_load_instrument(self):
        """回归：load_instrument_or_effect 映射仍存在。"""
        self.assertIn("load_instrument_or_effect", COMMAND_MAP)


if __name__ == "__main__":
    unittest.main()
