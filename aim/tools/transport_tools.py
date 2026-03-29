TOOLS: list[dict] = [
    {
        "name": "start_playback",
        "description": "开始播放",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "stop_playback",
        "description": "停止播放",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "back_to_arrangement",
        "description": "停止所有 clip 播放，回到编排视图",
        "input_schema": {"type": "object", "properties": {}},
    },
]
