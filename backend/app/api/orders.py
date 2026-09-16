"""
===========================================================
Orders API
-----------------------------------------------------------
Read endpoints used by the dashboard and chat assistant:
list orders, get one order, dashboard summary, and the
conversational Q&A endpoint.
===========================================================
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.database_service import get_db
from app.agents.dashboard_agent import DashboardAgent
from app.agents.conversation_agent import ConversationAgent
from app.models.database_models import Order

router = APIRouter(prefix="/api", tags=["orders"])

dashboard_agent = DashboardAgent()
conversation_agent = ConversationAgent()


class ChatRequest(BaseModel):
    question: str


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "purchase_order_number": o.purchase_order_number,
            "status": o.status,
            "delivery_date": o.delivery_date,
            "item_count": len(o.items),
            "intake_source": o.intake_source,
        }
        for o in orders
    ]


@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"status": "error", "message": "Order not found."}

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "purchase_order_number": order.purchase_order_number,
        "order_date": order.order_date,
        "delivery_date": order.delivery_date,
        "currency": order.currency,
        "status": order.status,
        "confidence_score": order.confidence_score,
        "validation_errors": order.validation_errors,
        "validation_warnings": order.validation_warnings,
        "items": [
            {
                "product_code": i.product_code,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_price": i.total_price,
                "confidence": i.confidence,
                "in_stock": i.in_stock,
            }
            for i in order.items
        ],
    }


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)):
    return dashboard_agent.summary(db)


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return conversation_agent.ask(db, request.question)
