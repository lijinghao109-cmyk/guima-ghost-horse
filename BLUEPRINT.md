# AIM — Ableton Interact Machine 项目蓝图

> **状态**: 活跃 | **阶段**: Phase 2 完成，Phase 2.5 进行中
> **最后更新**: 2026-03-29

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
│  ┌─────────────┐   ┌──────────────┐                     │
│  │ Conversation │   │ Tool Engine  │                     │
│  │  Manager    │──▶│ (Claude API) │                     │
│  └─────────────┘   └──────┬───────┘                     │
│                           │                             │
│                    ┌──────▼──────────────────────────┐  │
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
│   ├── tool_engine.py       # 工具调用路由 + 执行
│   ├── ableton_bridge.py    # socket 通信层
│   ├── prompts.py           # System Prompt + 提示管理
│   ├── analysis/            # 音频分析桥梁（Phase 2.5）
│   │   ├── _validate.py     # 文件校验
│   │   ├── audio_analysis.py # librosa 分析
│   │   ├── midi_conversion.py # basic-pitch 转换
│   │   └── stem_separation.py # demucs 分离
│   └── tools/               # 工具定义（每类一个文件）
│       ├── session_tools.py
│       ├── track_tools.py
│       ├── clip_tools.py
│       ├── mixer_tools.py
│       ├── device_tools.py
│       ├── transport_tools.py
│       ├── management_tools.py
│       └── analysis_tools.py
├── tests/
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
| `conversation.py` | 消息历史，session 状态，撤销栈 | — |
| `tool_engine.py` | 工具定义注册，调用路由，结果处理 | ableton_bridge, prompts, tools; conversation（运行时注入） |
| `ableton_bridge.py` | TCP socket，JSON 序列化，超时重试 | — |
| `prompts.py` | System Prompt，动态上下文注入 | — |

---

## 3. 开发阶段规划

### Phase 0 ✅ 原型验证（已完成）
- 单文件 aim.py
- 验证：自然语言 → Claude → Ableton 工具链路通

### Phase 1 ✅ 基础架构重构（已完成，2026-03-28）
**目标**：把原型拆成可维护的模块结构，不新增功能。

- [x] 创建 `aim/` 包结构
- [x] 拆分 `ableton_bridge.py`（socket 层独立）
- [x] 拆分 `tool_engine.py`（工具定义 + 执行分离）
- [x] 拆分 `conversation.py`（消息历史管理）
- [x] 拆分 `prompts.py`（System Prompt）
- [x] 更新 `run.sh` 入口
- [x] 验证：功能与原型完全一致

**完成标志**：`python -m aim` 运行效果与 `python aim.py` 完全相同。 ✅

### Phase 2：工具扩展 + Prompt 优化
**目标**：采用社区补丁版 Remote Script，将工具从 8 个扩展到 23 个，同时重写 System Prompt 为原则性音乐指导。覆盖声音设计、混音、编排、律动、一致性五个品质维度。

- [x] 清理 Phase 1 遗留的 drum_engine.py 骨架和 drum_tools.py 占位文件
- [ ] 采用补丁版 Remote Script（ADR-008）
- [ ] 新增 15 个工具定义（mixer/device/transport/management 四个文件）
- [ ] 更新 tool_engine.py（per-tool 截断限制 + 值域钳制）
- [ ] 重写 System Prompt（从硬编码模板 → 原则性音乐指导）
- [ ] 端到端验证：多种风格描述均能生成含声音设计和混音的高质量 loop

**完成标志**：用户描述任意风格，Claude 能建轨 → 选乐器 → 调参数 → 写音符 → 混音，全流程自主完成。

### Phase 2.5：音频分析桥梁（Audio Analysis Bridge）
**目标**：让 Claude 能分析参考音轨，从中借鉴、复刻、解构重组或采样。集成开源音频分析工具作为语言模型与音频之间的桥梁。

- [x] 创建 `aim/analysis/` 包（`_validate.py`, `audio_analysis.py`, `midi_conversion.py`, `stem_separation.py`）
- [x] 新增 6 个工具定义（`aim/tools/analysis_tools.py`）
- [x] `tool_engine.py` 新增 `LOCAL_TOOLS` 本地执行路径（ADR-009）
- [x] System Prompt 追加分析工具和参考工作流
- [x] 单元测试（37 tests 全通过）
- [x] 创建 `pyproject.toml`（可选依赖组：analysis/midi/stems）
- [ ] 安装 librosa 并端到端验证 analyze_audio
- [ ] 安装 basic-pitch 并端到端验证 audio_to_midi
- [ ] 安装 demucs 并端到端验证 separate_stems

**完成标志**：用户提供参考音轨，Claude 分析后以此为基准创作；或分离 stems 后选择性重建。

### Phase 3：录音 + 高级路由 + Session 状态
**目标**：支持录音工作流和动态状态感知。

- [ ] 录音工具（start_recording, stop_recording, set_track_arm, set_track_monitor）
- [ ] 路由工具（set_track_input_routing, get_track_routing_info）
- [ ] Session 状态动态注入（build_system_prompt(session_context) 实现）
- [ ] 错误恢复引导

**完成标志**：用户能通过自然语言录制外部音频输入。

### Phase 4：场景管理 + 实时演化
**目标**：多 loop 切换和跨 scene 演化。

- [ ] Scene 创建/命名/触发/删除
- [ ] Send 量控制
- [ ] 自动化曲线（如 Remote Script 支持）
- [ ] Max for Live 集成（实时演化，可选）

### Phase 5：体验与分发（远期）
- Web UI / Electron 桌面应用
- 预设库（用户可保存/分享风格）
- 插件化工具（第三方工具接入）

---

## 4. 工具 API 设计

### Phase 2 工具（23 个）

**Session（2）**
```
get_session_info()
set_tempo(tempo)
```

**轨道（5）**
```
create_midi_track(index?)
create_audio_track(index?)
set_track_name(track_index, name)
get_track_info(track_index)
delete_track(track_index)
```

**乐器/设备（3）**
```
load_instrument_or_effect(track_index, uri)
get_device_parameters(track_index, device_index)
set_device_parameter(track_index, device_index, parameter_name, value)
```

**Clip（6）**
```
create_clip(track_index, clip_index, length?)
add_notes_to_clip(track_index, clip_index, notes[])
get_clip_notes(track_index, clip_index)
delete_clip(track_index, clip_index)
fire_clip(track_index, clip_index)
stop_clip(track_index, clip_index)
```

**混音（4）**
```
set_track_volume(track_index, volume)       # 0.0~1.0
set_track_panning(track_index, panning)     # -1.0~1.0
set_track_mute(track_index, mute)
set_track_solo(track_index, solo)
```

**传输（3）**
```
start_playback()
stop_playback()
back_to_arrangement()
```

### Phase 2.5 音频分析工具（6）

**分析（3）**
```
analyze_audio(file_path)                   # BPM/调性/和弦/结构/能量曲线
analyze_beats(file_path, start?, end?)     # 节拍网格/onset/groove偏移
analyze_stem(file_path, stem_type)         # 类型感知 stem 分析
```

**转换（1）**
```
audio_to_midi(file_path, output_path?)     # 音频→MIDI（basic-pitch）
```

**分离（1）**
```
separate_stems(file_path, output_dir?)     # 4-stem 分离（demucs）
```

**加载（1）**
```
load_audio_to_track(file_path, track_index, clip_index?)  # 音频→Ableton轨道
```

### Phase 3 新增工具

```
start_recording()                          # 开始录音
stop_recording()                           # 停止录音
set_track_arm(track_index, arm)            # 录音准备
set_track_monitor(track_index, state)      # 监听模式（0=In, 1=Auto, 2=Off）
set_track_input_routing(track_index, ...)  # 输入路由
get_track_routing_info(track_index)        # 查看路由信息
```

---

## 5. 关键设计决策（ADR）

### ADR-001：保留 TCP Socket 而非 OSC
**决策**：继续用 TCP socket (port 9877)，不切换到 OSC。
**原因**：原有 Remote Script 基于 socket 实现，重写成本高；socket 支持双向复杂 JSON，OSC 对嵌套数据支持弱。
**风险**：单连接串行，并发工具调用会排队。Phase 4 可评估连接池。

### ADR-002：~~drum_engine 在客户端运行~~ → 已被 ADR-007 取代
**原决策**：概率算法在 Python 侧计算，最终结果以静态 MIDI 音符写入 Ableton。
**废弃原因**：决定不实现客户端概率鼓机引擎，所有音乐创作由 Claude 直接推理。见 ADR-007。

### ADR-003：单文件原型永久保留
**决策**：`aim.py` 原型不删除，重构后的代码放在 `aim/` 包。
**原因**：原型是验证过的参照基准，重构时可对比行为。

### ADR-004：声明式工具路由（COMMAND_MAP）
**决策**：工具路由使用声明式字典 `COMMAND_MAP`，映射 `tool_name → (socket_command, param_transformer)`。无匹配时透传工具名和参数到 bridge。
**原因**：新增工具只需加一条字典记录，无需修改控制流；默认透传意味着 Claude 工具名与 socket 命令同名时零配置。
**取舍**：不如插件系统灵活，但通过 Phase 4 均不需要更复杂的机制。

### ADR-005：从 Phase 1 开始记录操作日志
**决策**：所有成功的工具调用立即通过 `conversation.log_action()` 记入 `_action_log`，即使撤销功能要到 Phase 3 才实现。
**原因**：避免后期改造日志基础设施；零运行时成本（仅 append to list）；附带提供审计跟踪。
**取舍**：日志只写不读，会在会话期间无限增长。对 CLI 会话生命周期（分钟级）而言可接受。

### ADR-006：错误以 Dict 传播，不抛异常
**决策**：`ableton_bridge.call()` 失败时返回 `{"error": str}` 而非抛出异常。
**原因**：Claude 工具结果必须是字符串；错误 dict 自然流入 `execute_tool()` 的 `"error: ..."` 字符串格式化管线，无需 try/except 包裹每次调用。
**取舍**：调用方必须检查 `"error"` 键；无异常栈轨迹可用于调试（Phase 4 可加 logging 模块缓解）。

### ADR-007：LLM-first — 不做客户端音乐生成逻辑
**决策**：不实现概率鼓机引擎（原 Phase 2 计划的 DrumEngine），所有音乐创作决策由 Claude 推理完成，通过现有工具（`add_notes_to_clip`）直接写入 Ableton。
**原因**：(1) Claude 具备足够的乐理知识，能根据自然语言推理出合适的音符/节奏/力度；(2) 硬编码风格预设限制了创作自由度，与 AIM "自然语言控制" 的核心理念矛盾；(3) 减少代码量和维护负担。
**取舍**：生成结果的随机性完全依赖 LLM temperature，无法做到"每次播放都不同"的实时演化。如未来需要实时性，可在 Phase 4 通过 Max for Live 设备实现。
**废弃**：原 ADR-002（drum_engine 在客户端运行）不再适用，由本 ADR 取代。

### ADR-008：采用社区补丁版 Remote Script
**决策**：替换原 ahujasid/ableton-mcp Remote Script 为 blaspalmisciano-ps/ableton-mcp-skill 的补丁版本。
**原因**：(1) 补丁版新增 17 个已实现命令，覆盖设备参数、混音、轨道管理、传输控制等关键能力；(2) 协议完全兼容（同端口、同 JSON 格式），AbletonBridge 零修改；(3) 修复了多个 Live 12 兼容性问题（MIDI 音符处理、线程安全）。
**风险**：依赖社区维护的 fork。缓解：补丁版代码已审计，关键功能有 AIM 端到端测试覆盖。

### ADR-009：本地执行路径（LOCAL_TOOLS）用于音频分析
**决策**：在 `tool_engine.py` 中新增 `LOCAL_TOOLS` dict，映射工具名到本地 Python 执行函数。`execute_tool()` 优先检查 LOCAL_TOOLS，命中则直接调用本地函数，不经过 Ableton socket。
**原因**：(1) 音频分析在 Ableton 侧无对应实现，必须本地 Python 执行；(2) dict 查找是最小代码变更（~10 行）；(3) 与 COMMAND_MAP 的声明式风格一致（ADR-004）；(4) 分析依赖项重且可选，懒加载 import 搭配清晰错误消息尊重不需要分析功能的用户。
**取舍**：两条执行路径（本地 + socket）略增路由复杂度。以 dict 成员检查缓解。长时间分析阻塞同步循环；Phase 2.5 CLI 场景可接受，GUI 场景留 Phase 5 解决。

**⚠️ 许可证警告（essentia / AGPL-3.0）**：
音频分析核心依赖 essentia，其使用 **AGPL-3.0** 许可证，具有传染性：
- **个人使用**：不受任何限制，可自由使用
- **对外分发**（发布、出售、SaaS）：整个 AIM 项目必须以 AGPL-3.0 发布，所有源代码必须公开
- **替代方案**：如需规避 AGPL，可将 essentia 替换为 librosa（ISC 许可证），代价是调性和和弦检测精度下降
- **当前决策**：优先音乐分析质量，采用 essentia。分发前重新评估许可证策略

---

## 6. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Ableton Remote Script API 变更 | 低 | 高 | 抽象 bridge 层，接口稳定 |
| Claude API 工具调用格式变更 | 低 | 中 | 版本锁定 anthropic SDK |
| 生成的 MIDI 音符 Ableton 不接受 | 中 | 中 | 单测覆盖边界值，加参数校验 |
| System Prompt 过长导致推理质量下降 | 中 | 中 | 模块化 prompt，按需注入上下文 |
| socket 超时在慢操作（加载乐器）时失败 | 高 | 低 | 已有 15s 超时（构造函数参数化），尚未外置为配置项 |

---

## 7. 成功标准

| 阶段 | 指标 | 目标值 |
|------|------|--------|
| Phase 1 | 重构后功能回归 | 100% 行为一致 ✅ |
| Phase 2 | 工具覆盖 | 23 tools（8 existing + 15 new） |
| Phase 2 | 音质五维度 | 声音设计：能调设备参数；混音：volume/pan 听感正确；律动：velocity 有变化；编排：能删/停；一致性：守调 |
| Phase 2 | Time-to-First-Loop | < 30s |
| Phase 2.5 | 分析工具覆盖 | 29 tools（23 Ableton + 6 分析） |
| Phase 2.5 | 参考工作流 | 用户给出参考曲 → Claude 分析 → 以分析结果创作 |
| Phase 3 | 录音工作流 | 能通过自然语言录制外部输入 |
| Phase 4 | Scene 管理 | 多 loop 切换可用 |

---

## 8. 开放问题

### 仍未决

- [x] ~~Remote Script 侧是否需要修改以支持 Phase 3 的撤销？~~
  *已决：ADR-008 采用补丁版 Remote Script，已包含 delete_track/delete_clip/stop_clip。Phase 2 即可使用。*
- [x] ~~Phase 2 的 evolution（跨 scene 突变）算法是否值得在 v1 实现，还是留到 Phase 4？~~
  *已决：ADR-007 取消了客户端概率引擎，evolution 概念不再适用。如需实时演化，Phase 4 可考虑 Max for Live 方案。*
- [ ] 是否需要支持多用户/多 Ableton 实例？（当前假设单机单实例）
  *现状：ableton_bridge.py 硬编码 localhost:9877，单实例假设贯穿所有模块。*
- [ ] System Prompt 的音乐规则（URI、BPM 范围等）是否应该外置为配置文件？
  *现状：prompts.py 包含 ~64 行硬编码规则；Phase 3 扩展点 `build_system_prompt(session_context)` 已预留，可作为外置入口。*

### Phase 1 新增问题

- [ ] Socket 超时 15 秒硬编码在 `AbletonBridge.__init__()` 中——是否应抽为配置项？（风险表已提及）
- [ ] 模型版本 `claude-sonnet-4-6` 硬编码在 `tool_engine.py`——是否外置到 `.env` 或配置文件？
- [x] ~~工具结果截断为 200 字符（`tool_engine.py`）——对复杂 `session_info` 响应是否足够？~~
  *已决：Phase 2 实现了 per-tool 截断限制（RESULT_LIMIT dict），get_device_parameters/get_clip_notes 2000 字符，get_track_info 1000 字符，默认 200。*

---

*本文档随项目演进持续更新。每个 Phase 完成后更新对应状态。*
