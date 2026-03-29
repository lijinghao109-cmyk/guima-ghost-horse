"""basic-pitch 音频转 MIDI。"""

from __future__ import annotations

import os
from pathlib import Path

from aim.analysis._validate import validate_audio_file


def run_audio_to_midi(params: dict) -> dict:
    """将音频文件转换为 MIDI，返回文件路径和音符预览。"""
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except ImportError:
        return {"error": "basic-pitch 未安装。运行: pip install 'aim[midi]'"}

    file_path = params.get("file_path", "")
    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    # 输出路径
    input_path = Path(file_path)
    output_path = params.get("output_path")
    if output_path:
        midi_path = Path(output_path)
    else:
        midi_path = input_path.with_suffix(".mid")

    min_note_length = params.get("min_note_length_ms", 50) / 1000.0  # 转秒

    try:
        print("  ⏳ 正在转换音频为 MIDI...")
        model_output, midi_data, note_events = predict(str(file_path))

        # 保存 MIDI 文件
        midi_path.parent.mkdir(parents=True, exist_ok=True)
        midi_data.write(str(midi_path))

        # 构建音符预览（前 20 个，过滤短音符）
        notes_preview = []
        total_notes = 0
        pitch_min = 127
        pitch_max = 0

        for note in note_events:
            start_time, end_time, pitch, velocity, *_ = note
            duration = end_time - start_time

            pitch_int = int(round(pitch))
            vel_int = int(round(velocity * 127))
            pitch_min = min(pitch_min, pitch_int)
            pitch_max = max(pitch_max, pitch_int)
            total_notes += 1

            if duration >= min_note_length and len(notes_preview) < 20:
                notes_preview.append({
                    "pitch": pitch_int,
                    "start_time": round(float(start_time), 3),
                    "duration": round(float(duration), 3),
                    "velocity": vel_int,
                })

        return {
            "midi_file": str(midi_path),
            "note_count": total_notes,
            "pitch_range": {
                "low": pitch_min if total_notes > 0 else 0,
                "high": pitch_max if total_notes > 0 else 0,
            },
            "notes_preview": notes_preview,
        }
    except Exception as e:
        return {"error": f"MIDI 转换失败: {e}"}
