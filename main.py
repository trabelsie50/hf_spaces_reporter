import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from config import settings
from scheduler import start_scheduler, scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the FastAPI application."""
    logger.info("Starting HF Spaces Reporter...")
    logger.info("Report hours (UTC): %s", settings.REPORT_HOURS)
    logger.info("Spaces limit: %s", settings.HF_SPACES_LIMIT)

    # Start the scheduler for hourly checks and daily reports
    start_scheduler()
    logger.info("Scheduler started successfully.")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down...")
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")


app = FastAPI(
    title="HF Spaces Reporter",
    description="Bot that monitors Hugging Face Spaces and sends daily reports via Telegram",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "message": "HF Spaces Reporter is active",
        "report_hours_utc": settings.REPORT_HOURS,
        "spaces_limit": settings.HF_SPACES_LIMIT,
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


def main():
    """Entry point: starts the FastAPI server and background scheduler.

    Designed to be run directly or as the entry point on Hugging Face Spaces.
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info("Starting server on %s:%d", host, port)
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
