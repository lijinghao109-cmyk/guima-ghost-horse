"""
ToolEngine — 工具路由 + Claude API 调用循环。

职责：
- COMMAND_MAP：工具名映射 + 参数变换（Claude 暴露名 → Ableton socket 命令名）
- execute_tool()：参数校验、路由、调用 bridge、格式化结果
- run_session()：单轮用户输入的完整处理（Claude API → 工具执行循环）
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import anthropic

from aim.ableton_bridge import bridge
from aim.prompts import build_system_prompt
from aim.tools import ALL_TOOLS

if TYPE_CHECKING:
    from aim.conversation import ConversationManager


# ── 工具名映射 ────────────────────────────────────────────────────────────────
# 格式：{ claude_tool_name: (socket_command, param_transformer_fn) }
# 新增映射时只需在此添加一条，execute_tool 自动路由。

def _transform_load_instrument(params: dict) -> dict:
    """load_instrument_or_effect → load_browser_item 的参数变换。"""
    return {
        "track_index": params.get("track_index"),
        "item_uri": params.get("uri"),  # Claude 用 "uri"，socket 用 "item_uri"
    }


COMMAND_MAP: dict[str, tuple[str, callable]] = {
    "load_instrument_or_effect": ("load_browser_item", _transform_load_instrument),
}


# ── 工具执行 ──────────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """路由工具调用，返回字符串结果。

    Args:
        tool_name:  Claude 调用的工具名。
        tool_input: Claude 传入的参数 dict。

    Returns:
        JSON 字符串（截断至 200 字符），或 "error: ..." 字符串。
    """
    # 前置校验：add_notes_to_clip 必须有 notes 且不为空
    if tool_name == "add_notes_to_clip":
        notes = tool_input.get("notes")
        if not notes:
            return "error: notes 参数缺失或为空，请重新调用并传入完整的 notes 数组"

    # 路由：有映射的走 COMMAND_MAP，其余直接透传
    if tool_name in COMMAND_MAP:
        cmd, transformer = COMMAND_MAP[tool_name]
        params = transformer(tool_input)
        result = bridge.call(cmd, params)
    else:
        result = bridge.call(tool_name, tool_input)

    if "error" in result:
        return f"error: {result['error']}"
    return json.dumps(result, ensure_ascii=False)[:200]


# ── Claude API 调用循环 ────────────────────────────────────────────────────────

def run_session(conversation: ConversationManager, client: anthropic.Anthropic) -> None:
    """处理单轮用户输入：调用 Claude API，执行工具，直到 Claude 完成回复。

    此函数在 main.py 的对话主循环中被调用，每次用户输入调用一次。
    conversation 中已包含用户最新消息。
    """
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=build_system_prompt(),
            tools=ALL_TOOLS,
            messages=conversation.get_messages(),
        )

        tool_use_blocks = []
        text_parts = []

        for block in response.content:
            if block.type == "thinking":
                pass
            elif block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_use_blocks.append(block)

        if text_parts:
            print(f"\nAIM: {''.join(text_parts)}")

        if not tool_use_blocks:
            conversation.add_assistant_response(response.content)
            break

        print()
        tool_results = []
        for tb in tool_use_blocks:
            args_str = json.dumps(tb.input, ensure_ascii=False)
            print(f"  ▸ {tb.name}({args_str})")
            result = execute_tool(tb.name, tb.input)
            print(f"    ✓ {result[:100]}")

            # Phase 3 扩展点：记录操作日志（当前只记录，不消费）
            conversation.log_action(tb.name, tb.input, result)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tb.id,
                "content": result,
            })

        conversation.add_assistant_response(response.content)
        conversation.add_tool_results(tool_results)

        # Claude 在有工具调用的情况下仍返回 end_turn → 停止循环
        if response.stop_reason == "end_turn":
            break
