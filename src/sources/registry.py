"""中文媒体数据源。"""
from __future__ import annotations

from typing import List

from ..models import Article
from .base import BaseSource


# ---------------- 政策/产业 ----------------


class CENA(BaseSource):
    """中国电子信息产业网(中国电子报官网)。"""

    name = "中国电子报"
    category = "政策"
    language = "zh"

    FEEDS = [
        "https://www.cena.com.cn/rss",  # 主 RSS
    ]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class EEFocusPolicy(BaseSource):
    """与非网-产业研究(深度产业分析)。"""

    name = "与非网·产业"
    category = "产业"
    language = "zh"

    FEEDS = [
        "https://www.eefocus.com/rss",
    ]

    def fetch(self) -> List[Article]:
        # 与非网主 RSS 里分类靠关键词筛
        arts = self._parse_rss(self.FEEDS[0])
        keep_kw = ["产业", "市场", "供应链", "趋势", "格局", "赛道", "图谱"]
        return [a for a in arts if any(k in a.title for k in keep_kw)][: self.max_per_source]


# ---------------- 垂直技术媒体 ----------------


class EEFocus(BaseSource):
    """与非网主站。"""

    name = "与非网"
    category = "技术"
    language = "zh"

    FEEDS = ["https://www.eefocus.com/rss"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class EETimesChina(BaseSource):
    """电子工程专辑(国际资讯)。"""

    name = "电子工程专辑"
    category = "技术"
    language = "zh"

    FEEDS = [
        "https://www.eet-china.com/rss",
    ]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class EEPW(BaseSource):
    """电子产品世界。"""

    name = "电子产品世界"
    category = "技术"
    language = "zh"

    FEEDS = ["https://www.eepw.com.cn/rss.xml"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class Elecfans(BaseSource):
    """电子发烧友。"""

    name = "电子发烧友"
    category = "技术"
    language = "zh"

    FEEDS = ["https://www.elecfans.com/rss"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class Ijiwei(BaseSource):
    """爱集微(半导体产业)。"""

    name = "爱集微"
    category = "产业"
    language = "zh"

    FEEDS = ["https://www.jiweinet.com/rss"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class Zhidx(BaseSource):
    """智东西(智能产业)。"""

    name = "智东西"
    category = "产业"
    language = "zh"

    FEEDS = ["https://www.zhidx.com/rss"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


# ---------------- 拆解/硬件分析 ----------------


class WoI52Audio(BaseSource):
    """我爱音频网(TWS/音频拆解)。"""

    name = "我爱音频网"
    category = "拆解"
    language = "zh"

    FEEDS = ["https://www.52audio.com/rss.xml"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class ChargerLAB(BaseSource):
    """ChargerLAB(充电器/移动电源拆解)。"""

    name = "ChargerLAB"
    category = "拆解"
    language = "en"

    FEEDS = ["https://www.chargerlab.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class IFixitFeed(BaseSource):
    """iFixit 拆解。"""

    name = "iFixit"
    category = "拆解"
    language = "en"

    FEEDS = ["https://www.ifixit.com/News/feed.rss"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


# ---------------- 趋势/众筹 ----------------


class KickstarterTech(BaseSource):
    """Kickstarter 技术类热门(从网页解析)。"""

    name = "Kickstarter"
    category = "趋势"
    language = "en"

    URL = "https://www.kickstarter.com/discover/advanced?category_id=16&sort=end_date&seed=2855338&page=1"

    def fetch(self) -> List[Article]:
        # Kickstarter 没有公开 RSS,这里用其 Discover 页 + 关键词过滤
        # 实际项目卡(每个项目)由它们的 discover API 输出
        # 简化:抓首页 HTML 提取标题+链接
        try:
            html = self._http_get(self.URL)
        except Exception:
            return []
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        articles: List[Article] = []
        for a in soup.select("a[href*='/projects/']"):
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)
            if not title or len(title) < 4 or "/projects/" not in href:
                continue
            if not href.startswith("http"):
                href = "https://www.kickstarter.com" + href
            articles.append(
                Article(title=title[:120], url=href, source=self.name, category=self.category, language=self.language)
            )
            if len(articles) >= self.max_per_source:
                break
        return articles
