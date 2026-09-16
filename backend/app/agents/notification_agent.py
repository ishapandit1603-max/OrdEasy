"""
===========================================================
Notification Agent
-----------------------------------------------------------
Creates lightweight, DB-backed notifications whenever an
order needs human attention: validation failures the
Recovery Agent couldn't fully fix, stock shortages, or low
AI confidence. The dashboard polls GET /api/notifications to
show these - no external email/SMS service required, so it
works with zero extra setup or cost.
===========================================================
"""

from typing import Dict

from sqlalchemy.orm import Session

from app.models.database_models import Notification, Order


class NotificationAgent:

    def _create(self, db: Session, order_id: int, level: str, title: str, message: str):
        note = Notification(order_id=order_id, level=level, title=title, message=message)
        db.add(note)
        db.commit()

    def notify_for_order(self, db: Session, order: Order, validation_result: Dict, inventory_result: Dict):

        if not validation_result["valid"]:
            self._create(
                db, order.id, "error",
                f"Order #{order.id} needs review",
                f"{len(validation_result['errors'])} issue(s) remained after automatic recovery: "
                + "; ".join(validation_result["errors"][:3]),
            )

        if inventory_result.get("has_shortages"):
            codes = ", ".join(s["product_code"] for s in inventory_result["shortages"] if s.get("product_code"))
            self._create(
                db, order.id, "warning",
                f"Stock shortage on order #{order.id}",
                f"Insufficient stock for: {codes}",
            )

        if validation_result["valid"] and not inventory_result.get("has_shortages"):
            self._create(
                db, order.id, "info",
                f"Order #{order.id} processed cleanly",
                f"Customer: {order.customer_name or 'unknown'} · PO: {order.purchase_order_number or 'unknown'}",
            )

    def list_recent(self, db: Session, limit: int = 30):
        return (
            db.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_read(self, db: Session, notification_id: int):
        note = db.query(Notification).filter(Notification.id == notification_id).first()
        if note:
            note.is_read = "yes"
            db.commit()
        return note
