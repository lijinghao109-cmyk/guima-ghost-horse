# AIM — Ableton Interact Machine

## 当前阶段
**原型验证完成，正式架构尚未开始。**

## 原型结构（单文件）
- `aim.py` — 全部逻辑：socket 通信 + 工具定义 + System Prompt + 主对话循环
- `run.sh` — 启动脚本
- `.env` — API Key（已 gitignore）

## 技术栈
- Python 3，anthropic SDK
- TCP socket → localhost:9877 → Ableton Remote Script
- 模型：claude-sonnet-4-6

## 已验证能力
- 自然语言 → Claude 推理 → 工具调用 → Ableton 执行
- 8 个工具：get_session_info / set_tempo / create_midi_track / set_track_name / load_instrument_or_effect / create_clip / add_notes_to_clip / fire_clip

## 开发蓝图
见 [BLUEPRINT.md](BLUEPRINT.md)

## 下一步（Phase 1）
架构重构：将 aim.py 拆分为 aim/ 包结构，不新增功能。
