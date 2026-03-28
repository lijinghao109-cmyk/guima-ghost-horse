# Phase 1: 空占位。Phase 2 在此添加 generate_drum_pattern 工具定义。
#
# Phase 2 新增示例：
# TOOLS = [
#     {
#         "name": "generate_drum_pattern",
#         "description": "生成概率鼓组 MIDI 音符，写入指定 clip（有机感，每次略有不同）",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "track_index": {"type": "integer"},
#                 "clip_index": {"type": "integer"},
#                 "style": {
#                     "type": "string",
#                     "enum": ["techno", "house", "minimal", "broken", "glitch"],
#                     "description": "鼓机风格预设",
#                 },
#                 "bars": {"type": "integer", "default": 2},
#                 "variation": {
#                     "type": "number",
#                     "description": "随机程度 0.0=机械 1.0=混乱 0.3=自然",
#                     "default": 0.3,
#                 },
#             },
#             "required": ["track_index", "clip_index", "style"],
#         },
#     }
# ]

TOOLS: list[dict] = []
