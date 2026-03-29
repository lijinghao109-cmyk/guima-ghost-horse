"""demucs stem 分离 + 音频加载桥接。"""

from __future__ import annotations

from pathlib import Path

from aim.analysis._validate import validate_audio_file


def run_separate_stems(params: dict) -> dict:
    """用 demucs 将音频分离为 4 个 stem（vocals/drums/bass/other）。"""
    try:
        import demucs.separate
    except ImportError:
        return {"error": "demucs 未安装。运行: pip install 'aim[stems]'"}

    file_path = params.get("file_path", "")
    err = validate_audio_file(file_path)
    if err:
        return {"error": err}

    input_path = Path(file_path)
    output_dir = params.get("output_dir")
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = input_path.parent / "stems"

    model = params.get("model", "htdemucs")

    try:
        print("  ⏳ 正在分离 stems（约 30-60 秒）...")
        # demucs 的 CLI 入口
        args = [
            "--out", str(out_path),
            "--name", model,
            "-n", model,
            str(file_path),
        ]
        demucs.separate.main(args)

        # demucs 输出结构: output_dir/model_name/track_name/stem.wav
        track_name = input_path.stem
        stem_dir = out_path / model / track_name

        stems = {}
        for stem_name in ["vocals", "drums", "bass", "other"]:
            stem_file = stem_dir / f"{stem_name}.wav"
            if stem_file.exists():
                stems[stem_name] = str(stem_file)
            else:
                stems[stem_name] = None

        # 获取时长
        duration = None
        try:
            import librosa
            y, sr = librosa.load(file_path, duration=5)  # 只加载 5 秒来获取信息
            duration = round(librosa.get_duration(filename=file_path), 1)
        except Exception:
            pass

        result = {
            "stems": stems,
            "model_used": model,
            "output_dir": str(stem_dir),
        }
        if duration is not None:
            result["duration_seconds"] = duration
        return result
    except Exception as e:
        return {"error": f"stem 分离失败: {e}"}


def run_load_audio_to_track(params: dict) -> dict:
    """将音频文件加载到 Ableton 音频轨。

    Phase 2.5：返回手动操作指引。
    后续版本可扩展为通过 Remote Script 自动加载。
    """
    file_path = params.get("file_path", "")
    track_index = params.get("track_index")
    clip_index = params.get("clip_index", 0)

    if not file_path:
        return {"error": "file_path 参数缺失"}
    if track_index is None:
        return {"error": "track_index 参数缺失"}

    p = Path(file_path)
    if not p.exists():
        return {"error": f"文件不存在: {file_path}"}

    return {
        "action_required": "manual_load",
        "file_path": str(p.resolve()),
        "file_name": p.name,
        "track_index": track_index,
        "clip_index": clip_index,
        "instruction": f"请将 {p.name} 拖入 Ableton 中第 {track_index + 1} 条轨道的第 {clip_index + 1} 个 clip 槽",
    }
