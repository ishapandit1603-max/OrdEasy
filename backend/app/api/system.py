"""
===========================================================
Notifications API
-----------------------------------------------------------
Read endpoints for the notification feed, plus a manual
"check email now" trigger and a system health/status check
useful for keeping free-tier hosting awake (see README).
===========================================================
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.database_service import get_db
from app.services.scheduler_service import poll_inbox_job
from app.agents.notification_agent import NotificationAgent

router = APIRouter(prefix="/api", tags=["system"])
notification_agent = NotificationAgent()


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db)):
    notes = notification_agent.list_recent(db)
    return [
        {
            "id": n.id,
            "order_id": n.order_id,
            "level": n.level,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    note = notification_agent.mark_read(db, notification_id)
    return {"status": "success" if note else "not_found"}


@router.post("/system/check-email-now")
def check_email_now():
    """
    Manually triggers one inbox-check cycle immediately, instead of
    waiting for the next scheduled interval. Also useful as the
    endpoint an external free cron service (e.g. cron-job.org) pings
    to keep a sleeping free host awake AND process email on schedule.
    """
    poll_inbox_job()
    return {"status": "success", "message": "Inbox check triggered."}


@router.get("/healthz")
def healthz():
    return {"status": "ok"}
