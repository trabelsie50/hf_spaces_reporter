import os
from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    """جميع إعدادات المشروع المقروءة من متغيرات البيئة."""

    hf_token: str
    telegram_bot_token: str
    gemini_api_key: str
    telegram_chat_id: str
    hf_spaces_limit: int
    report_hours: List[int]


def _parse_report_hours(value: str) -> List[int]:
    """تحويل سلسلة الساعات المفصولة بفواصل إلى قائمة أعداد صحيحة."""
    return [int(h.strip()) for h in value.split(",") if h.strip()]


settings = Settings(
    hf_token=os.environ["HF_TOKEN"],
    telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    gemini_api_key=os.environ["GEMINI_API_KEY"],
    telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
    hf_spaces_limit=int(os.environ.get("HF_SPACES_LIMIT", "50")),
    report_hours=_parse_report_hours(os.environ.get("REPORT_HOURS", "9,18")),
)
