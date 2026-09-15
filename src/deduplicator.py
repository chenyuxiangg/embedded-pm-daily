"""去重 + 持久化。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .models import Article


class DedupStore:
    """已推送文章存储,简单 JSON 文件。

    - 用 url 做主键
    - 默认保留 7 天,过期清理
    """

    def __init__(self, path: Path, ttl_days: int = 7):
        self.path = path
        self.ttl_days = ttl_days
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._store: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._store, f, ensure_ascii=False, indent=2)

    def filter_new(self, articles: List[Article]) -> List[Article]:
        """过滤掉已经推送过的。"""
        return [a for a in articles if a.dedup_key() not in self._store]

    def mark_seen(self, articles: List[Article]) -> None:
        """标记为已推送。"""
        now = datetime.now().isoformat()
        for a in articles:
            self._store[a.dedup_key()] = {
                "title": a.title,
                "source": a.source,
                "category": a.category,
                "first_seen": now,
            }
        self._save()

    def cleanup(self) -> int:
        """清理过期记录,返回清理条数。"""
        cutoff = datetime.now() - timedelta(days=self.ttl_days)
        before = len(self._store)
        new_store = {}
        for k, v in self._store.items():
            first_seen = v.get("first_seen")
            if not first_seen:
                new_store[k] = v
                continue
            try:
                ts = datetime.fromisoformat(first_seen)
            except Exception:
                new_store[k] = v
                continue
            if ts >= cutoff:
                new_store[k] = v
        self._store = new_store
        self._save()
        return before - len(self._store)
