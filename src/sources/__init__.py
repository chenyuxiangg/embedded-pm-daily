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
    """优先 RSS,不够 max_per_source 时用 HTML 补齐(而非完全替换)。

    设计:
    - RSS 全挂: 用 HTML 全部
    - RSS 拿到的 < max_per_source: 用 HTML 补到 max_per_source
    - RSS 已经够了: 不再调 HTML(节省时间/避免重复抓)
    """
    inst = primary(lookback_hours=lookback_hours, max_per_source=max_per_source)
    try:
        primary_items = inst.fetch()
    except Exception as e:
        logger.warning("[%s] 抓取异常: %s", primary.__name__, e)
        primary_items = []

    if primary_items:
        logger.info("[%s] RSS 抓到 %d 篇", primary.__name__, len(primary_items))

    # RSS 全挂或不够,且没有兜底,返回现有
    if secondary is None:
        return primary_items[:max_per_source]

    need_html = len(primary_items) < max_per_source
    if not need_html and primary_items:
        # RSS 已经够满
        return primary_items[:max_per_source]

    try:
        fb = secondary(lookback_hours=lookback_hours, max_per_source=max_per_source)
        html_items = fb.fetch() or []
    except Exception as e:
        logger.warning("[%s] HTML 兜底失败: %s", secondary.__name__, e)
        html_items = []

    if not primary_items:
        if html_items:
            logger.info("[%s] HTML 兜底抓到 %d 篇(RSS 全挂)", secondary.__name__, len(html_items))
        return html_items[:max_per_source]

    # RSS 不够 → HTML 补齐(URL 去重,避免 RSS 和 HTML 抓到同一篇)
    existing_urls = {a.url.strip().lower() for a in primary_items}
    merged = list(primary_items)
    added = 0
    for a in html_items:
        if len(merged) >= max_per_source:
            break
        if a.url.strip().lower() in existing_urls:
            continue
        merged.append(a)
        existing_urls.add(a.url.strip().lower())
        added += 1
    if added:
        logger.info("[%s] HTML 补齐 %d 篇(合并去重后共 %d)",
                    secondary.__name__, added, len(merged))
    return merged


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
