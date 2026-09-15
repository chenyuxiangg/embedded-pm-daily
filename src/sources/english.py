"""英文媒体数据源。"""
from __future__ import annotations

from typing import List

from ..models import Article
from .base import BaseSource


class EETimes(BaseSource):
    """EE Times(Aspencore 旗舰)。"""

    name = "EE Times"
    category = "技术"
    language = "en"

    FEEDS = ["https://www.eetimes.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class EmbeddedCom(BaseSource):
    """Embedded.com(Aspencore)。"""

    name = "Embedded.com"
    category = "技术"
    language = "en"

    FEEDS = ["https://www.embedded.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class IEEESpectrum(BaseSource):
    """IEEE Spectrum。"""

    name = "IEEE Spectrum"
    category = "技术"
    language = "en"

    FEEDS = ["https://spectrum.ieee.org/rss/fulltext"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class SemiEngineering(BaseSource):
    """Semiconductor Engineering。"""

    name = "Semiconductor Engineering"
    category = "技术"
    language = "en"

    FEEDS = ["https://semiengineering.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class ElectronicsWeekly(BaseSource):
    """Electronics Weekly。"""

    name = "Electronics Weekly"
    category = "技术"
    language = "en"

    FEEDS = ["https://www.electronicsweekly.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class Hackaday(BaseSource):
    """Hackaday(创客/趋势)。"""

    name = "Hackaday"
    category = "趋势"
    language = "en"

    FEEDS = ["https://hackaday.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class TheVerge(BaseSource):
    """The Verge(消费电子深度)。"""

    name = "The Verge"
    category = "趋势"
    language = "en"

    FEEDS = ["https://www.theverge.com/rss/index.xml"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class CNXSoftware(BaseSource):
    """CNX Software(嵌入式/IoT/开发板)。"""

    name = "CNX Software"
    category = "技术"
    language = "en"

    FEEDS = ["https://www.cnx-software.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class CircuitCellar(BaseSource):
    """Circuit Cellar(嵌入式系统)。"""

    name = "Circuit Cellar"
    category = "技术"
    language = "en"

    FEEDS = ["https://circuitcellar.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])


class EEHerald(BaseSource):
    """EE Herald(半导体/嵌入式)。"""

    name = "EE Herald"
    category = "技术"
    language = "en"

    FEEDS = ["https://eeherald.com/feed/"]

    def fetch(self) -> List[Article]:
        return self._parse_rss(self.FEEDS[0])
