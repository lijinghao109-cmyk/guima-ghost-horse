"""
AbletonBridge 单元测试。

使用 unittest.mock 模拟 socket，不依赖真实 Ableton 实例。
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from aim.ableton_bridge import AbletonBridge


class TestAbletonBridgeCall(unittest.TestCase):

    def _make_bridge(self) -> AbletonBridge:
        return AbletonBridge(host="localhost", port=9877, timeout=5.0)

    @patch("aim.ableton_bridge.socket.socket")
    def test_successful_call_returns_parsed_dict(self, mock_socket_cls):
        """正常响应能被正确解析为 dict。"""
        response_payload = json.dumps({"status": "ok", "result": {"track_count": 4}}).encode()

        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [response_payload, b""]
        mock_socket_cls.return_value = mock_sock

        bridge = self._make_bridge()
        result = bridge.call("get_session_info", {})

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result"]["track_count"], 4)

    @patch("aim.ableton_bridge.socket.socket")
    def test_connection_refused_returns_error_dict(self, mock_socket_cls):
        """连接失败时返回 {"error": str}，不抛出异常。"""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        bridge = self._make_bridge()
        result = bridge.call("get_session_info", {})

        self.assertIn("error", result)
        self.assertIsInstance(result["error"], str)

    @patch("aim.ableton_bridge.socket.socket")
    def test_fragmented_response_reassembled(self, mock_socket_cls):
        """TCP 粘包：分片响应能被正确拼接解析。"""
        full_response = json.dumps({"status": "ok"}).encode()
        half = len(full_response) // 2

        mock_sock = MagicMock()
        mock_sock.recv.side_effect = [
            full_response[:half],
            full_response[half:],
            b"",
        ]
        mock_socket_cls.return_value = mock_sock

        bridge = self._make_bridge()
        result = bridge.call("set_tempo", {"tempo": 90})

        self.assertEqual(result["status"], "ok")

    def test_test_connection_calls_get_session_info(self):
        """test_connection() 调用 get_session_info 命令。"""
        bridge = self._make_bridge()
        bridge.call = MagicMock(return_value={"status": "ok"})

        bridge.test_connection()

        bridge.call.assert_called_once_with("get_session_info", {})


if __name__ == "__main__":
    unittest.main()
