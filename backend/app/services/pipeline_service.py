"""
===========================================================
Pipeline Service
-----------------------------------------------------------
The single place that runs a saved file through the full
agent pipeline:

Intake -> (PDF/Excel/OCR) -> Extraction -> Validation
 -> Recovery (if needed) -> Inventory -> Billing -> Save to DB
 -> Notifications

Used by BOTH the manual upload API endpoint and the automatic
email-ingestion scheduler, so there is exactly one place that
implements "what happens to a file" - no duplicated logic.
===========================================================
"""

from pathlib import Path
from typing import Dict

from sqlalchemy.orm import Session

from app.services.logger_service import LoggerService
from app.services.pdf_service import PDFService
from app.services.excel_service import ExcelService
from app.services.ocr_service import OCRService
from app.agents.intake_agent import IntakeAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.recovery_agent import RecoveryAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.billing_agent import BillingAgent
from app.agents.notification_agent import NotificationAgent
from app.models.database_models import Order, OrderItem

logger = LoggerService.get_logger()

intake_agent = IntakeAgent()
extraction_agent = ExtractionAgent()
validation_agent = ValidationAgent()
recovery_agent = RecoveryAgent()
inventory_agent = InventoryAgent()
billing_agent = BillingAgent()
notification_agent = NotificationAgent()

pdf_service = PDFService()
excel_service = ExcelService()
ocr_service = OCRService()

SERVICE_MAP = {
    "pdf_service": lambda path: pdf_service.extract_text(path),
    "excel_service": lambda path: excel_service.extract_text(path),
    "ocr_service": lambda path: ocr_service.extract_text(path),
}


def _persist_order(db: Session, order_data: dict, validation: dict, source_file: str,
                    doc_type: str, source: str = "manual_upload") -> Order:

    order = Order(
        customer_name=order_data.get("customer_name"),
        purchase_order_number=order_data.get("purchase_order_number"),
        order_date=order_data.get("order_date"),
        delivery_date=order_data.get("delivery_date"),
        gst_number=order_data.get("gst_number"),
        currency=order_data.get("currency") or "INR",
        status="validated" if validation["valid"] else "validation_failed",
        confidence_score=order_data.get("confidence_score"),
        raw_extraction=order_data,
        validation_errors=validation["errors"],
        validation_warnings=validation["warnings"],
        source_file_name=Path(source_file).name,
        source_document_type=doc_type,
        intake_source=source,
    )

    for item in order_data.get("items", []):
        order.items.append(OrderItem(
            product_code=item.get("product_code"),
            product_name=item.get("product_name"),
            quantity=item.get("quantity"),
            unit_price=item.get("unit_price"),
            total_price=item.get("total_price"),
            confidence=item.get("confidence"),
            in_stock=item.get("in_stock"),
        ))

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def process_file(file_path: str, db: Session, source: str = "manual_upload") -> Dict:
    """
    Runs one file through the entire agent pipeline and persists the result.
    `source` is "manual_upload" or "email" - stored on the order and used by
    the dashboard to show where each order came from.
    """

    intake_result = intake_agent.process(file_path)
    if intake_result["status"] != "success":
        return {"status": "error", "stage": "intake", "message": intake_result.get("message")}

    extraction_fn = SERVICE_MAP.get(intake_result["next_service"])
    if extraction_fn is None:
        return {"status": "error", "stage": "routing", "message": "No handler for this document type."}

    text_result = extraction_fn(file_path)
    if text_result["status"] != "success":
        return {"status": "error", "stage": intake_result["next_service"], "message": text_result.get("message")}

    document_text = text_result["text"]

    extraction_result = extraction_agent.extract(document_text)
    if extraction_result["status"] != "success":
        return {"status": "error", "stage": "extraction", "message": extraction_result.get("message")}

    order_data = extraction_result["data"]

    validation_result = validation_agent.validate(order_data)

    # ---- CHANGED BLOCK START ----
    recovery_result = None

    if not validation_result["valid"]:
        recovery_result = recovery_agent.recover(
            order_data,
            validation_result["errors_detail"],   # structured list, not "errors"
            document_text,
            db=db,                                  # session already in scope here
            sku_mapping=validation_agent.sku_mapping,
        )
        order_data = recovery_result["recovered_data"]
        # Re-validate the recovered data before it gets persisted
        validation_result = validation_agent.validate(order_data)
    # ---- CHANGED BLOCK END ----

    inventory_result = inventory_agent.check(order_data)
    order_data = inventory_result["order_data"]

    invoice = billing_agent.generate_invoice(order_data)

    order_record = _persist_order(
        db, order_data, validation_result, file_path, intake_result["document_type"], source
    )

    notification_agent.notify_for_order(db, order_record, validation_result, inventory_result)

    logger.info(f"Order #{order_record.id} processed via {source} with status {order_record.status}")

    return {
        "status": "success",
        "order_id": order_record.id,
        "order_status": order_record.status,
        "validation": {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
        },
        "inventory": {
            "has_shortages": inventory_result["has_shortages"],
            "shortages": inventory_result["shortages"],
        },
        "invoice": invoice,
        # ---- CHANGED: surfaces what recovery actually did ----
        "recovery": {
            "auto_recovered_fields": recovery_result["auto_recovered_fields"],
            "ai_recovered_fields": recovery_result["ai_recovered_fields"],
            "product_code_suggestions": recovery_result["product_code_suggestions"],
            "needs_human_review": recovery_result["needs_human_review"],
        } if recovery_result else None,
        "order_data": order_data,
    }