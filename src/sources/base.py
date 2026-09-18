"""数据源基类。"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Article

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """所有数据源的基类。

    设计要点:
    - 每个子类声明 name / category
    - 子类必须实现 fetch() 返回 Article 列表
    - 工具方法: _parse_rss, _fetch_html, _abs_url, _parse_date
    """

    name: str = "base"
    category: str = "技术"
    language: str = "en"

    def __init__(self, lookback_hours: int = 24, max_per_source: int = 8):
        self.lookback_hours = lookback_hours
        self.max_per_source = max_per_source

    @abstractmethod
    def fetch(self) -> List[Article]:
        ...

    # ---- 工具方法 ----
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _http_get(self, url: str, timeout: int = 20) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.text

    def _parse_rss(self, feed_url: str) -> List[Article]:
        """通用 RSS 解析,自动过滤时间窗口内的条目。"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        articles: List[Article] = []
        try:
            r = self._http_get(feed_url)
        except Exception as e:
            logger.warning("[%s] RSS 抓取失败 %s: %s", self.name, feed_url, e)
            return articles

        try:
            feed = feedparser.parse(r)
        except Exception as e:
            logger.warning("[%s] RSS 解析失败: %s", self.name, e)
            return articles

        for entry in feed.entries[: self.max_per_source * 2]:
            published = self._parse_date(entry)
            # 没日期的也收下,避免漏掉
            if published and published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            if published and published < cutoff:
                continue
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            if not title or not link:
                continue
            # 摘要
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            summary = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)[:3000]

            articles.append(
                Article(
                    title=title,
                    url=link,
                    source=self.name,
                    category=self.category,
                    published=published,
                    raw_text=summary,
                    language=self.language,
                )
            )
            if len(articles) >= self.max_per_source:
                break
        return articles

    def _parse_date(self, entry) -> Optional[datetime]:
        for attr in ("published_parsed", "updated_parsed", "created_parsed"):
            v = getattr(entry, attr, None)
            if v:
                try:
                    return datetime(*v[:6], tzinfo=timezone.utc)
                except Exception:
                    continue
        for attr in ("published", "updated"):
            v = getattr(entry, attr, None)
            if v:
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except Exception:
                    continue
        return None
