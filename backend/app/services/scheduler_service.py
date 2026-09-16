"""
===========================================================
Scheduler Service
-----------------------------------------------------------
Runs email_service.fetch_new_attachments() on a background
timer (every EMAIL_POLL_MINUTES) while the FastAPI app is
running, feeding each new attachment through the same
pipeline_service.process_file() used by manual uploads. This
is what makes the system "continuous" instead of only
reacting to a browser upload.

Uses APScheduler's BackgroundScheduler, which runs inside the
same process as FastAPI - no separate worker or cron needed
for local/always-on hosting. For free hosts that sleep when
idle, see the README section on keeping this alive with an
external cron ping.
===========================================================
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.services.logger_service import LoggerService
from app.services.email_service import EmailService
from app.services.database_service import SessionLocal
from app.services.pipeline_service import process_file

logger = LoggerService.get_logger()

email_service = EmailService()
_scheduler = None


def poll_inbox_job():
    logger.info("Scheduler: checking inbox for new order emails...")

    saved_paths = email_service.fetch_new_attachments()

    if not saved_paths:
        logger.info("Scheduler: no new attachments found.")
        return

    db = SessionLocal()
    try:
        for path in saved_paths:
            result = process_file(path, db, source="email")
            logger.info(f"Scheduler: processed '{path}' -> {result.get('status')}")
    finally:
        db.close()


def start_scheduler():
    global _scheduler

    if not settings.ENABLE_EMAIL_POLLING:
        logger.info("Scheduler: email polling disabled (ENABLE_EMAIL_POLLING=false).")
        return

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        poll_inbox_job,
        "interval",
        minutes=settings.EMAIL_POLL_MINUTES,
        id="poll_inbox",
        next_run_time=None,  # first run happens after one interval; call poll_inbox_job() directly for an immediate check
    )
    _scheduler.start()
    logger.info(f"Scheduler: started, polling inbox every {settings.EMAIL_POLL_MINUTES} minute(s).")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
