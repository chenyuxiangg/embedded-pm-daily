"""数据源聚合。

策略:每个源优先用 RSS,RSS 抓不到时自动 fallback 到 HTML 列表解析。
"""
from __future__ import annotations

import logging
from typing import List, Type

from .base import BaseSource
from . import english
from . import registry
from . import fallback

logger = logging.getLogger(__name__)


# 源配置:(RSS 源类, 兜底 HTML 源类)
# None 表示没有 HTML 兜底
SOURCE_PLAN: list[tuple[Type[BaseSource], Type[BaseSource] | None]] = [
    # 政策/产业
    (registry.CENA, fallback.CENAHTML),
    (registry.EEFocusPolicy, fallback.EEFocusHTML),
    (registry.Ijiwei, fallback.IjiweiHTML),
    (registry.Zhidx, None),
    # 中文技术
    (registry.EEFocus, fallback.EEFocusHTML),
    (registry.EETimesChina, fallback.EETimesChinaHTML),
    (registry.EEPW, fallback.EEPWHTML),
    (registry.Elecfans, fallback.ElecfansHTML),
    # 拆解
    (registry.WoI52Audio, fallback.WoI52AudioHTML),
    (registry.ChargerLAB, fallback.ChargerLABHTML),
    (registry.IFixitFeed, fallback.IFixitHTML),
    # 趋势/众筹
    (registry.KickstarterTech, None),
    (english.Hackaday, None),
    # 英文技术
    (english.EETimes, None),
    (english.EmbeddedCom, None),
    (english.IEEESpectrum, None),
    (english.SemiEngineering, None),
    (english.ElectronicsWeekly, None),
    (english.TheVerge, None),
    (english.CNXSoftware, None),
    (english.CircuitCellar, None),
    (english.EEHerald, None),
]


def fetch_with_fallback(primary: Type[BaseSource], secondary: Type[BaseSource] | None,
                         lookback_hours: int, max_per_source: int) -> list:
    """优先用 RSS,失败时 fallback 到 HTML。返回 article 列表。"""
    inst = primary(lookback_hours=lookback_hours, max_per_source=max_per_source)
    try:
        items = inst.fetch()
    except Exception as e:
        logger.warning("[%s] 抓取异常: %s", primary.__name__, e)
        items = []

    if items:
        logger.info("[%s] RSS 抓到 %d 篇", primary.__name__, len(items))
        return items

    if secondary is None:
        return []

    try:
        fb = secondary(lookback_hours=lookback_hours, max_per_source=max_per_source)
        items = fb.fetch()
        if items:
            logger.info("[%s] HTML 兜底抓到 %d 篇", secondary.__name__, len(items))
    except Exception as e:
        logger.warning("[%s] HTML 兜底失败: %s", secondary.__name__, e)

    return items or []


def build_sources(lookback_hours: int, max_per_source: int):
    """返回一个 fetcher 列表,每个 fetcher 调用一次能拿到该源的文章。"""
    fetchers = []
    for primary, secondary in SOURCE_PLAN:
        def make_fetcher(p=primary, s=secondary):
            def f():
                return fetch_with_fallback(p, s, lookback_hours, max_per_source)
            return f
        fetchers.append((primary.__name__, make_fetcher()))
    return fetchers


def collect_all_articles(lookback_hours: int, max_per_source: int) -> list:
    """主流程:遍历所有源,聚合去重前的所有 article。"""
    from ..models import Article

    fetchers = build_sources(lookback_hours, max_per_source)
    all_articles: list[Article] = []
    for name, fn in fetchers:
        try:
            items = fn()
            all_articles.extend(items)
        except Exception as e:
            logger.error("[%s] 整体失败: %s", name, e)
    return all_articles
