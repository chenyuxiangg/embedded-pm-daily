"""主入口。"""
from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List

# 让脚本既可以 `python -m src.main` 也可以 `python src/main.py` 运行
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG
from src.deduplicator import DedupStore
from src.sources import collect_all_articles
from src.summarizer import Summarizer
from src.telegram_bot import send_to_telegram
from src.models import Article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("embedded-pm-daily")


def collect_all() -> List[Article]:
    """从所有源拉文章(RSS 优先 + HTML 兜底)。"""
    return collect_all_articles(CONFIG.lookback_hours, CONFIG.max_per_source)


def main() -> int:
    errors = CONFIG.validate()
    if errors:
        for e in errors:
            logger.error("配置缺失: %s", e)
        return 2

    logger.info("=== 嵌入式 PM 早报 启动 ===")

    # 1. 抓取
    raw = collect_all()
    logger.info("总抓取: %d 篇", len(raw))

    if not raw:
        logger.warning("没有抓到任何文章,跳过推送")
        return 0

    # 2. 去重
    store = DedupStore(CONFIG.seen_file)
    fresh = store.filter_new(raw)
    logger.info("过滤后新文章: %d 篇(去重掉 %d)", len(fresh), len(raw) - len(fresh))

    if not fresh:
        logger.info("今天没新内容")
        return 0

    # 3. AI 摘要(限制数量防止爆 token)
    summarizer = Summarizer()
    summarizer.summarize_batch(fresh, max_n=CONFIG.llm_max_articles)

    # 检查:LLM 失败的文章统计,方便排错
    failed = [a for a in fresh if not (a.summary and a.summary.strip())]
    if failed:
        logger.warning("LLM 摘要失败 %d 篇, 跳过推送: %s",
                       len(failed),
                       [a.title[:30] for a in failed[:5]])
    fresh_with_summary = [a for a in fresh if a.summary and a.summary.strip()]
    if not fresh_with_summary:
        logger.warning("所有文章摘要都失败,跳过推送")
        return 0

    # 4. 按"推送批次"分组(默认一天一批)
    today = datetime.now().strftime("%Y-%m-%d")
    batches = [[today, fresh_with_summary]]

    # 5. 推送(失败时不 mark_seen,避免下次被去重永远收不到)
    try:
        send_to_telegram(batches)
    except Exception as e:
        logger.exception("推送失败: %s", e)
        return 3

    # 6. 标记已推送(只在推送成功后才走, 且只标记实际推过的)
    store.mark_seen(fresh_with_summary)
    removed = store.cleanup()
    logger.info("清理过期 %d 条", removed)

    logger.info("=== 完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
