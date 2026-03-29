TOOLS: list[dict] = [
    {
        "name": "set_track_volume",
        "description": "设置轨道音量",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "volume": {
                    "type": "number",
                    "description": "音量值，0.0（静音）到 1.0（最大），0.85 约等于 unity gain",
                },
            },
            "required": ["track_index", "volume"],
        },
    },
    {
        "name": "set_track_panning",
        "description": "设置轨道声像位置",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "panning": {
                    "type": "number",
                    "description": "声像值，-1.0（最左）到 1.0（最右），0.0=居中",
                },
            },
            "required": ["track_index", "panning"],
        },
    },
    {
        "name": "set_track_mute",
        "description": "设置轨道静音状态",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "mute": {"type": "boolean", "description": "true=静音，false=取消静音"},
            },
            "required": ["track_index", "mute"],
        },
    },
    {
        "name": "set_track_solo",
        "description": "设置轨道独奏状态",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "solo": {"type": "boolean", "description": "true=独奏，false=取消独奏"},
            },
            "required": ["track_index", "solo"],
        },
    },
]
