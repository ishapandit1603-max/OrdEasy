"""
===========================================================
Recovery Agent
-----------------------------------------------------------
Runs when the Validation Agent reports errors. Tries, in order:

  1. Cheap deterministic fixes (no AI call) - e.g. computing
     total_price from quantity * unit_price.

  2. Product code recovery - fuzzy-matches an unrecognized
     product_code against the real catalog (sku_mapping.json),
     weighted by how often THIS customer has ordered each
     candidate code before (via order history in the database).
     High-confidence matches are auto-corrected; low-confidence
     matches are only suggested, never silently applied.

  3. AI recovery - asks the LLM to re-read the original
     document text for any field still missing after steps
     1-2.

Anything that still can't be resolved is left for manual
review rather than guessed at.
===========================================================
"""

import difflib
import json
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.openai_service import ask_openai
from app.services.logger_service import LoggerService
from app.models.database_models import Order, OrderItem

logger = LoggerService.get_logger()

RECOVERY_PROMPT_TEMPLATE = """
You are a recovery assistant for an order-processing system.
The following fields could not be extracted the first time:
{missing_fields}

Re-read the original document text below and try to find these
specific fields ONLY. Return ONLY a JSON object mapping each
missing field name to the value you found, or null if it truly
is not present. No explanations, no markdown.

DOCUMENT:
{document_text}
"""

# Thresholds for the auto-fix vs suggest-only decision.
MAX_EDIT_DISTANCE = 2          # candidates further than this aren't considered at all
AUTO_FIX_MIN_HISTORY_COUNT = 3  # customer must have ordered the candidate this many times
AUTO_FIX_MAX_EDIT_DISTANCE = 2   # and be at least this close, to auto-apply


def _levenshtein(a: str, b: str) -> int:
    """Simple edit distance, no external dependency needed."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a):
        current_row = [i + 1]
        for j, char_b in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (char_a != char_b)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


class RecoveryAgent:

    def _cheap_recovery(self, order_data: Dict, errors_detail: List[Dict]) -> Dict:
        """
        Recovery steps that don't need an AI call, e.g. filling
        total_price from quantity * unit_price when both exist.
        """
        recovered_fields = []

        for item in order_data.get("items", []):
            if item.get("total_price") is None and item.get("quantity") and item.get("unit_price"):
                item["total_price"] = round(item["quantity"] * item["unit_price"], 2)
                recovered_fields.append("total_price")

        return {"order_data": order_data, "recovered_fields": recovered_fields}

    def _get_customer_code_frequency(self, db: Optional[Session], customer_name: Optional[str]) -> Dict[str, int]:
        """
        Counts how many times this customer has ordered each product_code
        in the past, based on saved orders in the database. Returns e.g.
        {"5HBB001": 14, "5HBB003": 2}. Empty dict if no db/customer given
        or no history exists yet.
        """
        if db is None or not customer_name:
            return {}

        try:
            rows = (
                db.query(OrderItem.product_code, func.count(OrderItem.id))
                .join(Order, Order.id == OrderItem.order_id)
                .filter(Order.customer_name == customer_name)
                .filter(OrderItem.product_code.isnot(None))
                .group_by(OrderItem.product_code)
                .all()
            )
            return {code: count for code, count in rows if code}
        except Exception as e:
            logger.warning(f"Recovery Agent: failed to fetch customer order history - {e}")
            return {}

    def _recover_product_code(
        self,
        bad_code: str,
        sku_mapping: Dict,
        customer_name: Optional[str],
        db: Optional[Session],
    ) -> Dict:
        """
        Given an unrecognized product_code, find the best candidate from
        the real catalog using edit-distance similarity, weighted by how
        often this customer has ordered each candidate before.
        """
        normalized = str(bad_code).strip().upper()
        known_codes = list(sku_mapping.keys())

        history_counts = self._get_customer_code_frequency(db, customer_name)

        candidates = []
        for code in known_codes:
            distance = _levenshtein(normalized, code)
            if distance > MAX_EDIT_DISTANCE:
                continue
            history_count = history_counts.get(code, 0)
            # Score rewards closeness AND how often this customer has
            # actually ordered this code before - a customer's own history
            # is a strong signal for what they meant to type.
            score = (1.0 / (distance + 1)) + (history_count * 0.5)
            candidates.append({
                "code": code,
                "product_name": sku_mapping[code].get("product_name"),
                "distance": distance,
                "history_count": history_count,
                "score": score,
            })

        candidates.sort(key=lambda c: -c["score"])

        if not candidates:
            return {
                "resolved_code": None,
                "auto_applied": False,
                "candidates": [],
                "reason": f"No similar product code found for '{bad_code}' in catalog.",
            }

        best = candidates[0]
        auto_apply = (
            best["history_count"] >= AUTO_FIX_MIN_HISTORY_COUNT
            and best["distance"] <= AUTO_FIX_MAX_EDIT_DISTANCE
        )

        return {
            "resolved_code": best["code"],
            "auto_applied": auto_apply,
            "candidates": candidates[:5],  # top 5 for display, e.g. in the UI
            "reason": (
                f"Auto-corrected '{bad_code}' -> '{best['code']}' "
                f"(ordered {best['history_count']}x before by this customer, "
                f"edit distance {best['distance']})"
                if auto_apply else
                f"'{bad_code}' not found in catalog - did you mean '{best['code']}'? "
                f"({best['history_count']}x ordered before, edit distance {best['distance']})"
            ),
        }

    def _ai_recovery(self, missing_fields: List[str], document_text: str) -> Dict:

        prompt = RECOVERY_PROMPT_TEMPLATE.format(
            missing_fields=", ".join(missing_fields),
            document_text=document_text,
        )

        try:
            raw = ask_openai(prompt)
            cleaned = raw.strip().strip("`").replace("json", "", 1).strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Recovery Agent: AI recovery failed - {e}")
            return {}

    def recover(
        self,
        order_data: Dict,
        errors_detail: List[Dict],
        document_text: str = "",
        db: Optional[Session] = None,
        sku_mapping: Optional[Dict] = None,
    ) -> Dict:
        """
        errors_detail must be the structured list produced by
        ValidationAgent.validate() (the "errors_detail" key) - NOT the
        plain-string "errors" list. Structured fields let this function
        act reliably instead of parsing sentences.
        """

        # --- Step 1: cheap deterministic fixes ---
        cheap = self._cheap_recovery(order_data, errors_detail)
        order_data = cheap["order_data"]

        handled_fields = set(cheap["recovered_fields"])
        product_code_suggestions = []

        # --- Step 2: product code recovery (fuzzy + customer history) ---
        if sku_mapping:
            customer_name = order_data.get("customer_name")
            for error in errors_detail:
                if error["type"] != "invalid_product_code":
                    continue

                item_index = error["item_index"]
                bad_code = error["value"]

                result = self._recover_product_code(bad_code, sku_mapping, customer_name, db)
                result["item_index"] = item_index
                result["original_value"] = bad_code
                product_code_suggestions.append(result)

                if result["auto_applied"]:
                    # item_index is 1-based (see ValidationAgent), items list is 0-based
                    item = order_data["items"][item_index - 1]
                    item["product_code"] = result["resolved_code"]
                    item["product_name"] = sku_mapping[result["resolved_code"]].get("product_name")
                    item["auto_corrected"] = True
                    item["auto_correction_reason"] = result["reason"]
                    logger.info(f"Recovery Agent: {result['reason']}")
                    handled_fields.add(f"product_code_item_{item_index}")
                else:
                    logger.info(f"Recovery Agent: {result['reason']}")

        # --- Step 3: AI recovery for anything still missing ---
        remaining_missing = [
            e for e in errors_detail
            if e["type"] == "missing" and f"product_code_item_{e['item_index']}" not in handled_fields
        ]

        ai_recovered_fields = {}
        if remaining_missing and document_text:
            missing_field_names = list({e["field"] for e in remaining_missing})
            ai_recovered_fields = self._ai_recovery(missing_field_names, document_text)

            for field, value in ai_recovered_fields.items():
                if value not in (None, ""):
                    order_data[field] = value

        return {
            "agent": "RecoveryAgent",
            "status": "recovery_attempted",
            "recovered_data": order_data,
            "auto_recovered_fields": cheap["recovered_fields"],
            "ai_recovered_fields": [f for f, v in ai_recovered_fields.items() if v not in (None, "")],
            "product_code_suggestions": product_code_suggestions,
            # True if anything still needs a human even after all recovery steps
            "needs_human_review": any(
                not s["auto_applied"] for s in product_code_suggestions
            ) or bool(
                [f for f in ai_recovered_fields if ai_recovered_fields.get(f) in (None, "")]
            ),
        }