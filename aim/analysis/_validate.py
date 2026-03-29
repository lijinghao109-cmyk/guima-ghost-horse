"""音频文件校验 — 所有分析工具共用。"""

from __future__ import annotations

import os
from pathlib import Path

SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".ogg", ".aiff", ".m4a"}
MAX_FILE_SIZE_MB = 500


def validate_audio_file(file_path: str) -> str | None:
    """校验音频文件路径。

    Returns:
        None 表示通过，str 表示错误描述。
    """
    if not file_path:
        return "file_path 参数缺失"

    p = Path(file_path)

    if not p.exists():
        return f"文件不存在: {file_path}"

    if not p.is_file():
        return f"路径不是文件: {file_path}"

    ext = p.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        return f"不支持的格式 '{ext}'，支持: {', '.join(sorted(SUPPORTED_FORMATS))}"

    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"文件过大 ({size_mb:.0f}MB)，上限 {MAX_FILE_SIZE_MB}MB"

    if p.stat().st_size == 0:
        return "文件为空"

    return None
