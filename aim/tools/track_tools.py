TOOLS: list[dict] = [
    {
        "name": "create_midi_track",
        "description": "创建新 MIDI 轨道，返回创建结果",
        "input_schema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "插入位置，-1=末尾"},
            },
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
]
