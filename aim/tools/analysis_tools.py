"""音频分析工具定义 — 6 个本地执行工具。"""

TOOLS: list[dict] = [
    # ── Tier 1: 核心分析（librosa） ──────────────────────────────────
    {
        "name": "analyze_audio",
        "description": "分析音频文件，提取 BPM、调性、和弦进行、曲式结构、能量曲线",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件的绝对路径（支持 wav/mp3/flac/ogg/aiff/m4a）",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "analyze_beats",
        "description": "分析音频的详细节拍网格、onset 强度、groove 偏移量",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件的绝对路径",
                },
                "start_time": {
                    "type": "number",
                    "description": "分析起始时间（秒），可选",
                },
                "end_time": {
                    "type": "number",
                    "description": "分析结束时间（秒），可选",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "analyze_stem",
        "description": "对单个 stem 文件进行类型感知分析（drums→onset网格，bass→音符序列，vocals→音高轮廓，other→和弦进行）",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "stem 文件路径（通常来自 separate_stems 的输出）",
                },
                "stem_type": {
                    "type": "string",
                    "enum": ["vocals", "drums", "bass", "other"],
                    "description": "stem 类型，决定分析策略",
                },
            },
            "required": ["file_path", "stem_type"],
        },
    },
    # ── Tier 2: 转换（basic-pitch） ─────────────────────────────────
    {
        "name": "audio_to_midi",
        "description": "将音频文件转换为 MIDI（多声部音高检测），返回 .mid 文件路径和音符预览",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件的绝对路径",
                },
                "output_path": {
                    "type": "string",
                    "description": "输出 .mid 文件路径，默认与输入同目录同名",
                },
                "min_note_length_ms": {
                    "type": "number",
                    "description": "过滤掉短于此时长的音符（毫秒），默认 50",
                },
            },
            "required": ["file_path"],
        },
    },
    # ── Tier 3: 分离（demucs） ──────────────────────────────────────
    {
        "name": "separate_stems",
        "description": "将音频分离为 4 个 stem（vocals/drums/bass/other），耗时约 30-60 秒",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件的绝对路径",
                },
                "output_dir": {
                    "type": "string",
                    "description": "输出目录，默认在输入文件同目录下的 stems/ 文件夹",
                },
                "model": {
                    "type": "string",
                    "description": "demucs 模型名，默认 htdemucs",
                },
            },
            "required": ["file_path"],
        },
    },
    # ── 桥接工具 ─────────────────────────────────────────────────────
    {
        "name": "load_audio_to_track",
        "description": "将音频文件加载到 Ableton 音频轨的指定 clip 槽（当前需用户手动拖入）",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "音频文件的绝对路径",
                },
                "track_index": {
                    "type": "integer",
                    "description": "目标音频轨索引",
                },
                "clip_index": {
                    "type": "integer",
                    "description": "目标 clip 槽索引，默认 0",
                },
            },
            "required": ["file_path", "track_index"],
        },
    },
]
