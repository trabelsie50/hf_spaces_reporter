import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import settings
from hf_scraper import fetch_recent_spaces
from analyzer import analyze_spaces
from telegram_client import send_report

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _hourly_check():
    """Fetch recent Hugging Face Spaces every hour and log the count."""
    try:
        spaces = fetch_recent_spaces()
        logger.info(
            "Hourly check: fetched %d recent Spaces.",
            len(spaces),
        )
    except Exception as e:
        logger.error("Error during hourly spaces check: %s", e)


async def _daily_report():
    """Analyze collected Spaces and send reports via Telegram."""
    try:
        reports = analyze_spaces()
        logger.info("Generated %d analysis reports.", len(reports))
        for index, report in enumerate(reports, start=1):
            try:
                await send_report(report)
                logger.info(
                    "Report #%d sent successfully.",
                    index,
                )
            except Exception as e:
                logger.error(
                    "Error sending report #%d: %s",
                    index,
                    e,
                )
    except Exception as e:
        logger.error("Error during analysis and report generation: %s", e)


def start_scheduler():
    """Start the APScheduler with hourly checks and twice-daily report jobs."""
    scheduler.add_job(
        _hourly_check,
        trigger=IntervalTrigger(hours=1),
        id="hourly_spaces_check",
        name="Hourly Spaces Check",
        replace_existing=True,
    )

    for hour in settings.REPORT_HOURS:
        scheduler.add_job(
            _daily_report,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f"daily_report_{hour}",
            name=f"Daily Report at {hour}:00 UTC",
            replace_existing=True,
        )

    scheduler.start()
    logger.info(
        "Scheduler started. Hourly checks and daily reports at %s UTC scheduled.",
        settings.REPORT_HOURS,
    )
