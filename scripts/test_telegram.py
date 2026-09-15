"""Telegram 推送连通性测试。发送一条简单消息确认配置正确。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG
from src.telegram_bot import _send_async


async def _test():
    msg = (
        "✅ <b>Telegram 推送连通性测试</b>\n\n"
        f"如果你看到这条消息,说明:\n"
        f"• Bot Token 正确\n"
        f"• Chat ID 正确\n"
        f"• HTML 模式可用\n\n"
        f"模型: <code>{CONFIG.llm_model}</code>\n"
        f"抓取窗口: {CONFIG.lookback_hours}h\n"
        f"每源上限: {CONFIG.max_per_source}"
    )
    await _send_async(msg)


if __name__ == "__main__":
    errors = CONFIG.validate()
    if errors:
        print("配置缺失:")
        for e in errors:
            print(f"  - {e}")
        print("\n请先编辑 .env 文件。")
        sys.exit(1)
    asyncio.run(_test())
    print("已发送测试消息,请到 Telegram 确认。")
