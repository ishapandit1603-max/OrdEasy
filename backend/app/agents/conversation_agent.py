"""
===========================================================
Conversation Agent
-----------------------------------------------------------
Powers the chat assistant. Pulls relevant order data from
the database, then asks OpenAI to answer the user's question
in plain language using that data as grounding context (so
answers are based on real records, not invented ones).
===========================================================
"""

import json
from typing import Dict

from sqlalchemy.orm import Session

from app.models.database_models import Order
from app.services.openai_service import ask_openai

CHAT_PROMPT_TEMPLATE = """
You are the assistant for SmartOrder AI, an order-processing system.
Answer the user's question using ONLY the order data provided below.
If the data doesn't contain the answer, say so honestly.
Be concise and specific (mention order numbers, customer names, statuses).

ORDER DATA (JSON):
{order_data}

USER QUESTION:
{question}
"""


class ConversationAgent:

    def _serialize_orders(self, db: Session, limit: int = 50) -> list:

        orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()

        return [
            {
                "id": o.id,
                "customer_name": o.customer_name,
                "purchase_order_number": o.purchase_order_number,
                "status": o.status,
                "delivery_date": o.delivery_date,
                "items": [
                    {
                        "product_code": i.product_code,
                        "quantity": i.quantity,
                        "in_stock": i.in_stock,
                    }
                    for i in o.items
                ],
            }
            for o in orders
        ]

    def ask(self, db: Session, question: str) -> Dict:

        order_data = self._serialize_orders(db)

        prompt = CHAT_PROMPT_TEMPLATE.format(
            order_data=json.dumps(order_data, indent=2),
            question=question,
        )

        try:
            answer = ask_openai(prompt)
            return {"agent": "ConversationAgent", "status": "success", "answer": answer.strip()}
        except Exception as e:
            return {"agent": "ConversationAgent", "status": "failed", "message": str(e)}
