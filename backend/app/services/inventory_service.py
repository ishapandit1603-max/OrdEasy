"""
===========================================================
Inventory Service
-----------------------------------------------------------
Looks up product availability. For the prototype this reads
from app/knowledge/sku_mapping.json (seed data); in a real
deployment this would query the `inventory` table via
database_service instead.
===========================================================
"""

import json
from pathlib import Path
from typing import Dict, Optional

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "sku_mapping.json"


class InventoryService:

    def __init__(self):
        self._catalog = self._load_catalog()

    def _load_catalog(self) -> Dict:
        if not KNOWLEDGE_PATH.exists():
            return {}
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def lookup(self, product_code: str) -> Optional[Dict]:
        if not product_code:
            return None
        return self._catalog.get(product_code.strip().upper()) or self._catalog.get(product_code)

    def check_availability(self, product_code: str, requested_qty: float) -> Dict:

        product = self.lookup(product_code)

        if not product:
            return {
                "product_code": product_code,
                "found": False,
                "in_stock": "unknown",
                "available_quantity": 0,
            }

        available_qty = product.get("quantity_available", 0)

        if requested_qty is None:
            status = "unknown"
        elif available_qty >= requested_qty:
            status = "yes"
        elif available_qty > 0:
            status = "partial"
        else:
            status = "no"

        return {
            "product_code": product_code,
            "found": True,
            "product_name": product.get("product_name"),
            "in_stock": status,
            "available_quantity": available_qty,
            "catalog_unit_price": product.get("unit_price"),
        }
