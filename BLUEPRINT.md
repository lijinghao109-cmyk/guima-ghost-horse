# AIM — Ableton Interact Machine 项目蓝图

> **状态**: 草稿 | **阶段**: 原型验证完成，正式开发启动前
> **最后更新**: 2026-03-28

---

## 0. 一句话定义

> 用自然语言控制 Ableton Live，让音乐人把注意力放在音乐上，而不是 DAW 操作上。

---

## 1. 问题与机会

### 核心痛点

音乐人脑子里有想法，但从"想法"到"能听的声音"之间有一道 DAW 操作的高墙：
建轨道 → 选乐器 → 画 clip → 输入音符 → 调参数 → 播放。
这个过程打断创作状态，尤其对非专业用户更是门槛。

### Jobs-to-be-Done

> "当我脑子里有个音乐 idea 时，我想立刻把它变成能听的东西，而不是花 20 分钟在 DAW 里点鼠标。"

### 差异化定位

| 方案 | 控制权 | 创作自由度 | Ableton 集成 |
|------|--------|-----------|-------------|
| Suno / Udio | ❌ 黑盒生成 | 低 | ❌ |
| AbletonMCP（原始） | ✅ | 低（需手写命令） | ✅ |
| **AIM** | ✅ 完全可控 | 高（自然语言） | ✅ 深度集成 |

### 北极星指标

**Time-to-First-Loop**：从用户描述想法 → 第一次听到 loop 的时间。
目标：原型 ~45s → v1.0 < 20s。

---

## 2. 系统架构

### 2.1 整体架构（C4 Context）

```
┌─────────────────────────────────────────────────────────┐
│                      用户                                │
│              自然语言输入（CLI / 未来 GUI）               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   AIM Core                               │
│                                                         │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │ Conversation │   │ Tool Engine  │   │  Drum Engine │  │
│  │  Manager    │──▶│ (Claude API) │──▶│ (概率鼓机)   │  │
│  └─────────────┘   └──────┬───────┘   └──────┬──────┘  │
│                           │                   │         │
│                    ┌──────▼───────────────────▼──────┐  │
│                    │      Ableton Bridge              │  │
│                    │   (socket client, port 9877)     │  │
│                    └──────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────┘
                              │ TCP socket
┌─────────────────────────────▼───────────────────────────┐
│              Ableton Live + Remote Script                │
└─────────────────────────────────────────────────────────┘
```

### 2.2 目标目录结构

```
ableton-interact-machine/
├── aim/
│   ├── __init__.py
│   ├── main.py              # 入口，CLI 循环
│   ├── conversation.py      # 对话管理，消息历史，撤销
│   ├── tool_engine.py       # 工具定义 + 工具调用执行
│   ├── ableton_bridge.py    # socket 通信层
│   ├── drum_engine.py       # 概率鼓机（从 skill 提炼）
│   ├── prompts.py           # System Prompt + 提示管理
│   └── tools/               # 工具定义（每类一个文件）
│       ├── session_tools.py
│       ├── track_tools.py
│       ├── clip_tools.py
│       └── drum_tools.py    # 概率鼓机工具
├── tests/
│   ├── test_drum_engine.py
│   └── test_ableton_bridge.py
├── aim.py                   # 原型（保留，不动）
├── run.sh
├── .env
├── BLUEPRINT.md             # 本文档
└── CLAUDE.md
```

### 2.3 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `main.py` | CLI 入口，初始化，循环 | conversation |
| `conversation.py` | 消息历史，session 状态，撤销栈 | tool_engine |
| `tool_engine.py` | 工具定义注册，调用路由，结果处理 | ableton_bridge, drum_engine |
| `ableton_bridge.py` | TCP socket，JSON 序列化，超时重试 | — |
| `drum_engine.py` | 概率步进网格，三层随机，风格预设 | — |
| `prompts.py` | System Prompt，动态上下文注入 | — |

---

## 3. 开发阶段规划

### Phase 0 ✅ 原型验证（已完成）
- 单文件 aim.py
- 验证：自然语言 → Claude → Ableton 工具链路通

### Phase 1：基础架构重构
**目标**：把原型拆成可维护的模块结构，不新增功能。

- [ ] 创建 `aim/` 包结构
- [ ] 拆分 `ableton_bridge.py`（socket 层独立）
- [ ] 拆分 `tool_engine.py`（工具定义 + 执行分离）
- [ ] 拆分 `conversation.py`（消息历史管理）
- [ ] 拆分 `prompts.py`（System Prompt）
- [ ] 更新 `run.sh` 入口
- [ ] 验证：功能与原型完全一致

**完成标志**：`python -m aim` 运行效果与 `python aim.py` 完全相同。

### Phase 2：概率鼓机集成
**目标**：让 AIM 生成有"有机感"的鼓组，每次播放都略有不同。

- [ ] 实现 `drum_engine.py`（基于 probabilistic-drum-engine skill）
  - 概率步进网格（6 轨 × 32 步）
  - 三层随机：概率门 + variation + evolution
  - 5 种风格预设（Techno / House / Minimal / Broken / Glitch）
- [ ] 新增工具 `generate_drum_pattern(style, bars, variation)`
- [ ] System Prompt 更新（告知 Claude 何时用新工具）
- [ ] 验证：相同指令每次生成的 MIDI 音符不完全相同

**完成标志**：用户说"lo-fi 风格鼓组"，连续生成 3 次，结果有细微差异但风格一致。

### Phase 3：Session 增强
**目标**：改善对话体验，支持撤销和状态感知。

- [ ] 撤销命令（"撤销上一步" → 调用 Ableton delete/clear）
- [ ] Session 状态显示（当前有几条轨道、什么 BPM）
- [ ] 多轮对话中保持 Ableton 状态同步
- [ ] 错误恢复引导（工具失败时给出建议）

**完成标志**：用户能说"不对，删掉刚才的鼓轨重来"并成功执行。

### Phase 4：工具扩展
**目标**：覆盖更多 Ableton 操作场景。

- [ ] 音频轨支持（导入 sample）
- [ ] 效果链控制（加 Reverb/Delay 并设置参数）
- [ ] 场景（Scene）管理（多个 loop 切换）
- [ ] 混音参数（Volume / Pan / Send）
- [ ] Clip 演化（基于 evolution 算法跨 scene 突变）

### Phase 5：体验与分发（远期）
- Web UI / Electron 桌面应用
- 预设库（用户可保存/分享风格）
- 插件化工具（第三方工具接入）

---

## 4. 工具 API 设计

### 现有工具（Phase 1 保持不变）

```
get_session_info()
set_tempo(tempo)
create_midi_track(index?)
set_track_name(track_index, name)
load_instrument_or_effect(track_index, uri)
create_clip(track_index, clip_index, length?)
add_notes_to_clip(track_index, clip_index, notes[])
fire_clip(track_index, clip_index)
```

### Phase 2 新增工具

```
generate_drum_pattern(
    track_index: int,
    clip_index: int,
    style: "techno" | "house" | "minimal" | "broken" | "glitch",
    bars: int = 2,
    variation: float = 0.3   # 0=机械, 1=混乱, 0.3=自然
) → writes notes directly to clip
```

### Phase 3 新增工具

```
undo_last_action()                          # 撤销上一步
clear_track(track_index)                   # 清空轨道
get_track_info(track_index)                # 获取单轨状态
delete_track(track_index)                  # 删除轨道
```

---

## 5. 关键设计决策（ADR）

### ADR-001：保留 TCP Socket 而非 OSC
**决策**：继续用 TCP socket (port 9877)，不切换到 OSC。
**原因**：原有 Remote Script 基于 socket 实现，重写成本高；socket 支持双向复杂 JSON，OSC 对嵌套数据支持弱。
**风险**：单连接串行，并发工具调用会排队。Phase 4 可评估连接池。

### ADR-002：drum_engine 在客户端运行，不在 Ableton 侧
**决策**：概率算法在 Python 侧计算，最终结果以静态 MIDI 音符写入 Ableton。
**原因**：无需修改 Remote Script；调试方便；逻辑可单测。
**取舍**：无法实现实时演化（播放中突变）。Phase 4 可通过 Max for Live 设备实现实时版本。

### ADR-003：单文件原型永久保留
**决策**：`aim.py` 原型不删除，重构后的代码放在 `aim/` 包。
**原因**：原型是验证过的参照基准，重构时可对比行为。

---

## 6. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Ableton Remote Script API 变更 | 低 | 高 | 抽象 bridge 层，接口稳定 |
| Claude API 工具调用格式变更 | 低 | 中 | 版本锁定 anthropic SDK |
| 生成的 MIDI 音符 Ableton 不接受 | 中 | 中 | 单测覆盖边界值，加参数校验 |
| System Prompt 过长导致推理质量下降 | 中 | 中 | 模块化 prompt，按需注入上下文 |
| socket 超时在慢操作（加载乐器）时失败 | 高 | 低 | 已有 15s 超时，Phase 1 改为可配置 |

---

## 7. 成功标准

| 阶段 | 指标 | 目标值 |
|------|------|--------|
| Phase 1 | 重构后功能回归 | 100% 行为一致 |
| Phase 2 | 鼓机生成有机感 | 连续生成差异率 > 15% |
| Phase 2 | Time-to-First-Loop | < 30s |
| Phase 3 | 撤销成功率 | > 90% |
| Phase 4 | 工具覆盖率 | 覆盖 Ableton 80% 常用操作 |

---

## 8. 开放问题

- [ ] Remote Script 侧是否需要修改以支持 Phase 3 的撤销？
- [ ] Phase 2 的 evolution（跨 scene 突变）算法是否值得在 v1 实现，还是留到 Phase 4？
- [ ] 是否需要支持多用户/多 Ableton 实例？（当前假设单机单实例）
- [ ] System Prompt 的音乐规则（URI、BPM 范围等）是否应该外置为配置文件？

---

*本文档随项目演进持续更新。每个 Phase 完成后更新对应状态。*
