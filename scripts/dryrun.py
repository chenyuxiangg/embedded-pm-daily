"""本地 dryrun:不调用 LLM,不推送 Telegram,只把抓到的文章和分组打印出来。

用法:
    python scripts/dryrun.py
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG
from src.deduplicator import DedupStore
from src.sources import collect_all_articles
from src.models import Article


def main():
    all_arts: list[Article] = collect_all_articles(CONFIG.lookback_hours, CONFIG.max_per_source)

    # dryrun 也做一次 URL 去重,看着清爽
    seen_urls: set[str] = set()
    unique: list[Article] = []
    for a in all_arts:
        if a.url in seen_urls:
            continue
        seen_urls.add(a.url)
        unique.append(a)

    print(f"\n总抓取: {len(all_arts)} 篇(URL 去重后 {len(unique)} 篇)")
    store = DedupStore(CONFIG.seen_file)
    fresh = store.filter_new(unique)
    print(f"新文章: {len(fresh)} 篇(已过滤 {len(unique) - len(fresh)} 篇重复)")

    by_cat: dict[str, list[Article]] = defaultdict(list)
    for a in fresh:
        by_cat[a.category].append(a)

    for cat, items in by_cat.items():
        print(f"\n{'='*60}\n{cat} ({len(items)} 篇)\n{'='*60}")
        for i, a in enumerate(items, 1):
            t = (a.published.strftime("%m-%d %H:%M") if a.published else "??-??")
            print(f"{i}. [{a.source}] {a.title}\n   {t} | {a.url}")

    # dryrun 不写入 seen,免得占真数据
    print("\n(dryrun 不会写入 seen.json)")


if __name__ == "__main__":
    main()
