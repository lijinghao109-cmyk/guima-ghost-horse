"""
AIM — Ableton Interact Machine
自然语言 → Claude 推理 → Ableton 执行
"""

import os
import json
import socket
import anthropic

# ── Ableton Socket 通信层 ──────────────────────────────────────────
ABLETON_HOST = "localhost"
ABLETON_PORT = 9877

def call_ableton(command: str, params: dict) -> dict:
    """直接通过 socket 调用 Ableton Remote Script"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ABLETON_HOST, ABLETON_PORT))
        sock.settimeout(15.0)

        payload = json.dumps({"type": command, "params": params})
        sock.sendall(payload.encode() + b'\n')

        chunks = []
        while True:
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
                data = b''.join(chunks)
                try:
                    result = json.loads(data.decode())
                    sock.close()
                    return result
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                break

        sock.close()
        data = b''.join(chunks)
        return json.loads(data.decode()) if data else {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """将 Claude 工具调用转为 Ableton socket 命令"""
    # 防护：add_notes_to_clip 必须有 notes 且不为空
    if tool_name == "add_notes_to_clip":
        notes = tool_input.get("notes")
        if not notes:
            return "error: notes 参数缺失或为空，请重新调用并传入完整的 notes 数组"

    # 工具名映射：Claude 用的名字 → Ableton socket 实际命令名
    COMMAND_MAP = {
        "load_instrument_or_effect": ("load_browser_item", {
            "track_index": tool_input.get("track_index"),
            "item_uri": tool_input.get("uri"),
        }),
    }

    if tool_name in COMMAND_MAP:
        cmd, params = COMMAND_MAP[tool_name]
        result = call_ableton(cmd, params)
    else:
        result = call_ableton(tool_name, tool_input)

    if "error" in result:
        return f"error: {result['error']}"
    return json.dumps(result, ensure_ascii=False)[:200]


# ── System Prompt ──────────────────────────────────────────────────
SYSTEM_PROMPT = """你是 AIM（Ableton Interact Machine），一个专业的 AI 音乐制作助手，直接控制用户的 Ableton Live。

## 工具调用顺序（严格遵守）
1. get_session_info — 先了解当前状态（现有几条轨道）
2. set_tempo — 设定 BPM
3. create_midi_track — 每个声部建一条轨（先建鼓，再贝斯，再和弦，再旋律）
4. set_track_name — 命名轨道
5. load_instrument_or_effect — 给每条轨道加载乐器（必须在 create_clip 之前）
6. create_clip — 在对应轨道的 clip_index=0 创建 clip，length=8（固定8拍=2小节）
7. add_notes_to_clip — 写入音符（必须包含 notes 数组，绝对不能省略）
8. fire_clip — 播放所有轨道的 clip

## 乐器加载（URI 固定用以下值）
鼓轨:    uri="query:Synths#Drum%20Rack"         → Drum Rack（用MIDI音符触发）
贝斯轨:  uri="query:Synths#Operator"            → Operator（FM合成，适合各种音色）
和弦轨:  uri="query:Synths#Wavetable"           → Wavetable（现代感强）
旋律轨:  uri="query:Synths#Analog"              → Analog（温暖模拟音色）
钢琴/键盘: uri="query:Synths#Electric"          → Electric（电钢琴）
lo-fi专用: 和弦/旋律用 uri="query:Synths#Meld"  → Meld（更有质感）

## 关键规则
- create_clip 的 length 固定用 8（2小节循环，够了）
- add_notes_to_clip 必须同时传 track_index、clip_index、notes 三个参数
- notes 是具体音符数组，不能为空，不能省略
- 如果 note_count 返回 0，说明 notes 没传到，立刻重试并检查参数
- 不要重复调用相同参数的失败工具超过2次，换思路

## 轨道索引规则
- 调用 get_session_info 后，track_count 是现有轨道数
- 新建的第1条轨道索引 = track_count（比如原来4条，新建的是索引4）
- 每 create_midi_track 之后索引+1

## MIDI 音符格式（每个字段都必须有）
{"pitch": int, "start_time": float, "duration": float, "velocity": int, "mute": false}

## 鼓 MIDI 映射
Kick=36, Snare=38, HiHat=42, OpenHat=46, Clap=39

## 8拍鼓组示例（lo-fi风格，直接用这个）
Kick: start=0,1,2,3,4,5,6,7 中选 0,2,3.5,4,6
Snare: start=1,3,5,7（每拍后半）
HiHat: 每0.5拍一个，start=0,0.5,1,1.5...7.5

## 风格参数参考
lo-fi:  BPM=75, F小调(root=65), im7-ivm7-vm7
ambient: BPM=80, D大调(root=62), 长音符
EDM:    BPM=130, C大调(root=60), 密集律动
jazz:   BPM=100, 复杂和声

## 和弦写法（以F小调为例，8拍循环）
Fm7:  [65,68,72,75] 各音符 start=0.0, duration=2.0
Bbm7: [70,73,77,80] start=2.0, duration=2.0
Cm7:  [72,75,79,82] start=4.0, duration=2.0
Fm7:  [65,68,72,75] start=6.0, duration=2.0

回应先用中文说明创作思路，再执行工具。每步执行后继续下一步，不要停下来等确认。"""


# ── MCP 工具定义（给 Claude 看的） ────────────────────────────────
TOOLS = [
    {
        "name": "get_session_info",
        "description": "获取当前 Ableton session 状态，包括 track_count（现有轨道数）和 BPM",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_tempo",
        "description": "设置 BPM",
        "input_schema": {
            "type": "object",
            "properties": {"tempo": {"type": "number"}},
            "required": ["tempo"],
        },
    },
    {
        "name": "create_midi_track",
        "description": "创建新 MIDI 轨道，返回创建结果",
        "input_schema": {
            "type": "object",
            "properties": {"index": {"type": "integer", "description": "插入位置，-1=末尾"}},
        },
    },
    {
        "name": "set_track_name",
        "description": "设置轨道名称",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["track_index", "name"],
        },
    },
    {
        "name": "load_instrument_or_effect",
        "description": "给轨道加载乐器或效果器",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "uri": {"type": "string", "description": "乐器URI，如 query:Synths#Operator"},
            },
            "required": ["track_index", "uri"],
        },
    },
    {
        "name": "create_clip",
        "description": "在轨道的 clip slot 创建 MIDI clip",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "clip_index": {"type": "integer"},
                "length": {"type": "number", "description": "clip长度（拍数）"},
            },
            "required": ["track_index", "clip_index"],
        },
    },
    {
        "name": "add_notes_to_clip",
        "description": "向 clip 添加 MIDI 音符",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "clip_index": {"type": "integer"},
                "notes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "pitch": {"type": "integer"},
                            "start_time": {"type": "number"},
                            "duration": {"type": "number"},
                            "velocity": {"type": "integer"},
                            "mute": {"type": "boolean"},
                        },
                        "required": ["pitch", "start_time", "duration", "velocity", "mute"],
                    },
                },
            },
            "required": ["track_index", "clip_index", "notes"],
        },
    },
    {
        "name": "fire_clip",
        "description": "播放指定 clip",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "clip_index": {"type": "integer"},
            },
            "required": ["track_index", "clip_index"],
        },
    },
]


# ── 主对话循环 ──────────────────────────────────────────────────────
def aim_session():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误：请设置 ANTHROPIC_API_KEY 环境变量")
        return

    # 测试 Ableton 连接
    test = call_ableton("get_session_info", {})
    if "error" in test:
        print(f"❌ 无法连接 Ableton（端口 {ABLETON_PORT}）: {test['error']}")
        print("   请确认 Ableton 正在运行且 AbletonMCP Remote Script 已加载")
        return
    print(f"✅ Ableton 已连接：{test.get('result', test)}")

    client = anthropic.Anthropic(api_key=api_key)
    conversation = []

    print("\n🎵  AIM — Ableton Interact Machine")
    print("    用自然语言创作音乐。输入 'quit' 退出。")
    print("─" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出 AIM。")
            break

        if user_input.lower() in ("quit", "exit", "q", "退出"):
            print("再见！")
            break
        if not user_input:
            continue

        conversation.append({"role": "user", "content": user_input})

        # Claude 推理 + 工具调用循环
        while True:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation,
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
                conversation.append({"role": "assistant", "content": response.content})
                break

            print()
            tool_results = []
            for tb in tool_use_blocks:
                args_str = json.dumps(tb.input, ensure_ascii=False)
                print(f"  ▸ {tb.name}({args_str})")
                result = execute_tool(tb.name, tb.input)
                print(f"    ✓ {result[:100]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": result,
                })

            conversation.append({"role": "assistant", "content": response.content})
            conversation.append({"role": "user", "content": tool_results})

            if response.stop_reason == "end_turn":
                break


if __name__ == "__main__":
    aim_session()
