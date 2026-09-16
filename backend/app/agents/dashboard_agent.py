"""
===========================================================
Dashboard Agent
-----------------------------------------------------------
Reads orders from the database and aggregates them into
summary statistics the frontend dashboard can render
directly (totals, status breakdown, top products).
===========================================================
"""

from collections import Counter
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.database_models import Order, OrderItem


class DashboardAgent:

    def summary(self, db: Session) -> Dict:

        orders: List[Order] = db.query(Order).all()

        status_counts = Counter(o.status for o in orders)

        total_revenue = 0.0
        for order in orders:
            for item in order.items:
                if item.total_price:
                    total_revenue += item.total_price

        product_counter = Counter()
        for order in orders:
            for item in order.items:
                if item.product_code:
                    product_counter[item.product_code] += (item.quantity or 0)

        top_products = product_counter.most_common(5)

        return {
            "agent": "DashboardAgent",
            "total_orders": len(orders),
            "status_breakdown": dict(status_counts),
            "total_revenue": round(total_revenue, 2),
            "top_products": [
                {"product_code": code, "total_quantity": qty} for code, qty in top_products
            ],
        }
