"""音频转 MIDI — 使用 librosa piptrack + pretty_midi。"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from aim.analysis._validate import validate_audio_file


def run_audio_to_midi(params: dict) -> dict:
    """将音频文件转换为 MIDI，返回文件路径和音符预览。"""
    try:
        import librosa
        import pretty_midi
    except ImportError:
        return {"error": "librosa 或 pretty_midi 未安装。运行: pip install librosa pretty_midi"}

    file_path = params.get("file_path", "")
    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    input_path = Path(file_path)
    output_path = params.get("output_path")
    midi_path = Path(output_path) if output_path else input_path.with_suffix(".mid")

    min_note_length = params.get("min_note_length_ms", 80) / 1000.0

    try:
        print("  ⏳ 正在转换音频为 MIDI...")
        y, sr = librosa.load(file_path, sr=22050)

        # 多声部音高检测
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
        hop_length = 512  # librosa 默认
        frame_duration = hop_length / sr

        # 提取每帧中最强的音高（最多 4 个同时发声）
        notes = []  # (pitch_hz, start_frame, magnitude)
        for frame_idx in range(pitches.shape[1]):
            frame_pitches = pitches[:, frame_idx]
            frame_mags = magnitudes[:, frame_idx]
            # 找出该帧中幅度最大的几个频率
            indices = np.where(frame_mags > 0)[0]
            if len(indices) == 0:
                continue
            sorted_idx = indices[np.argsort(frame_mags[indices])[::-1]][:4]
            for idx in sorted_idx:
                hz = frame_pitches[idx]
                if hz > 50:  # 过滤低于 50Hz 的噪声
                    notes.append((float(hz), frame_idx, float(frame_mags[idx])))

        # 将逐帧音高合并为音符（连续相近频率 → 一个音符）
        if not notes:
            return {
                "midi_file": str(midi_path),
                "note_count": 0,
                "pitch_range": {"low": 0, "high": 0},
                "notes_preview": [],
            }

        # 按帧排序
        notes.sort(key=lambda x: (x[1], -x[2]))

        # 合并连续帧中相近的音高为音符事件
        merged_notes = []  # (midi_pitch, start_sec, end_sec, velocity)
        active = {}  # midi_pitch -> (start_frame, last_frame, max_mag)

        for hz, frame, mag in notes:
            midi_pitch = int(round(librosa.hz_to_midi(hz)))
            if midi_pitch < 21 or midi_pitch > 108:
                continue

            if midi_pitch in active:
                _, last_frame, max_mag = active[midi_pitch]
                if frame - last_frame <= 2:  # 允许 2 帧间隙
                    active[midi_pitch] = (active[midi_pitch][0], frame, max(max_mag, mag))
                    continue
                else:
                    # 结束旧音符
                    start_f, end_f, m = active[midi_pitch]
                    start_sec = start_f * frame_duration
                    end_sec = (end_f + 1) * frame_duration
                    if end_sec - start_sec >= min_note_length:
                        vel = min(127, int(m * 80 + 40))
                        merged_notes.append((midi_pitch, start_sec, end_sec, vel))

            active[midi_pitch] = (frame, frame, mag)

        # 清理剩余活跃音符
        for midi_pitch, (start_f, end_f, m) in active.items():
            start_sec = start_f * frame_duration
            end_sec = (end_f + 1) * frame_duration
            if end_sec - start_sec >= min_note_length:
                vel = min(127, int(m * 80 + 40))
                merged_notes.append((midi_pitch, start_sec, end_sec, vel))

        merged_notes.sort(key=lambda x: x[1])

        # 写 MIDI 文件
        midi = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=0)
        for pitch, start, end, vel in merged_notes:
            note = pretty_midi.Note(velocity=vel, pitch=pitch, start=start, end=end)
            instrument.notes.append(note)
        midi.instruments.append(instrument)

        midi_path.parent.mkdir(parents=True, exist_ok=True)
        midi.write(str(midi_path))

        # 统计
        pitch_values = [n[0] for n in merged_notes]
        pitch_min = min(pitch_values) if pitch_values else 0
        pitch_max = max(pitch_values) if pitch_values else 0

        # 音符预览（前 20 个）
        notes_preview = []
        for pitch, start, end, vel in merged_notes[:20]:
            notes_preview.append({
                "pitch": pitch,
                "start_time": round(start, 3),
                "duration": round(end - start, 3),
                "velocity": vel,
            })

        return {
            "midi_file": str(midi_path),
            "note_count": len(merged_notes),
            "pitch_range": {"low": pitch_min, "high": pitch_max},
            "notes_preview": notes_preview,
        }
    except Exception as e:
        return {"error": f"MIDI 转换失败: {e}"}
