"""AI 摘要模块。

策略:
- 英文文章:用 LLM 写一段中文摘要(2-3 句),PM 视角,聚焦对产品决策的价值
- 中文文章:用 LLM 改写为更精炼的中文摘要
- 失败时降级到 raw_text 截取

针对 MiniMax-M 系列做了适配:
- M3 是推理模型,推荐 temperature=1.0
- 用 max_completion_tokens(M3 推荐,旧的 max_tokens 仍兼容)
- 对 M3 加 reasoning_split 让 thinking 和正文分开返回
"""
from __future__ import annotations

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
2. **不要逐句翻译原文**——要提炼核心要点,讲"这意味着什么"或"PM 该关注什么"
3. 优先指出: 技术/产品变化、产业链动向、价格/供应变化、用户痛点信号
4. 避免空话,不要"近日""据悉""据悉报道"等废话
5. 不要"标题党"风格,实事求是
6. 如果原文是英文标题或英文人名/产品名,保留英文(不要强行翻译 iPhone 这种品牌名)
7. 直接输出中文摘要,不要"以下是摘要"等废话前缀
"""

SYSTEM_PROMPT_EN = """You are an assistant for a product manager in the embedded consumer electronics industry.
Your task: read the article and produce a Chinese summary.

Strict requirements:
1. 2-3 sentences, no more than 120 Chinese characters
2. **Do NOT translate the article sentence by sentence.** Extract the key point, focus on what a PM should know.
3. Focus on: technology/product shifts, supply chain, user pain points, pricing changes
4. Be concrete, avoid "据报道" / "近日" / "据悉" filler phrases
5. Keep English brand names and product names in English (e.g. iPhone, Meta Portal, Hackaday, ESP32)
6. Output ONLY the Chinese summary, no preamble, no English translation, no "以下是摘要"
"""


def _is_reasoning_model(model: str) -> bool:
    """M3 / M2 系列是推理模型,需要特殊处理。"""
    m = (model or "").lower()
    return any(tag in m for tag in ("-m3", "-m2", "reasoning", "o1", "o3"))


def _default_temperature(model: str) -> float:
    """按模型推荐 temperature。"""
    if _is_reasoning_model(model):
        return 1.0  # M3 / M2 / M2.x 推荐 0.8-1.0
    return 0.3  # 通用摘要场景


class Summarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=CONFIG.llm_api_key,
            base_url=CONFIG.llm_api_base,
        )
        self.model = CONFIG.llm_model
        self.temperature = _default_temperature(self.model)
        self.is_reasoning = _is_reasoning_model(self.model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _call_llm(self, sys: str, user: str, max_tokens: int = 220) -> str:
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=self.temperature,
        )
        # M3 / MiniMax-M 系列推荐新参数
        kwargs["max_completion_tokens"] = max_tokens
        # 旧的 max_tokens 也带上,某些服务端只认这个
        kwargs["max_tokens"] = max_tokens
        # 推理模型需要这个才能拿到 thinking 和正文
        if self.is_reasoning:
            kwargs["extra_body"] = {"reasoning_split": True}

        logger.debug("LLM 调用 model=%s temp=%.1f reasoning=%s",
                     self.model, self.temperature, self.is_reasoning)
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        return (msg.content or "").strip()

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
            # 诊断:打印异常类型 + traceback 头几行,方便排错
            import traceback
            tb_lines = traceback.format_exc().splitlines()
            tb_head = "\n    ".join(tb_lines[-4:])  # 最后4行
            logger.warning("摘要失败[%s]: %s | %s: %s\n    %s",
                           article.source, article.title[:50],
                           type(e).__name__, e, tb_head)
            # fallback: 返回空字符串而不是 raw_text(英文 raw_text 会导致推送英文)
            # 空字符串会让 formatter 跳过该文章
            return ""

    def summarize_batch(self, articles: List[Article], max_n: Optional[int] = None) -> List[Article]:
        """批量摘要,带数量限制(防止爆 token / 烧钱)。"""
        target = articles[: max_n] if max_n else articles
        logger.info("开始摘要 %d 篇文章 (model=%s, reasoning=%s)",
                    len(target), self.model, self.is_reasoning)
        for i, a in enumerate(target, 1):
            if a.summary:
                continue
            a.summary = self.summarize_one(a)
            if i % 10 == 0:
                logger.info("已摘要 %d/%d", i, len(target))
        # 没摘要到的文章跳过(LLM 失败就不推送,避免泄露英文 raw_text)
        return target