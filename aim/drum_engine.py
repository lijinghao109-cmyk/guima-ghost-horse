"""
DrumEngine — 概率鼓机引擎（Phase 2 实现）。

Phase 1：接口 skeleton，generate() 抛出 NotImplementedError。
Phase 2：实现三层随机性系统（概率门 + variation + evolution）和风格预设。

设计参考（Phase 2 开发者请阅读）：
────────────────────────────────────────────────────────────────
数据结构：6 轨 × 32 步概率网格
  Step = { active: bool, probability: float, velocity: float, micro_shift: float }
  轨道：Kick(36), Snare(38), ClosedHat(42), OpenHat(46), Clap(39), Perc(75)

三层随机：
  Layer 1 — 概率门（per-step）：random() > step.probability → 跳过
  Layer 2 — Variation（per-event）：velocity ±30%，timing ±10% 步长
  Layer 3 — Evolution（per-N-bars）：有界随机游走，drift 上限 maxDrift=0.3

风格向量（StyleVector）：
  density, syncopation, swing, glitch_factor, harmonic_stability, evolution_rate

参数映射：
  velocity_variance = syncopation × 0.5
  timing_jitter     = syncopation × 0.3
  ghost_density     = glitch_factor

底鼓模板：FourOnFloor, BrokenGrid, Asymmetric
────────────────────────────────────────────────────────────────
"""

from __future__ import annotations


# 风格预设（Phase 2 填充实际 StyleVector 值）
STYLE_PRESETS: dict[str, dict] = {
    "techno": {},
    "house": {},
    "minimal": {},
    "broken": {},
    "glitch": {},
}

# MIDI 音符映射（Phase 2 直接使用）
TRACK_NOTES: dict[str, int] = {
    "kick": 36,
    "snare": 38,
    "closed_hat": 42,
    "open_hat": 46,
    "clap": 39,
    "perc": 75,
}


class DrumEngine:
    """概率步进鼓机。

    Phase 1：接口占位。
    Phase 2：实现 generate()，填充三层随机逻辑和风格预设。
    """

    def __init__(self, variation: float = 0.3) -> None:
        """
        Args:
            variation: 随机程度。0.0 = 机械精确，1.0 = 完全随机，0.3 = 自然人感。
        """
        self.variation = variation

    def generate(
        self,
        style: str,
        bars: int = 2,
    ) -> list[dict]:
        """生成鼓组 MIDI 音符列表。

        Args:
            style: 风格名称，见 STYLE_PRESETS 的 key。
            bars:  小节数，默认 2（= 8 拍）。

        Returns:
            符合 add_notes_to_clip 格式的 notes 列表：
            [{"pitch": int, "start_time": float, "duration": float,
              "velocity": int, "mute": bool}, ...]

        Raises:
            NotImplementedError: Phase 1 占位，Phase 2 实现。
        """
        raise NotImplementedError(
            "DrumEngine.generate() 将在 Phase 2 实现。"
            "当前请使用 add_notes_to_clip 手动传入音符。"
        )
