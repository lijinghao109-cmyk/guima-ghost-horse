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
    """用自相似矩阵 + checkerboard kernel 检测段落边界。"""
    import numpy as np
    import librosa
    from scipy.signal import find_peaks

    duration = len(audio) / sr
    if duration < 10:
        return [{"label": "full", "start": 0.0, "end": round(duration, 1)}]

    # 提取 MFCC + Mel 频谱组合特征
    hop = 2048
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20, hop_length=hop)
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop, n_mels=40)
    mel_db = librosa.power_to_db(mel)
    features = np.vstack([mfcc, mel_db])
    features = librosa.util.normalize(features, axis=0)

    # 自相似矩阵
    sim = features.T @ features

    # Checkerboard kernel 新奇度曲线
    kernel_size = 32
    novelty = np.zeros(sim.shape[0])
    for i in range(kernel_size, sim.shape[0] - kernel_size):
        tl = sim[i - kernel_size:i, i - kernel_size:i].mean()
        br = sim[i:i + kernel_size, i:i + kernel_size].mean()
        tr = sim[i - kernel_size:i, i:i + kernel_size].mean()
        bl = sim[i:i + kernel_size, i - kernel_size:i].mean()
        novelty[i] = (tl + br) - (tr + bl)

    novelty = np.maximum(novelty, 0)
    if novelty.max() > 0:
        novelty /= novelty.max()

    # 找峰值（最小段落间隔 15 秒）
    min_distance = max(1, int(15 * sr / hop))
    peaks, _ = find_peaks(novelty, height=0.08, distance=min_distance, prominence=0.03)
    hop_duration = hop / sr
    peak_times = [round(float(p) * hop_duration, 1) for p in peaks]

    # 构建边界，合并过短的尾段（< 8 秒）
    boundary_times = [0.0] + peak_times + [round(duration, 1)]
    if len(boundary_times) > 2 and (boundary_times[-1] - boundary_times[-2]) < 8:
        boundary_times.pop(-2)

    # 限制最多 8 段
    boundary_times = boundary_times[:9]
    if boundary_times[-1] < round(duration, 1):
        boundary_times[-1] = round(duration, 1)

    labels = ["intro", "verse", "chorus", "bridge", "verse", "chorus", "bridge", "outro"]
    sections = []
    for i in range(len(boundary_times) - 1):
        label = labels[i] if i < len(labels) else f"section_{i + 1}"
        sections.append({
            "label": label,
            "start": boundary_times[i],
            "end": boundary_times[i + 1],
        })
    return sections


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
