"""hf_scraper.py - جلب أحدث المساحات (Spaces) من Hugging Face API مع فلترة حسب التاريخ والحد الأقصى المحدد."""

import httpx
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from config import settings


@dataclass
class SpaceInfo:
    """يمثل معلومات مساحة Hugging Face Space."""
    space_name: str
    url: str
    likes: int
    date: datetime
    description: str


def fetch_recent_spaces() -> List[SpaceInfo]:
    """جلب أحدث المساحات من Hugging Face API مع فلترة حسب تاريخ الإنشاء والحد الأقصى.

    يطلب من Hugging Face API قائمة المساحات، ثم يفلترة فقط تلك التي تم إنشاؤها
    خلال آخر 24 ساعة، ويُرجعها مرتبة حسب عدد الإعجابات تنازلياً.

    Returns:
        List[SpaceInfo]: قائمة بكائنات SpaceInfo تمثل المساحات الحديثة.

    Raises:
        httpx.HTTPError: في حال فشل طلب HTTP.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    limit = getattr(settings, "HF_SPACES_LIMIT", 50)

    url = "https://huggingface.co/api/spaces"
    params: dict = {"limit": limit}
    headers: dict = {}
    if getattr(settings, "HF_TOKEN", ""):
        headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"

    response = httpx.get(url, params=params, headers=headers, timeout=30.0)
    response.raise_for_status()
    spaces_data: List[dict] = response.json()

    recent_spaces: List[SpaceInfo] = []
    for item in spaces_data:
        created_at_str: Optional[str] = item.get("created_at")
        if not created_at_str:
            continue

        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        if created_at < cutoff:
            continue

        space_id: Optional[str] = item.get("id")
        if not space_id:
            continue

        space_info = SpaceInfo(
            space_name=space_id,
            url=f"https://huggingface.co/spaces/{space_id}",
            likes=int(item.get("likes", 0)),
            date=created_at,
            description=(item.get("description") or "").strip(),
        )
        recent_spaces.append(space_info)

    recent_spaces.sort(key=lambda s: s.likes, reverse=True)
    return recent_spaces
