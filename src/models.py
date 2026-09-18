"""数据模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """单篇文章。"""
    title: str
    url: str
    source: str  # 来源名,如 "EE Times"
    category: str  # 分类: 政策/产业/技术/拆解/趋势/用户
    published: Optional[datetime] = None
    summary: Optional[str] = None  # AI 摘要(2-3 句中文,英文源也会被翻译/改写)
    raw_text: Optional[str] = None  # 原文(供 AI 摘要用)
    language: str = "en"  # en / zh

    def dedup_key(self) -> str:
        """用于去重的稳定 key,优先用 url。"""
        return self.url.strip().lower()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.summary,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Article":
        pub = d.get("published")
        if pub and isinstance(pub, str):
            try:
                pub = datetime.fromisoformat(pub)
            except Exception:
                pub = None
        return cls(
            title=d.get("title", ""),
            url=d.get("url", ""),
            source=d.get("source", ""),
            category=d.get("category", ""),
            published=pub,
            summary=d.get("summary"),
            language=d.get("language", "en"),
        )
