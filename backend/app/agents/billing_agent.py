"""
===========================================================
Billing Agent
-----------------------------------------------------------
Computes subtotal, GST, and grand total for a validated,
inventory-checked order and returns an invoice-ready JSON
structure.
===========================================================
"""

from typing import Dict

GST_RATE = 0.18  # 18% GST, adjust as needed for your prototype


class BillingAgent:

    def generate_invoice(self, order_data: Dict) -> Dict:

        items = order_data.get("items", [])

        subtotal = 0.0
        for item in items:
            quantity = item.get("quantity") or 0
            unit_price = item.get("unit_price") or 0
            total_price = item.get("total_price")

            if total_price is None:
                total_price = round(quantity * unit_price, 2)
                item["total_price"] = total_price

            subtotal += total_price

        gst_amount = round(subtotal * GST_RATE, 2)
        grand_total = round(subtotal + gst_amount, 2)

        invoice = {
            "agent": "BillingAgent",
            "status": "invoiced",
            "customer_name": order_data.get("customer_name"),
            "purchase_order_number": order_data.get("purchase_order_number"),
            "currency": order_data.get("currency") or "INR",
            "subtotal": round(subtotal, 2),
            "gst_rate": GST_RATE,
            "gst_amount": gst_amount,
            "grand_total": grand_total,
            "items": items,
        }

        return invoice
