"""
AbletonBridge — TCP socket 通信层。

外部模块只调用 `bridge.call(command, params)`，socket 细节全部封装在此。

Phase 4 扩展点：子类化 AbletonBridge，override call() 接入连接池：
    bridge = PooledAbletonBridge(host="localhost", port=9877, pool_size=4)
"""

import json
import socket


class AbletonBridge:
    """TCP socket 通信层，负责与 Ableton Remote Script 通信。

    Phase 4 可子类化为 PooledAbletonBridge，override call() 实现连接复用。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9877,
        timeout: float = 15.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def call(self, command: str, params: dict) -> dict:
        """发送 JSON 命令，返回响应 dict。失败返回 {"error": str}。

        每次调用建立新的短连接（短连接模型）。
        Phase 4 override 此方法可接入长连接池。
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.settimeout(self.timeout)

            payload = json.dumps({"type": command, "params": params})
            sock.sendall(payload.encode() + b"\n")

            # 粘包处理：持续 recv 直到能 parse 完整 JSON
            chunks = []
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    data = b"".join(chunks)
                    try:
                        result = json.loads(data.decode())
                        sock.close()
                        return result
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    break

            sock.close()
            data = b"".join(chunks)
            return json.loads(data.decode()) if data else {"status": "ok"}

        except Exception as e:
            return {"error": str(e)}

    def test_connection(self) -> dict:
        """连接检测，调用 get_session_info。启动时使用。"""
        return self.call("get_session_info", {})


# 模块级单例——tool_engine 直接 import 使用。
# Phase 4 替换示例：bridge = PooledAbletonBridge(pool_size=4)
bridge = AbletonBridge()
