"""essentia 音频分析 — analyze_audio, analyze_beats, analyze_stem。

⚠️ 许可证警告：essentia 使用 AGPL-3.0 许可证，具有传染性。
如果 AIM 对外分发，整个项目必须以 AGPL-3.0 发布。
详见 BLUEPRINT.md ADR-009。
"""

from __future__ import annotations

from aim.analysis._validate import validate_audio_file

_IMPORT_ERROR_MSG = "essentia 未安装。运行: pip install 'aim[analysis]'"


# ── 内部工具 ──────────────────────────────────────────────────────────────────


def _load_audio(file_path: str):
    """用 essentia MonoLoader 加载音频，返回 (audio_array, sample_rate)。"""
    from essentia.standard import MonoLoader

    # MonoLoader 默认 44100 Hz mono
    loader = MonoLoader(filename=file_path)
    audio = loader()
    return audio, 44100


def _detect_key(audio) -> tuple[str, str, float]:
    """用 essentia KeyExtractor 检测调性。

    Returns: (key, scale, strength)  e.g. ("C", "minor", 0.85)
    """
    from essentia.standard import KeyExtractor

    key_extractor = KeyExtractor()
    key, scale, strength = key_extractor(audio)
    return key, scale, round(float(strength), 2)


def _detect_chords(audio) -> list[str]:
    """用 essentia 提取和弦进行。"""
    from essentia.standard import (
        FrameGenerator, Windowing, Spectrum,
        SpectralPeaks, HPCP, ChordsDetection,
    )
    import numpy as np

    frame_size = 8192
    hop_size = 4096

    hpcps = []
    for frame in FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
        windowed = Windowing(type="blackmanharris62")(frame)
        spectrum = Spectrum()(windowed)
        freqs, mags = SpectralPeaks(
            minFrequency=40, maxFrequency=5000, maxPeaks=100,
            sampleRate=44100, magnitudeThreshold=0.001,
        )(spectrum)
        hpcp = HPCP(sampleRate=44100)(freqs, mags)
        hpcps.append(hpcp)

    if not hpcps:
        return []

    hpcps_array = np.array(hpcps)
    chords_detection = ChordsDetection(hopSize=hop_size, sampleRate=44100)
    chords, strengths = chords_detection(hpcps_array)

    # 去重保留顺序，取前 8 个独特和弦
    seen = set()
    unique = []
    for c in chords:
        if c not in seen and c != "N":  # "N" = no chord detected
            seen.add(c)
            unique.append(c)
        if len(unique) >= 8:
            break
    return unique


def _compute_energy_curve(audio, n_points: int = 8) -> list[float]:
    """计算能量曲线（归一化到 0-1）。"""
    import numpy as np

    # 分段计算 RMS
    chunk_size = max(1, len(audio) // n_points)
    curve = []
    for i in range(n_points):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(audio))
        rms = float(np.sqrt(np.mean(audio[start:end] ** 2)))
        curve.append(rms)
    # 归一化
    max_val = max(curve) if curve else 1.0
    if max_val > 0:
        curve = [round(v / max_val, 2) for v in curve]
    return curve


def _estimate_sections(audio, sr: int = 44100) -> list[dict]:
    """用 essentia SBic 估计曲式段落边界。"""
    import numpy as np
    from essentia.standard import (
        FrameGenerator, Windowing, Spectrum, MFCC, SBic,
    )

    duration = len(audio) / sr

    # 提取 MFCC 特征矩阵
    mfccs = []
    for frame in FrameGenerator(audio, frameSize=2048, hopSize=1024):
        windowed = Windowing(type="hann")(frame)
        spectrum = Spectrum()(windowed)
        _, mfcc_coeffs = MFCC(numberCoefficients=13)(spectrum)
        mfccs.append(mfcc_coeffs)

    if len(mfccs) < 10:
        # 太短，返回单段
        return [{"label": "full", "start": 0.0, "end": round(duration, 1)}]

    mfcc_matrix = np.array(mfccs)

    try:
        sbic = SBic(minLength=10, inc1=60, inc2=20)
        boundaries = sbic(mfcc_matrix)
        # boundaries 是帧索引，转为秒
        hop_duration = 1024 / sr
        boundary_times = sorted(set([0.0] + [round(float(b) * hop_duration, 1) for b in boundaries] + [round(duration, 1)]))
    except Exception:
        # SBic 失败时回退到均分
        n_segments = min(8, max(2, int(duration / 15)))
        segment_len = duration / n_segments
        boundary_times = [round(i * segment_len, 1) for i in range(n_segments + 1)]

    labels = ["intro", "verse", "chorus", "bridge", "verse", "chorus", "bridge", "outro"]
    sections = []
    for i in range(len(boundary_times) - 1):
        label = labels[i] if i < len(labels) else f"section_{i+1}"
        sections.append({
            "label": label,
            "start": boundary_times[i],
            "end": boundary_times[i + 1],
        })
    return sections[:8]  # 最多 8 段


# ── 公开函数 ──────────────────────────────────────────────────────────────────


def run_analyze_audio(params: dict) -> dict:
    """提取音频的 BPM、调性、和弦进行、曲式结构、能量曲线。"""
    try:
        import essentia  # noqa: F401
        from essentia.standard import RhythmExtractor2013
    except ImportError:
        return {"error": _IMPORT_ERROR_MSG}

    file_path = params.get("file_path", "")
    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    try:
        audio, sr = _load_audio(file_path)
        duration = round(len(audio) / sr, 1)

        # BPM + beats
        rhythm = RhythmExtractor2013()
        bpm, beats, beats_confidence, _, _ = rhythm(audio)

        # 调性
        key, scale, key_strength = _detect_key(audio)

        # 和弦
        chords = _detect_chords(audio)

        # 曲式结构
        sections = _estimate_sections(audio, sr)

        # 能量曲线
        energy = _compute_energy_curve(audio)

        return {
            "bpm": round(float(bpm), 1),
            "key": f"{key} {scale}",
            "key_confidence": key_strength,
            "duration_seconds": duration,
            "chord_progression": chords,
            "sections": sections,
            "energy_curve": energy,
        }
    except Exception as e:
        return {"error": f"分析失败: {e}"}


def run_analyze_beats(params: dict) -> dict:
    """提取详细节拍网格、onset 强度、groove 偏移。"""
    try:
        import essentia  # noqa: F401
        from essentia.standard import RhythmExtractor2013, OnsetRate
    except ImportError:
        return {"error": _IMPORT_ERROR_MSG}

    file_path = params.get("file_path", "")
    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    start_time = params.get("start_time")
    end_time = params.get("end_time")

    try:
        audio, sr = _load_audio(file_path)

        # 截取片段
        if start_time is not None or end_time is not None:
            start_sample = int((start_time or 0) * sr)
            end_sample = int((end_time or len(audio) / sr) * sr)
            audio = audio[start_sample:end_sample]

        # BPM + beats
        rhythm = RhythmExtractor2013()
        bpm, beat_times, beats_confidence, _, _ = rhythm(audio)
        bpm = float(bpm)

        # onset 强度：用每拍附近的音频能量估算
        import numpy as np
        onset_strengths = []
        half_window = int(0.05 * sr)  # 50ms 窗口
        for bt in beat_times:
            center = int(float(bt) * sr)
            start_s = max(0, center - half_window)
            end_s = min(len(audio), center + half_window)
            rms = float(np.sqrt(np.mean(audio[start_s:end_s] ** 2)))
            onset_strengths.append(rms)
        max_rms = max(onset_strengths) if onset_strengths else 1.0
        if max_rms > 0:
            onset_strengths = [round(v / max_rms, 2) for v in onset_strengths]

        # groove 偏移
        if len(beat_times) >= 2:
            ideal_interval = 60.0 / bpm
            groove_offsets = []
            for i, bt in enumerate(beat_times):
                ideal_time = float(beat_times[0]) + i * ideal_interval
                offset_ms = round((float(bt) - ideal_time) * 1000, 1)
                groove_offsets.append(offset_ms)
        else:
            groove_offsets = []

        max_beats = 32
        return {
            "bpm": round(bpm, 1),
            "total_beats": len(beat_times),
            "beats": [round(float(b), 3) for b in beat_times[:max_beats]],
            "onset_strengths": onset_strengths[:max_beats],
            "groove_offset_ms": groove_offsets[:max_beats],
        }
    except Exception as e:
        return {"error": f"节拍分析失败: {e}"}


def run_analyze_stem(params: dict) -> dict:
    """对单个 stem 进行类型感知分析。"""
    try:
        import essentia  # noqa: F401
        from essentia.standard import FrameGenerator, Windowing
    except ImportError:
        return {"error": _IMPORT_ERROR_MSG}

    file_path = params.get("file_path", "")
    stem_type = params.get("stem_type", "")

    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    valid_types = {"vocals", "drums", "bass", "other"}
    if stem_type not in valid_types:
        return {"error": f"stem_type 必须是 {valid_types} 之一，收到: '{stem_type}'"}

    try:
        import numpy as np

        audio, sr = _load_audio(file_path)
        duration = round(len(audio) / sr, 1)
        result = {"stem_type": stem_type, "duration_seconds": duration}

        if stem_type == "drums":
            # 鼓：用 RhythmExtractor2013 提取节拍 + 用能量做 onset 密度
            from essentia.standard import RhythmExtractor2013
            rhythm = RhythmExtractor2013()
            bpm, beats, _, _, _ = rhythm(audio)

            # 用能量阈值检测 onset
            hop = 512
            frame_size = 1024
            energies = []
            for frame in FrameGenerator(audio, frameSize=frame_size, hopSize=hop):
                energies.append(float(np.sqrt(np.mean(frame ** 2))))
            energies = np.array(energies)
            threshold = np.mean(energies) + 1.5 * np.std(energies)
            onset_frames = np.where(energies > threshold)[0]
            # 去除过近的 onset（最小间隔 50ms）
            min_gap = int(0.05 * sr / hop)
            filtered = [onset_frames[0]] if len(onset_frames) > 0 else []
            for f in onset_frames[1:]:
                if f - filtered[-1] >= min_gap:
                    filtered.append(f)
            onset_times_sec = [round(float(f) * hop / sr, 3) for f in filtered]

            result["bpm"] = round(float(bpm), 1)
            result["onset_count"] = len(onset_times_sec)
            result["onsets"] = [{"time": t} for t in onset_times_sec[:64]]
            result["density_per_second"] = round(len(onset_times_sec) / max(duration, 0.1), 1)

        elif stem_type == "bass":
            # 贝斯：调性 + 主要音高
            key, scale, _ = _detect_key(audio)
            result["key"] = f"{key} {scale}"

            # 用 HPCP 找主要音高
            from essentia.standard import Spectrum, SpectralPeaks, HPCP
            _KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

            hpcps = []
            for frame in FrameGenerator(audio, frameSize=4096, hopSize=2048):
                windowed = Windowing(type="hann")(frame)
                spectrum = Spectrum()(windowed)
                freqs, mags = SpectralPeaks(
                    minFrequency=30, maxFrequency=500, sampleRate=sr,
                )(spectrum)
                hpcp = HPCP(sampleRate=sr)(freqs, mags)
                hpcps.append(hpcp)

            if hpcps:
                hpcp_mean = np.mean(np.array(hpcps), axis=0)
                top_indices = np.argsort(hpcp_mean)[::-1][:5]
                result["dominant_notes"] = [_KEY_NAMES[int(i)] for i in top_indices]

            # onset 时间（能量阈值法）
            hop = 512
            frame_size = 1024
            energies = []
            for frame in FrameGenerator(audio, frameSize=frame_size, hopSize=hop):
                energies.append(float(np.sqrt(np.mean(frame ** 2))))
            energies = np.array(energies)
            threshold = np.mean(energies) + 1.5 * np.std(energies)
            onset_frames = np.where(energies > threshold)[0]
            min_gap = int(0.05 * sr / hop)
            filtered = [onset_frames[0]] if len(onset_frames) > 0 else []
            for f in onset_frames[1:]:
                if f - filtered[-1] >= min_gap:
                    filtered.append(f)
            result["note_onsets"] = [round(float(f) * hop / sr, 3) for f in filtered[:32]]

        elif stem_type == "vocals":
            # 人声：调性 + 音高轮廓
            key, scale, _ = _detect_key(audio)
            result["key"] = f"{key} {scale}"

            from essentia.standard import PitchYinFFT
            pitch_extractor = PitchYinFFT(frameSize=2048, sampleRate=sr)
            pitches = []
            for frame in FrameGenerator(audio, frameSize=2048, hopSize=1024):
                pitch, confidence = pitch_extractor(frame)
                if confidence > 0.5 and 50 < pitch < 2000:
                    pitches.append(float(pitch))

            # 降采样到 32 点
            if pitches:
                n_points = min(32, len(pitches))
                step = max(1, len(pitches) // n_points)
                result["pitch_contour_hz"] = [round(pitches[i * step], 1) for i in range(n_points)]
            else:
                result["pitch_contour_hz"] = []

        else:  # "other"
            key, scale, _ = _detect_key(audio)
            chords = _detect_chords(audio)
            result["key"] = f"{key} {scale}"
            result["chord_progression"] = chords

        return result
    except Exception as e:
        return {"error": f"stem 分析失败: {e}"}
