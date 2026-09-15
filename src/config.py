"""配置加载模块。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# 加载 .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


@dataclass
class Config:
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # LLM
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://api.MiniMax.cn/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "MiniMax-Text-01")
    llm_max_articles: int = int(os.getenv("LLM_MAX_ARTICLES", "80"))

    # 运行参数
    lookback_hours: int = int(os.getenv("LOOKBACK_HOURS", "24"))
    max_per_source: int = int(os.getenv("MAX_PER_SOURCE", "8"))
    telegram_batch_size: int = int(os.getenv("TELEGRAM_BATCH_SIZE", "12"))

    # 数据持久化
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    seen_file: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "seen.json")

    def validate(self) -> List[str]:
        """返回缺失/错误的配置项清单,空列表表示 OK。"""
        errors: List[str] = []
        if not self.telegram_bot_token or self.telegram_bot_token == "your_telegram_bot_token_here":
            errors.append("TELEGRAM_BOT_TOKEN 未配置")
        if not self.telegram_chat_id or self.telegram_chat_id == "your_chat_id_here":
            errors.append("TELEGRAM_CHAT_ID 未配置")
        if not self.llm_api_key or self.llm_api_key == "your_llm_api_key_here":
            errors.append("LLM_API_KEY 未配置")
        return errors


CONFIG = Config()
