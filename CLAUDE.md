# AIM — Ableton Interact Machine

## 当前阶段
**Phase 2.5 实施中：音频分析桥梁（代码完成，待端到端验证）。**

## 项目结构
- `aim/` — 模块化包：main, conversation, tool_engine, ableton_bridge, prompts, tools/, analysis/
- `aim/tools/` — 8 个工具文件：session, track, clip, mixer, device, transport, management, analysis
- `aim/analysis/` — 音频分析执行层：_validate, audio_analysis(librosa), midi_conversion(basic-pitch), stem_separation(demucs)
- `aim.py` — 原型（保留作参照，ADR-003）
- `run.sh` — 启动脚本
- `.env` — API Key（已 gitignore）
- `pyproject.toml` — 包定义 + 可选依赖组
- `tests/` — 单元测试（37 tests）

## 技术栈
- Python 3，anthropic SDK
- TCP socket → localhost:9877 → Ableton Remote Script（补丁版，ADR-008）
- 模型：claude-sonnet-4-6
- 音频分析：essentia（BPM/调性/和弦/节拍）, basic-pitch（音频→MIDI）, demucs（stem分离）

## ⚠️ 许可证风险
音频分析依赖 **essentia（AGPL-3.0）**，具有传染性。个人使用无限制；对外分发时整个项目必须以 AGPL-3.0 发布。详见 BLUEPRINT.md ADR-009。

## 已验证能力
- 自然语言 → Claude 推理 → 工具调用 → Ableton 执行
- 29 个工具：session(2) + 轨道(5) + 设备(3) + clip(6) + 混音(4) + 传输(3) + 音频分析(6)
- LOCAL_TOOLS 本地执行路径（分析工具不经过 Ableton socket）

## 开发蓝图
见 [BLUEPRINT.md](BLUEPRINT.md)

## 下一步
- 安装 librosa 并端到端验证分析工具
- 安装 basic-pitch / demucs 验证转换和分离
- Phase 3：录音 + 高级路由
