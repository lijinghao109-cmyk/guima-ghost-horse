TOOLS: list[dict] = [
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
