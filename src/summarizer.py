"""AI 摘要模块。

策略:
- 英文文章:用 LLM 写一段中文摘要(2-3 句),PM 视角,聚焦对产品决策的价值
- 中文文章:用 LLM 改写为更精炼的中文摘要
- 失败时降级到 raw_text 截取
"""
from __future__ import annotations

import json
import logging
from typing import List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import CONFIG
from .models import Article

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_ZH = """你是嵌入式消费电子行业的产品经理助手。你的任务是把新闻/文章改写为对 PM 有价值的中文摘要。

要求:
1. 2-3 句话,不超过 120 字
2. 直接讲"这意味着什么"或"PM 该关注什么"
3. 优先指出: 技术/产品变化、产业链动向、价格/供应变化、用户痛点信号
4. 避免空话,不要"近日""据悉"
5. 不要"标题党"风格,实事求是
"""

SYSTEM_PROMPT_EN = """You are an assistant for a product manager in the embedded consumer electronics industry.
Your task: read the article and produce a Chinese summary.

Requirements:
1. 2-3 sentences, no more than 120 Chinese characters
2. Focus on product/PM implications: technology shifts, supply chain, user pain points, pricing
3. Be concrete, avoid "据报道" / "近日" filler phrases
4. Output ONLY the Chinese summary, no preamble
"""


class Summarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=CONFIG.llm_api_key,
            base_url=CONFIG.llm_api_base,
        )
        self.model = CONFIG.llm_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _call_llm(self, sys: str, user: str, max_tokens: int = 220) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    def summarize_one(self, article: Article) -> str:
        """生成单篇文章摘要。失败时降级。"""
        text = (article.raw_text or article.title or "").strip()
        if not text:
            return ""

        # 截断防止爆 token
        text = text[:1800]
        try:
            if article.language == "zh":
                sys = SYSTEM_PROMPT_ZH
                user = (
                    f"标题:{article.title}\n来源:{article.source}\n"
                    f"分类:{article.category}\n正文:\n{text}\n\n"
                    "请改写为 PM 视角的中文摘要(2-3 句):"
                )
            else:
                sys = SYSTEM_PROMPT_EN
                user = (
                    f"Title: {article.title}\nSource: {article.source}\n"
                    f"Category: {article.category}\n\n"
                    f"Content:\n{text}\n\n"
                    "Write a 2-3 sentence Chinese summary for a PM:"
                )
            return self._call_llm(sys, user, max_tokens=220)
        except Exception as e:
            logger.warning("摘要失败[%s]: %s | %s", article.source, article.title[:50], e)
            return text[:140] + ("…" if len(text) > 140 else "")

    def summarize_batch(self, articles: List[Article], max_n: Optional[int] = None) -> List[Article]:
        """批量摘要,带数量限制(防止爆 token / 烧钱)。"""
        target = articles[: max_n] if max_n else articles
        logger.info("开始摘要 %d 篇文章", len(target))
        for i, a in enumerate(target, 1):
            if a.summary:
                continue
            a.summary = self.summarize_one(a)
            if i % 10 == 0:
                logger.info("已摘要 %d/%d", i, len(target))
        # 没摘要到的文章用 raw_text 兜底
        for a in target:
            if not a.summary and a.raw_text:
                a.summary = a.raw_text[:140] + ("…" if len(a.raw_text) > 140 else "")
        return target
