TOOLS: list[dict] = [
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
]
