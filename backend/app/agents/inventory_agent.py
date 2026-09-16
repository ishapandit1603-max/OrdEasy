"""
===========================================================
Inventory Agent
-----------------------------------------------------------
For every line item in a validated order, checks stock
availability via InventoryService and annotates each item
with an in_stock status: "yes" / "partial" / "no" / "unknown".
===========================================================
"""

from typing import Dict

from app.services.inventory_service import InventoryService
from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()


class InventoryAgent:

    def __init__(self):
        self.inventory_service = InventoryService()

    def check(self, order_data: Dict) -> Dict:

        items = order_data.get("items", [])
        annotated_items = []
        shortages = []

        for item in items:
            availability = self.inventory_service.check_availability(
                item.get("product_code"), item.get("quantity")
            )

            item["in_stock"] = availability["in_stock"]

            if availability["found"] and not item.get("product_name"):
                item["product_name"] = availability.get("product_name")

            if availability["in_stock"] in ("no", "partial"):
                shortages.append({
                    "product_code": item.get("product_code"),
                    "requested": item.get("quantity"),
                    "available": availability["available_quantity"],
                })

            annotated_items.append(item)

        order_data["items"] = annotated_items

        return {
            "agent": "InventoryAgent",
            "status": "checked",
            "order_data": order_data,
            "has_shortages": len(shortages) > 0,
            "shortages": shortages,
        }
