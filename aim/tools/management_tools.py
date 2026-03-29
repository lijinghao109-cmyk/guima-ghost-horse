TOOLS: list[dict] = [
    {
        "name": "get_track_info",
        "description": "获取单条轨道的详细信息（名称、音量、声像、设备列表、clip 列表等）",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
            },
            "required": ["track_index"],
        },
    },
    {
        "name": "create_audio_track",
        "description": "创建新音频轨道",
        "input_schema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "插入位置，-1=末尾"},
            },
        },
    },
    {
        "name": "delete_track",
        "description": "删除轨道（不能删除最后一条轨道。删除多条时从高索引往低索引删）",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
            },
            "required": ["track_index"],
        },
    },
    {
        "name": "delete_clip",
        "description": "删除指定 clip slot 中的 clip",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "clip_index": {"type": "integer"},
            },
            "required": ["track_index", "clip_index"],
        },
    },
    {
        "name": "stop_clip",
        "description": "停止播放指定 clip",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "clip_index": {"type": "integer"},
            },
            "required": ["track_index", "clip_index"],
        },
    },
    {
        "name": "get_clip_notes",
        "description": "读取 clip 中的 MIDI 音符（最多返回 50 个）",
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
