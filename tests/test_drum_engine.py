"""
DrumEngine 单元测试。

Phase 1：验证 skeleton 行为（NotImplementedError）。
Phase 2：在此文件补充真实生成逻辑的测试。
"""

import unittest

from aim.drum_engine import DrumEngine, STYLE_PRESETS, TRACK_NOTES


class TestDrumEnginePhase1(unittest.TestCase):

    def test_generate_raises_not_implemented(self):
        """Phase 1: generate() 抛出 NotImplementedError。"""
        engine = DrumEngine()
        with self.assertRaises(NotImplementedError):
            engine.generate(style="techno")

    def test_all_style_presets_exist(self):
        """5 种风格预设 key 都存在。"""
        expected = {"techno", "house", "minimal", "broken", "glitch"}
        self.assertEqual(set(STYLE_PRESETS.keys()), expected)

    def test_track_notes_has_all_tracks(self):
        """6 个鼓轨都有 MIDI 映射。"""
        expected = {"kick", "snare", "closed_hat", "open_hat", "clap", "perc"}
        self.assertEqual(set(TRACK_NOTES.keys()), expected)

    def test_variation_stored_on_init(self):
        """variation 参数被正确存储。"""
        engine = DrumEngine(variation=0.7)
        self.assertEqual(engine.variation, 0.7)


# ── Phase 2 测试预留（取消注释后填充实现）─────────────────────────────────────
#
# class TestDrumEnginePhase2(unittest.TestCase):
#
#     def test_generate_returns_list_of_notes(self):
#         engine = DrumEngine(variation=0.0)
#         notes = engine.generate(style="techno", bars=2)
#         self.assertIsInstance(notes, list)
#         self.assertGreater(len(notes), 0)
#
#     def test_notes_have_required_fields(self):
#         engine = DrumEngine(variation=0.0)
#         notes = engine.generate(style="house", bars=2)
#         required = {"pitch", "start_time", "duration", "velocity", "mute"}
#         for note in notes:
#             self.assertTrue(required.issubset(note.keys()))
#
#     def test_same_style_different_variation_produces_different_output(self):
#         """variation > 0 时，两次生成结果不完全相同（概率性，多次运行偶发失败可接受）。"""
#         engine = DrumEngine(variation=0.9)
#         notes_a = engine.generate(style="glitch", bars=2)
#         notes_b = engine.generate(style="glitch", bars=2)
#         velocities_a = [n["velocity"] for n in notes_a]
#         velocities_b = [n["velocity"] for n in notes_b]
#         self.assertNotEqual(velocities_a, velocities_b)


if __name__ == "__main__":
    unittest.main()
