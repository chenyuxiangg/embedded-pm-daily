"""HTML 兜底解析器。

对于没有 RSS 或 RSS 抓不到的站点,从首页/列表页 HTML 解析文章链接和标题。
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..models import Article
from .base import BaseSource

logger = logging.getLogger(__name__)


class HTMLListSource(BaseSource):
    """通用 HTML 列表页解析器。

    适配大部分"文章列表"型站点:
    - 抓首页 HTML
    - 找 <article> / class 含 post/article/news 的元素
    - 提取链接 + 标题
    - 用 URL 模式做白名单,避免抓导航/广告链接
    """

    name = "HTML"
    category = "技术"
    language = "zh"
    URL = ""
    URL_PATTERNS = ()  # 白名单正则,匹配文章 URL
    TITLE_SELECTOR = None  # 自定义标题选择器,None 时用 <a> 文本

    def fetch(self) -> List[Article]:
        if not self.URL:
            return []
        try:
            html = self._http_get(self.URL, timeout=25)
        except Exception as e:
            logger.warning("[%s] 抓取 %s 失败: %s", self.name, self.URL, e)
            return []

        soup = BeautifulSoup(html, "lxml")
        items: list[Article] = []
        seen_urls: set[str] = set()

        # 优先按 article 标签找
        candidates = soup.find_all("article")
        if not candidates:
            # 退而求其次,扫所有链接
            candidates = soup.find_all("a", href=True)

        for node in candidates:
            a = node.find("a", href=True) if node.name != "a" else node
            if not a or not a.get("href"):
                continue
            href = a["href"]
            if not self._url_match(href):
                continue
            # 转绝对 URL
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                p = urlparse(self.URL)
                href = f"{p.scheme}://{p.netloc}{href}"
            elif not href.startswith("http"):
                continue

            if href in seen_urls:
                continue
            seen_urls.add(href)

            # 标题
            if self.TITLE_SELECTOR:
                tnode = node.select_one(self.TITLE_SELECTOR)
                title = tnode.get_text(" ", strip=True) if tnode else a.get_text(" ", strip=True)
            else:
                title = a.get_text(" ", strip=True)
            title = re.sub(r"\s+", " ", title).strip()
            if len(title) < 6 or len(title) > 200:
                continue

            items.append(
                Article(
                    title=title,
                    url=href,
                    source=self.name,
                    category=self.category,
                    published=datetime.now(timezone.utc),  # 无日期兜底
                    language=self.language,
                )
            )
            if len(items) >= self.max_per_source:
                break

        return items

    def _url_match(self, href: str) -> bool:
        if not self.URL_PATTERNS:
            return True
        # 排除明显的导航/分类/tag/搜索类 URL
        bad_patterns = ("/category/", "/tag/", "/tags/", "/search/", "/author/", "/about", "/contact", "/login", "/signup", "/privacy", "/terms")
        if any(p in href.lower() for p in bad_patterns):
            return False
        return any(re.search(p, href, re.IGNORECASE) for p in self.URL_PATTERNS)


# ---------------- 具体的中文站点(HTML 兜底) ----------------


class EEFocusHTML(HTMLListSource):
    name = "与非网"
    category = "技术"
    language = "zh"
    URL = "https://www.eefocus.com"
    URL_PATTERNS = (r"/article/\d+", r"/article/[a-f0-9-]+")


class ElecfansHTML(HTMLListSource):
    name = "电子发烧友"
    category = "技术"
    language = "zh"
    URL = "https://www.elecfans.com"
    URL_PATTERNS = (r"elecfans\.com/d/\d+\.html", r"/news/\d+/\d+\.html")


class EEPWHTML(HTMLListSource):
    name = "电子产品世界"
    category = "技术"
    language = "zh"
    URL = "https://www.eepw.com.cn"
    URL_PATTERNS = (r"/article/", r"/news/")


class EETimesChinaHTML(HTMLListSource):
    name = "电子工程专辑"
    category = "技术"
    language = "zh"
    URL = "https://www.eet-china.com"
    URL_PATTERNS = (r"/news/article/", r"/article/", r"/[a-z\-]+-article-\d+")


class CENAHTML(HTMLListSource):
    name = "中国电子报"
    category = "政策"
    language = "zh"
    URL = "https://www.cena.com.cn"
    URL_PATTERNS = (r"/\d{4}/\d{2}/\d{2}/", r"/news/")


class IjiweiHTML(HTMLListSource):
    name = "爱集微"
    category = "产业"
    language = "zh"
    URL = "https://www.jiweinet.com"
    URL_PATTERNS = (r"/news/\d+", r"/p/")


class ChargerLABHTML(HTMLListSource):
    name = "ChargerLAB"
    category = "拆解"
    language = "en"
    URL = "https://www.chargerlab.com"
    URL_PATTERNS = (r"/teardown-of-", r"chargerlab\.com/[a-z0-9\-]+/$")


class IFixitHTML(HTMLListSource):
    name = "iFixit"
    category = "拆解"
    language = "en"
    URL = "https://www.ifixit.com/Teardown"
    URL_PATTERNS = (r"/Teardown/[a-z0-9\-]+$", r"/News/\d+")


class WoI52AudioHTML(HTMLListSource):
    name = "我爱音频网"
    category = "拆解"
    language = "zh"
    URL = "https://www.52audio.com"
    URL_PATTERNS = (r"/archives/\d+", r"52audio\.com/\d+\.html")


# 通用 HTML 抓取器
HTML_FALLBACK_SOURCES = [
    EEFocusHTML,
    ElecfansHTML,
    EEPWHTML,
    EETimesChinaHTML,
    CENAHTML,
    IjiweiHTML,
    ChargerLABHTML,
    IFixitHTML,
    WoI52AudioHTML,
]
