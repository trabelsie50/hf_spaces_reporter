"""
telegram_client.py
إرسال تقارير التحليل المفصلة عبر بوت تليجرام إلى محادثة شخصية مباشرة.
"""

import logging
from typing import List, Optional

from config import settings
from analyzer import AnalysisReport

logger = logging.getLogger(__name__)


class TelegramClient:
    """عميل بوت تليجرام لإرسال تقارير التحليل المفصلة إلى محادثة شخصية."""

    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be provided")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID must be provided")
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._bot = None

    def _get_bot(self):
        """الحصول على كائن البوت (تأخير الاستيراد)."""
        if self._bot is None:
            from telegram import Bot
            self._bot = Bot(token=self._bot_token)
        return self._bot

    async def send_report(self, report: AnalysisReport) -> bool:
        """
        إرسال تقرير تحليل واحد عبر بوت تليجرام إلى المحادثة الشخصية.

        Args:
            report: تقرير التحليل المراد إرساله.

        Returns:
            True إذا تم الإرسال بنجاح، False في حال الفشل.
        """
        message = self._build_message(report)
        try:
            bot = self._get_bot()
            await bot.send_message(
                chat_id=self._chat_id,
                text=message,
                parse_mode="Markdown",
            )
            logger.info(
                "Report sent successfully for space: %s", report.space_name
            )
            return True
        except Exception as e:
            logger.error("Failed to send report for %s: %s", report.space_name, e)
            return False

    def _build_message(self, report: AnalysisReport) -> str:
        """بناء رسالة نصية مفصّلة من تقرير التحليل بصيغة Markdown."""
        space_name = report.space_name or "غير محدد"
        space_url = report.space_url or "لا يوجد رابط"
        created_at = report.created_at or "غير معروف"
        likes = report.likes if report.likes is not None else 0
        description = report.description or "لا يوجد وصف متوفر."
        reason = report.reason or "لا يوجد سبب محدد."
        suggestions = report.suggestions or "لا توجد مقترحات متوفرة."

        innovation_score = report.innovation_score if report.innovation_score is not None else 0.0
        like_speed_score = report.like_speed_score if report.like_speed_score is not None else 0.0
        ease_score = report.ease_score if report.ease_score is not None else 0.0
        overall_score = report.overall_score if report.overall_score is not None else 0.0

        message = (
            f"🚀 *تقرير مشروع جديد على Hugging Face Spaces*\n"
            f"{'━' * 45}\n\n"
            f"📌 *اسم المشروع:* {space_name}\n"
            f"🔗 *الرابط:* [{space_name}]({space_url})\n"
            f"📅 *تاريخ الإنشاء:* {created_at}\n"
            f"👍 *عدد الإعجابات:* {likes}\n\n"
            f"📝 *الوصف:*\n{description}\n\n"
            f"{'━' * 45}\n"
            f"📊 *التقييم التفصيلي:*\n\n"
            f"💡 *الابتكار:* {innovation_score:.1f} / 10\n"
            f"⚡ *سرعة جمع الإعجابات:* {like_speed_score:.1f} / 10\n"
            f"🛠️ *سهولة التنفيذ:* {ease_score:.1f} / 10\n"
            f"{'━' * 45}\n"
            f"⭐ *الدرجة الإجمالية:* {overall_score:.1f} / 10\n\n"
            f"{'━' * 45}\n"
            f"🏆 *سبب التميز:*\n{reason}\n\n"
            f"💡 *مقترحات التطوير:*\n{suggestions}\n\n"
            f"{'━' * 45}\n"
            f"🔗 *رابط المشروع الأصلي:* {space_url}"
        )
        return message


def _get_default_client() -> TelegramClient:
    """إنشاء عميل تليجرام افتراضي من إعدادات المشروع."""
    return TelegramClient(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID,
    )


telegram_client = _get_default_client()


async def send_report(report: AnalysisReport) -> bool:
    """
    إرسال تقرير تحليل مفصّل عبر بوت تليجرام إلى المحادثة الشخصية.

    هذه هي الدالة الرئيسية للتصدير التي تستخدمها بقية المشروع
    لإرسال التقارير إلى المستخدم.

    Args:
        report: تقرير التحليل المراد إرساله، يتضمن معلومات المشروع
                والتقييم ومقترحات التطوير والروابط.

    Returns:
        True إذا تم الإرسال بنجاح، False في حال الفشل.
    """
    return await telegram_client.send_report(report)
