"""
AIM 主程序入口。

负责：初始化、Ableton 连接检测、启动对话主循环。
业务逻辑不在此文件，分别由 tool_engine 和 conversation 处理。
"""

import os

import anthropic

from aim.ableton_bridge import bridge
from aim.conversation import ConversationManager
from aim.tool_engine import run_session


def _check_api_key() -> str:
    """读取并校验 ANTHROPIC_API_KEY，失败则 exit(1)。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误：请设置 ANTHROPIC_API_KEY 环境变量")
        raise SystemExit(1)
    return api_key


def _print_banner() -> None:
    print("\n🎵  AIM — Ableton Interact Machine")
    print("    用自然语言创作音乐。输入 'quit' 退出。")
    print("─" * 50)


def main() -> None:
    """程序入口：初始化并启动会话。"""
    api_key = _check_api_key()

    # Ableton 连接检测
    test = bridge.test_connection()
    if "error" in test:
        print(f"❌ 无法连接 Ableton（端口 {bridge.port}）: {test['error']}")
        print("   请确认 Ableton 正在运行且 AbletonMCP Remote Script 已加载")
        raise SystemExit(1)
    print(f"✅ Ableton 已连接：{test.get('result', test)}")

    client = anthropic.Anthropic(api_key=api_key)
    conversation = ConversationManager()

    _print_banner()

    # 主对话循环
    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出 AIM。")
            break

        if user_input.lower() in ("quit", "exit", "q", "退出"):
            print("再见！")
            break
        if not user_input:
            continue

        conversation.add_user_message(user_input)
        run_session(conversation, client)
