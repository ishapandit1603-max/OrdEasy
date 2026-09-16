"""
===========================================================
Validation Agent
-----------------------------------------------------------
Checks the structured JSON produced by the Extraction Agent
against required fields, simple business rules loaded from
app/knowledge/business_rules.json, and the real product
catalog in app/knowledge/sku_mapping.json.

Produces two parallel outputs:
  - errors / warnings: human-readable strings (unchanged
    format - anything already displaying these keeps working)
  - errors_detail: structured dicts the Recovery Agent can
    act on reliably, instead of parsing sentences.
===========================================================
"""

import json
from pathlib import Path
from typing import Dict, List

RULES_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "business_rules.json"
SKU_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "sku_mapping.json"


class ValidationAgent:

    def __init__(self):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            self.rules = json.load(f)
        with open(SKU_PATH, "r", encoding="utf-8") as f:
            self.sku_mapping = json.load(f)

    def validate(self, order_data: Dict) -> Dict:

        errors: List[str] = []
        warnings: List[str] = []
        errors_detail: List[Dict] = []

        for field in self.rules["required_fields"]:
            if not order_data.get(field):
                errors.append(f"{field} is missing.")
                errors_detail.append({
                    "field": field,
                    "item_index": None,
                    "type": "missing",
                    "value": None,
                    "message": f"{field} is missing.",
                })

        items = order_data.get("items") or []
        if len(items) == 0:
            errors.append("No products found in order.")
            errors_detail.append({
                "field": "items",
                "item_index": None,
                "type": "no_items",
                "value": None,
                "message": "No products found in order.",
            })

        for index, item in enumerate(items, start=1):

            raw_code = item.get("product_code")

            if not raw_code:
                errors.append(f"Item {index}: product_code missing.")
                errors_detail.append({
                    "field": "product_code",
                    "item_index": index,
                    "type": "missing",
                    "value": None,
                    "message": f"Item {index}: product_code missing.",
                })
            else:
                # Real lookup against the catalog - normalized (case/whitespace
                # insensitive) - not just "is this field non-empty".
                normalized = str(raw_code).strip().upper()
                if normalized not in self.sku_mapping:
                    errors.append(f"Item {index}: product_code '{raw_code}' not found in catalog.")
                    errors_detail.append({
                        "field": "product_code",
                        "item_index": index,
                        "type": "invalid_product_code",
                        "value": raw_code,
                        "message": f"Item {index}: product_code '{raw_code}' not found in catalog.",
                    })
                elif normalized != raw_code:
                    # Silently normalize case/whitespace, no need to flag this
                    item["product_code"] = normalized

            if not item.get("product_name"):
                warnings.append(f"Item {index}: product_name missing.")

            quantity = item.get("quantity")
            if quantity is None:
                errors.append(f"Item {index}: quantity missing.")
                errors_detail.append({
                    "field": "quantity",
                    "item_index": index,
                    "type": "missing",
                    "value": None,
                    "message": f"Item {index}: quantity missing.",
                })
            elif quantity <= 0:
                errors.append(f"Item {index}: invalid quantity ({quantity}).")
                errors_detail.append({
                    "field": "quantity",
                    "item_index": index,
                    "type": "invalid_value",
                    "value": quantity,
                    "message": f"Item {index}: invalid quantity ({quantity}).",
                })
            elif quantity > self.rules["max_reasonable_quantity"]:
                warnings.append(f"Item {index}: unusually large quantity ({quantity}).")

            price = item.get("unit_price")
            if price is None:
                warnings.append(f"Item {index}: unit_price missing.")
            elif price < 0:
                errors.append(f"Item {index}: invalid unit_price ({price}).")
                errors_detail.append({
                    "field": "unit_price",
                    "item_index": index,
                    "type": "invalid_value",
                    "value": price,
                    "message": f"Item {index}: invalid unit_price ({price}).",
                })

            confidence = item.get("confidence")
            if confidence is not None and confidence < self.rules["min_item_confidence"]:
                warnings.append(f"Item {index}: low AI confidence ({confidence}).")

        currency = order_data.get("currency")
        if currency and currency not in self.rules["allowed_currencies"]:
            warnings.append(f"Unrecognized currency: {currency}.")

        overall_confidence = order_data.get("confidence_score")
        if overall_confidence is not None and overall_confidence < self.rules["min_extraction_confidence"]:
            warnings.append(f"Low overall extraction confidence ({overall_confidence}).")

        status = "validated" if len(errors) == 0 else "validation_failed"

        return {
            "agent": "ValidationAgent",
            "status": status,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "errors_detail": errors_detail,
            "validated_data": order_data,
        }