"""
工具定义聚合。

新增工具时只需：
1. 在对应 *_tools.py 文件里追加 dict 到 TOOLS 列表
2. 无需修改本文件（已自动 import）
"""

from aim.tools.session_tools import TOOLS as SESSION_TOOLS
from aim.tools.track_tools import TOOLS as TRACK_TOOLS
from aim.tools.clip_tools import TOOLS as CLIP_TOOLS
from aim.tools.drum_tools import TOOLS as DRUM_TOOLS

ALL_TOOLS: list[dict] = SESSION_TOOLS + TRACK_TOOLS + CLIP_TOOLS + DRUM_TOOLS
