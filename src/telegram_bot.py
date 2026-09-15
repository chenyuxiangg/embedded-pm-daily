"""Telegram 推送。"""
from __future__ import annotations

import asyncio
import logging
from typing import List

import telegram
from telegram.constants import ParseMode

from .config import CONFIG
from .formatter import format_daily

logger = logging.getLogger(__name__)


def _split_message(text: str, max_len: int = 3500) -> List[str]:
    """按字符数切分,尽量按段落切。"""
    if len(text) <= max_len:
        return [text]
    parts: List[str] = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        # 找最近的 \n\n 切
        cut = text.rfind("\n\n", 0, max_len)
        if cut < max_len // 2:
            cut = max_len
        parts.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return parts


async def _send_async(text: str) -> None:
    bot = telegram.Bot(token=CONFIG.telegram_bot_token)
    parts = _split_message(text)
    for i, part in enumerate(parts, 1):
        suffix = f" <i>({i}/{len(parts)})</i>" if len(parts) > 1 else ""
        try:
            await bot.send_message(
                chat_id=CONFIG.telegram_chat_id,
                text=part + suffix,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            logger.info("已发送第 %d/%d 段", i, len(parts))
        except Exception as e:
            logger.error("发送失败[%d/%d]: %s", i, len(parts), e)
            # 降级:纯文本再发一次
            try:
                await bot.send_message(
                    chat_id=CONFIG.telegram_chat_id,
                    text=part + suffix,
                    disable_web_page_preview=True,
                )
            except Exception as e2:
                logger.error("降级发送也失败: %s", e2)


def send_to_telegram(articles: List[list]) -> None:
    """同步入口,内部跑异步。

    articles: [[date_str, [Article...]], ...]
    """
    if not articles:
        logger.warning("没有文章可发")
        return
    for date_str, arts in articles:
        if not arts:
            continue
        text = format_daily(arts, date_str)
        asyncio.run(_send_async(text))
