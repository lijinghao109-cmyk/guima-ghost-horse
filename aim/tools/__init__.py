"""
工具定义聚合。

新增工具时：
1. 在对应 *_tools.py 文件里追加 dict 到 TOOLS 列表
2. 如果是新文件，在此处添加 import
"""

from aim.tools.session_tools import TOOLS as SESSION_TOOLS
from aim.tools.track_tools import TOOLS as TRACK_TOOLS
from aim.tools.clip_tools import TOOLS as CLIP_TOOLS
from aim.tools.mixer_tools import TOOLS as MIXER_TOOLS
from aim.tools.device_tools import TOOLS as DEVICE_TOOLS
from aim.tools.transport_tools import TOOLS as TRANSPORT_TOOLS
from aim.tools.management_tools import TOOLS as MANAGEMENT_TOOLS
from aim.tools.analysis_tools import TOOLS as ANALYSIS_TOOLS

ALL_TOOLS: list[dict] = (
    SESSION_TOOLS + TRACK_TOOLS + CLIP_TOOLS
    + MIXER_TOOLS + DEVICE_TOOLS + TRANSPORT_TOOLS + MANAGEMENT_TOOLS
    + ANALYSIS_TOOLS
)
