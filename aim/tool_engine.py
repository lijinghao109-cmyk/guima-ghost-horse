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
from aim.analysis import (
    run_analyze_audio,
    run_analyze_beats,
    run_analyze_stem,
    run_audio_to_midi,
    run_separate_stems,
    run_load_audio_to_track,
)
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


# ── 本地执行工具（不经过 Ableton socket） ────────────────────────────────────

LOCAL_TOOLS: dict[str, callable] = {
    "analyze_audio": run_analyze_audio,
    "analyze_beats": run_analyze_beats,
    "analyze_stem": run_analyze_stem,
    "audio_to_midi": run_audio_to_midi,
    "separate_stems": run_separate_stems,
    "load_audio_to_track": run_load_audio_to_track,
}


# ── 工具执行 ──────────────────────────────────────────────────────────────────

# 返回大量数据的工具需要更高的截断限制
RESULT_LIMIT: dict[str, int] = {
    "get_device_parameters": 2000,
    "get_track_info": 1000,
    "get_clip_notes": 2000,
    "get_session_info": 500,
    "analyze_audio": 2000,
    "analyze_beats": 2000,
    "analyze_stem": 2000,
    "audio_to_midi": 3000,
    "separate_stems": 1000,
    "load_audio_to_track": 500,
}
DEFAULT_RESULT_LIMIT = 200


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """路由工具调用，返回字符串结果。

    Args:
        tool_name:  Claude 调用的工具名。
        tool_input: Claude 传入的参数 dict。

    Returns:
        JSON 字符串（按工具截断），或 "error: ..." 字符串。
    """
    # 前置校验：add_notes_to_clip 必须有 notes 且不为空
    if tool_name == "add_notes_to_clip":
        notes = tool_input.get("notes")
        if not notes:
            return "error: notes 参数缺失或为空，请重新调用并传入完整的 notes 数组"

    # 值域钳制：Remote Script 不做范围校验
    if tool_name == "set_track_volume":
        tool_input["volume"] = max(0.0, min(1.0, tool_input.get("volume", 0.85)))
    elif tool_name == "set_track_panning":
        tool_input["panning"] = max(-1.0, min(1.0, tool_input.get("panning", 0.0)))

    # 路由：本地工具 → COMMAND_MAP → 透传 bridge
    if tool_name in LOCAL_TOOLS:
        result = LOCAL_TOOLS[tool_name](tool_input)
    elif tool_name in COMMAND_MAP:
        cmd, transformer = COMMAND_MAP[tool_name]
        params = transformer(tool_input)
        result = bridge.call(cmd, params)
    else:
        result = bridge.call(tool_name, tool_input)

    if "error" in result:
        return f"error: {result['error']}"
    limit = RESULT_LIMIT.get(tool_name, DEFAULT_RESULT_LIMIT)
    return json.dumps(result, ensure_ascii=False)[:limit]


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
