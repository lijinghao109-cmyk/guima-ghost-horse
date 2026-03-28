"""
ConversationManager — 对话历史与操作日志管理。

职责：
- 封装 Claude API 消息列表的所有读写操作
- 维护 Ableton 操作日志（Phase 3 撤销功能的数据基础）

Phase 3 扩展点：
- log_action() 记录每次成功的工具调用
- pop_last_action() 供撤销逻辑查询并弹出最近操作
"""

from __future__ import annotations


class ConversationManager:
    """管理与 Claude 的对话历史，以及 Ableton 操作日志。"""

    def __init__(self) -> None:
        self._messages: list[dict] = []
        # Phase 3 扩展点：可撤销操作日志
        # 格式：[{"tool": str, "params": dict, "result": str}, ...]
        # Phase 1 只记录，不使用。Phase 3 实现 undo 时读取此栈。
        self._action_log: list[dict] = []

    # ── 消息历史 ──────────────────────────────────────────────────────

    def add_user_message(self, text: str) -> None:
        self._messages.append({"role": "user", "content": text})

    def add_assistant_response(self, content: list) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def add_tool_results(self, results: list[dict]) -> None:
        self._messages.append({"role": "user", "content": results})

    def get_messages(self) -> list[dict]:
        return self._messages

    # ── 操作日志（Phase 3 扩展点）────────────────────────────────────

    def log_action(self, tool_name: str, params: dict, result: str) -> None:
        """记录一次成功的工具调用。

        Phase 1：仅记录，不被其他逻辑消费。
        Phase 3：撤销栈依赖此数据，结合 Ableton 的反向命令实现 undo。
        """
        self._action_log.append({
            "tool": tool_name,
            "params": params,
            "result": result,
        })

    def last_action(self) -> dict | None:
        """返回最近一次操作，不弹出。"""
        return self._action_log[-1] if self._action_log else None

    def pop_last_action(self) -> dict | None:
        """弹出并返回最近一次操作。

        Phase 1：存在但不被调用。
        Phase 3：撤销命令调用此方法，再根据 tool 名称派发反向操作。
        """
        return self._action_log.pop() if self._action_log else None
