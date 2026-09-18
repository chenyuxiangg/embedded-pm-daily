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
    """按字符数切分,尽量按段落切,避免切到 HTML 标签中间。

    Telegram HTML 模式限制:
    - 单条最大 4096 字符,留点余量
    - 如果切点落在某个 '<...>' 标签内部或之后,会导致标签跨段未闭合,Telegram 会丢消息
    """
    if len(text) <= max_len:
        return [text]

    def safe_cut(s: str, limit: int) -> int:
        """找一个 cut 点,保证 [0:cut] 区间内 <a> 标签都成对闭合。
        返回值可能略大于 limit(最多 1 个 </a> 之后),Telegram 上限 4096 留有足够余量。
        """
        cut = s.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = limit

        # 检查 [0:cut] 区间内是否有悬空 '<a'
        head = s[:cut]
        last_open_a = head.rfind("<a ")
        last_open_a_simple = head.rfind("<a>")
        last_a_pos = max(last_open_a, last_open_a_simple)
        if last_a_pos != -1:
            tail_after_open = head[last_a_pos:]
            if "</a>" not in tail_after_open:
                # 悬空:把 cut 推到下一个 </a> 之后,让 <a ...>...</a> 完整留在前段
                close = s.find("</a>", last_a_pos)
                if close != -1:
                    cut = close + len("</a>")
                else:
                    # 没找到闭合 → 这个 <a 标签肯定是畸形,直接 cut 到 <a 之前让前段不带它
                    cut = max(last_a_pos - 1, 0)
        return cut

    parts: List[str] = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        cut = safe_cut(text, max_len)
        # 防御:切出空串(比如切点在字符串最末尾)
        if cut <= 0:
            cut = max_len
        parts.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return parts


async def _send_async(text: str) -> None:
    bot = telegram.Bot(token=CONFIG.telegram_bot_token)
    parts = _split_message(text)
    failures: List[str] = []
    for i, part in enumerate(parts, 1):
        suffix = f" <i>({i}/{len(parts)})</i>" if len(parts) > 1 else ""
        sent = False
        # 第一次:HTML 模式
        try:
            await bot.send_message(
                chat_id=CONFIG.telegram_chat_id,
                text=part + suffix,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            logger.info("已发送第 %d/%d 段", i, len(parts))
            sent = True
        except Exception as e:
            logger.warning("HTML 发送失败[%d/%d], 降级为纯文本: %s", i, len(parts), e)
        # 第二次:纯文本降级
        if not sent:
            try:
                await bot.send_message(
                    chat_id=CONFIG.telegram_chat_id,
                    text=part + suffix,
                    disable_web_page_preview=True,
                )
                logger.info("已发送第 %d/%d 段(纯文本降级)", i, len(parts))
                sent = True
            except Exception as e2:
                logger.error("纯文本降级也失败[%d/%d]: %s", i, len(parts), e2)
        if not sent:
            failures.append(f"{i}/{len(parts)}")

    if failures:
        # 任何一段发不出去,直接抛,避免上层 mark_seen 后文章永远去重掉
        raise RuntimeError(f"Telegram 推送失败,以下分段未发送: {failures}")


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
