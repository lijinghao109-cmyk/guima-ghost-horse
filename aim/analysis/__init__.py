"""
音频分析桥梁 — 本地执行层。

将开源音频分析工具（librosa, basic-pitch, demucs）的结果
转化为 Claude 可推理的结构化数据。

所有 run_* 函数签名统一：(params: dict) -> dict
成功返回数据 dict，失败返回 {"error": str}。
"""

from aim.analysis.audio_analysis import (
    run_analyze_audio,
    run_analyze_beats,
    run_analyze_stem,
)
from aim.analysis.midi_conversion import run_audio_to_midi
from aim.analysis.stem_separation import run_separate_stems, run_load_audio_to_track

__all__ = [
    "run_analyze_audio",
    "run_analyze_beats",
    "run_analyze_stem",
    "run_audio_to_midi",
    "run_separate_stems",
    "run_load_audio_to_track",
]
