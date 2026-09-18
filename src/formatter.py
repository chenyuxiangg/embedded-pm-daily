"""Telegram 消息格式化。

Telegram 限制:
- 单条消息最大 4096 字符
- HTML 模式支持 <b> <i> <code> <pre> <a href>
"""
from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime
from typing import List

from .models import Article

CATEGORY_EMOJI = {
    "政策": "🏛",
    "产业": "🏭",
    "技术": "🔬",
    "拆解": "🔧",
    "趋势": "🚀",
    "用户": "👥",
}

CATEGORY_ORDER = ["政策", "产业", "技术", "拆解", "趋势", "用户"]


def _esc(s: str) -> str:
    """Escape for Telegram HTML parse mode."""
    if not s:
        return ""
    return html.escape(s, quote=False)


def format_article_line(a: Article, idx: int) -> str:
    """单条 article 的文本行(Telegram HTML)。"""
    summary = a.summary or a.raw_text or ""
    summary = _esc(summary[:240])
    title = _esc(a.title)
    source = _esc(a.source)
    url = a.url
    return (
        f"{idx}. <a href=\"{html.escape(url)}\">{title}</a>\n"
        f"   <i>{source}</i>\n"
        f"   {summary}"
    )


def format_section(category: str, items: List[Article], start_idx: int = 1) -> tuple[str, int]:
    """格式化一个分类段落,返回 (text, 下次起始 idx)。"""
    if not items:
        return "", start_idx
    emoji = CATEGORY_EMOJI.get(category, "•")
    lines = [f"\n{emoji} <b>{category}</b>"]
    for i, a in enumerate(items, start_idx):
        lines.append(format_article_line(a, i))
    return "\n".join(lines), start_idx + len(items)


def format_daily(articles: List[Article], date_str: str) -> str:
    """把一天的文章拼成单条 Telegram 消息。

    设计:按 category 分组,每段标题 + N 个条目。
    若总长度超过 3500 字符,拆成多条。

    跳过空 summary 的文章(LLM 失败的文章不推送,避免泄露 raw_text)。
    """
    # 过滤:只保留有 summary 的文章
    articles = [a for a in articles if a.summary and a.summary.strip()]
    if not articles:
        return ""
    # 分组
    by_cat: dict[str, list[Article]] = defaultdict(list)
    for a in articles:
        by_cat[a.category].append(a)

    # 按既定顺序输出
    sections: list[str] = []
    header = (
        f"📰 <b>嵌入式 PM 早报 · {date_str}</b>\n"
        f"共 {len(articles)} 条"
    )
    sections.append(header)
    idx = 1
    for cat in CATEGORY_ORDER:
        if cat in by_cat:
            text, idx = format_section(cat, by_cat[cat], idx)
            if text:
                sections.append(text)
    # 兜底:任何未列入的分类
    for cat, items in by_cat.items():
        if cat not in CATEGORY_ORDER:
            text, idx = format_section(cat, items, idx)
            if text:
                sections.append(text)

    return "\n".join(sections)
