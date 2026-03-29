TOOLS: list[dict] = [
    {
        "name": "get_device_parameters",
        "description": "获取轨道上指定设备的所有参数（名称、当前值、最小值、最大值）",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "device_index": {
                    "type": "integer",
                    "description": "设备索引，0=第一个设备（通常是乐器）",
                },
            },
            "required": ["track_index", "device_index"],
        },
    },
    {
        "name": "set_device_parameter",
        "description": "设置设备参数值（先调用 get_device_parameters 查看可用参数名）",
        "input_schema": {
            "type": "object",
            "properties": {
                "track_index": {"type": "integer"},
                "device_index": {
                    "type": "integer",
                    "description": "设备索引，0=第一个设备（通常是乐器）",
                },
                "param_name": {
                    "type": "string",
                    "description": "参数名称，使用 get_device_parameters 返回的精确名称",
                },
                "value": {"type": "number", "description": "参数值（会自动钳制到有效范围）"},
            },
            "required": ["track_index", "device_index", "param_name", "value"],
        },
    },
]
